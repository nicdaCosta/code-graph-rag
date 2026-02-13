#!/usr/bin/env node
/**
 * TypeScript Module Resolution Helper
 *
 * Uses TypeScript's native ts.resolveModuleName() API to resolve import specifiers
 * to filesystem paths. This handles tsconfig paths, baseUrl, and all TypeScript
 * resolution features.
 *
 * Input format (JSON lines):
 * {"specifier": "@web-platform/shared-acorn-redux/src/utils", "fromFile": "/repo/apps/main.ts"}
 *
 * Output format (JSON lines):
 * {"specifier": "@web-platform/shared-acorn-redux/src/utils", "resolvedPath": "/repo/libs/shared-acorn-redux/src/utils.ts", "isExternal": false}
 *
 * Exit codes:
 * 0 - Success
 * 1 - Error (details in stderr)
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Try to load TypeScript - it's optional
let ts = null;
try {
    ts = require('typescript');
} catch (e) {
    // TypeScript not available - will fall back to require.resolve
}

// Module-level state for workspace-injected paths
// Initialized via init message from Python process
let injectedPaths = null;   // { "@scope/pkg/*": ["relative/path/*"], ... }
let injectedBaseUrl = null;  // "/absolute/path/to/repo"

/**
 * Load tsconfig.json for a given file
 * @param {string} fromFile - Path to the file being processed
 * @returns {{config: any, configPath: string} | null}
 */
function loadTsConfig(fromFile) {
    if (!ts) return null;

    let currentDir = path.dirname(fromFile);
    const root = path.parse(currentDir).root;

    // Walk up directory tree looking for tsconfig.json
    while (currentDir !== root) {
        const configPath = path.join(currentDir, 'tsconfig.json');
        if (fs.existsSync(configPath)) {
            try {
                const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
                if (configFile.error) {
                    return null;
                }

                const parsedConfig = ts.parseJsonConfigFileContent(
                    configFile.config,
                    ts.sys,
                    currentDir
                );

                return { config: parsedConfig, configPath };
            } catch (error) {
                return null;
            }
        }
        currentDir = path.dirname(currentDir);
    }

    return null;
}

// Cache for tsconfig per directory
const tsconfigCache = new Map();

/**
 * Resolve using TypeScript's native resolution
 * @param {string} specifier - The import specifier
 * @param {string} fromFile - Absolute path to the file containing the import
 * @returns {{resolvedPath: string|null, isExternal: boolean|null, error: string|null}}
 */
function resolveWithTypeScript(specifier, fromFile) {
    const fromDir = path.dirname(fromFile);

    // Get or load tsconfig
    let tsConfigInfo = tsconfigCache.get(fromDir);
    if (tsConfigInfo === undefined) {
        tsConfigInfo = loadTsConfig(fromFile);
        tsconfigCache.set(fromDir, tsConfigInfo);
    }

    if (!tsConfigInfo) {
        // No tsconfig found - can't use TypeScript resolution
        return { resolvedPath: null, isExternal: null, error: 'No tsconfig.json found' };
    }

    const { config } = tsConfigInfo;

    try {
        // Create shallow copy of compiler options to avoid mutating cached config
        const options = { ...config.options };

        // Merge workspace-injected paths into compiler options
        if (injectedPaths && Object.keys(injectedPaths).length > 0) {
            // Per PLAN_WORKSPACE_PATHS_INJECTION.md: existing paths first, then injected
            // This means injected paths OVERRIDE existing paths (spread right overwrites left)
            options.paths = { ...options.paths, ...injectedPaths };
        }

        // Set baseUrl if not already defined
        if (injectedBaseUrl && !options.baseUrl) {
            options.baseUrl = injectedBaseUrl;
        }

        const host = ts.createCompilerHost(options);
        const result = ts.resolveModuleName(
            specifier,
            fromFile,
            options,
            host
        );

        if (result.resolvedModule) {
            const resolved = result.resolvedModule.resolvedFileName;

            // Check if it's external (in node_modules)
            const isExternal = resolved.includes('/node_modules/') ||
                             resolved.includes('\\node_modules\\');

            return {
                resolvedPath: isExternal ? null : resolved,
                isExternal: isExternal,
                error: null
            };
        }

        // Module not resolved by TypeScript
        return {
            resolvedPath: null,
            isExternal: null,
            error: 'TypeScript could not resolve module'
        };
    } catch (error) {
        return {
            resolvedPath: null,
            isExternal: null,
            error: error.message
        };
    }
}

/**
 * Fallback resolution using require.resolve
 * @param {string} specifier - The import specifier
 * @param {string} fromFile - Absolute path to the file containing the import
 * @returns {{resolvedPath: string|null, isExternal: boolean|null, error: string|null}}
 */
function resolveWithRequire(specifier, fromFile) {
    const fromDir = path.dirname(fromFile);

    try {
        const resolved = require.resolve(specifier, { paths: [fromDir] });

        // Check if resolved path is inside node_modules
        const isExternal = resolved.includes('/node_modules/') ||
                         resolved.includes('\\node_modules\\');

        return {
            resolvedPath: isExternal ? null : resolved,
            isExternal: isExternal,
            error: null
        };
    } catch (requireError) {
        // Resolution failed - this doesn't mean it's external,
        // just that require.resolve couldn't find it
        // (e.g., workspace packages, tsconfig paths)
        return {
            resolvedPath: null,
            isExternal: null,  // null = unknown, not false/true
            error: null
        };
    }
}

/**
 * Resolve relative imports using filesystem
 * @param {string} specifier - The import specifier
 * @param {string} fromFile - Absolute path to the file containing the import
 * @returns {{resolvedPath: string|null, isExternal: boolean, error: string|null}}
 */
function resolveRelative(specifier, fromFile) {
    const fromDir = path.dirname(fromFile);
    let resolved = path.resolve(fromDir, specifier);

    // Try with various extensions
    const extensions = ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.mts', '.cts'];

    // Try exact path first
    if (fs.existsSync(resolved)) {
        const stats = fs.statSync(resolved);
        if (stats.isFile()) {
            return { resolvedPath: resolved, isExternal: false, error: null };
        }
        // If directory, try index files
        for (const ext of extensions) {
            const indexPath = path.join(resolved, `index${ext}`);
            if (fs.existsSync(indexPath)) {
                return { resolvedPath: indexPath, isExternal: false, error: null };
            }
        }
    }

    // Try with extensions
    for (const ext of extensions) {
        const withExt = resolved + ext;
        if (fs.existsSync(withExt)) {
            return { resolvedPath: withExt, isExternal: false, error: null };
        }
    }

    return {
        resolvedPath: null,
        isExternal: false,
        error: `Could not resolve relative path: ${specifier}`
    };
}

/**
 * Main resolution function
 * @param {string} specifier - The import specifier
 * @param {string} fromFile - Absolute path to the file containing the import
 * @returns {{resolvedPath: string|null, isExternal: boolean|null, error: string|null}}
 */
function resolveModule(specifier, fromFile) {
    // Handle relative imports with filesystem resolution
    if (specifier.startsWith('./') || specifier.startsWith('../')) {
        return resolveRelative(specifier, fromFile);
    }

    // Try TypeScript resolution first if available
    if (ts) {
        const tsResult = resolveWithTypeScript(specifier, fromFile);
        if (tsResult.resolvedPath !== null || tsResult.isExternal === true) {
            // Successfully resolved or determined to be external
            return tsResult;
        }
        // If TypeScript couldn't resolve it, fall through to require.resolve
    }

    // Fallback to require.resolve
    return resolveWithRequire(specifier, fromFile);
}

/**
 * Main entry point - reads JSON lines from stdin and outputs resolved paths
 */
async function main() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false
    });

    let lineCount = 0;
    let errorCount = 0;

    rl.on('line', (line) => {
        lineCount++;

        try {
            const input = JSON.parse(line);

            // Handle initialization message
            if (input.init === true) {
                injectedPaths = input.paths || {};
                injectedBaseUrl = input.baseUrl || null;

                // Clear tsconfig cache to force re-merge with new paths
                tsconfigCache.clear();

                // Respond with acknowledgement
                console.log(JSON.stringify({
                    init: true,
                    status: 'ok',
                    pathCount: Object.keys(injectedPaths).length
                }));
                return;
            }

            // Existing resolve logic (keep all existing code below)
            const { specifier, fromFile } = input;

            if (!specifier || !fromFile) {
                console.error(`Line ${lineCount}: Missing required fields 'specifier' or 'fromFile'`);
                errorCount++;
                return;
            }

            const result = resolveModule(specifier, fromFile);

            // Output result as JSON line
            console.log(JSON.stringify({
                specifier,
                fromFile,
                resolvedPath: result.resolvedPath,
                isExternal: result.isExternal,
                error: result.error
            }));

        } catch (error) {
            console.error(`Line ${lineCount}: Failed to parse JSON: ${error.message}`);
            errorCount++;
        }
    });

    rl.on('close', () => {
        if (errorCount > 0) {
            process.exit(1);
        }
        process.exit(0);
    });
}

// Run if executed directly
if (require.main === module) {
    main().catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = { resolveModule, resolveWithTypeScript, resolveWithRequire, resolveRelative };
