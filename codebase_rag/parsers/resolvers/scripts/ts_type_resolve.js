#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

let ts = null;
try {
    ts = require('typescript');
} catch (e) {
    // (H) TypeScript not available — report unavailable on init
}

let languageService = null;
let program = null;
let programFiles = [];

function findNearestTsconfig(startDir) {
    let currentDir = startDir;
    const root = path.parse(currentDir).root;

    while (currentDir !== root) {
        const configPath = path.join(currentDir, 'tsconfig.json');
        if (fs.existsSync(configPath)) {
            return configPath;
        }
        currentDir = path.dirname(currentDir);
    }

    return null;
}

function createLanguageServiceHost(configPath) {
    const configFile = ts.readConfigFile(configPath, ts.sys.readFile);
    if (configFile.error) {
        return null;
    }

    const configDir = path.dirname(configPath);
    const parsedConfig = ts.parseJsonConfigFileContent(
        configFile.config,
        ts.sys,
        configDir
    );

    const fileNames = parsedConfig.fileNames;
    const options = parsedConfig.options;
    const fileVersions = new Map();

    fileNames.forEach(f => fileVersions.set(f, 0));

    const host = {
        getScriptFileNames: () => fileNames,
        getScriptVersion: (fileName) => {
            const v = fileVersions.get(fileName);
            return v !== undefined ? String(v) : '0';
        },
        getScriptSnapshot: (fileName) => {
            if (!fs.existsSync(fileName)) {
                return undefined;
            }
            return ts.ScriptSnapshot.fromString(fs.readFileSync(fileName, 'utf8'));
        },
        getCurrentDirectory: () => configDir,
        getCompilationSettings: () => options,
        getDefaultLibFileName: (opts) => ts.getDefaultLibFilePath(opts),
        fileExists: ts.sys.fileExists,
        readFile: ts.sys.readFile,
        readDirectory: ts.sys.readDirectory,
        directoryExists: ts.sys.directoryExists,
        getDirectories: ts.sys.getDirectories,
    };

    return { host, fileNames, options };
}

function extractFunctionTypes(sourceFile, checker) {
    const functions = {};

    function visitNode(node) {
        if (ts.isFunctionDeclaration(node) && node.name) {
            const funcName = node.name.text;
            const params = extractParameterTypes(node, checker);
            if (Object.keys(params).length > 0) {
                functions[funcName] = { parameters: params };
            }
        }

        if (ts.isMethodDeclaration(node) && node.name) {
            const methodName = node.name.getText(sourceFile);
            const params = extractParameterTypes(node, checker);
            if (Object.keys(params).length > 0) {
                functions[methodName] = { parameters: params };
            }
        }

        if (ts.isVariableDeclaration(node) && node.name && ts.isIdentifier(node.name)) {
            const varName = node.name.text;
            const initializer = node.initializer;

            if (initializer && (ts.isArrowFunction(initializer) || ts.isFunctionExpression(initializer))) {
                const params = extractParameterTypes(initializer, checker);
                if (Object.keys(params).length > 0) {
                    functions[varName] = { parameters: params };
                }
            }
        }

        ts.forEachChild(node, visitNode);
    }

    visitNode(sourceFile);
    return functions;
}

function extractParameterTypes(funcNode, checker) {
    const params = {};

    if (!funcNode.parameters) {
        return params;
    }

    for (const paramDecl of funcNode.parameters) {
        if (!paramDecl.type) {
            continue;
        }

        if (!paramDecl.name || !ts.isIdentifier(paramDecl.name)) {
            continue;
        }

        const paramName = paramDecl.name.text;

        try {
            const paramType = checker.getTypeAtLocation(paramDecl);
            const typeStr = checker.typeToString(
                paramType,
                paramDecl,
                ts.TypeFormatFlags.NoTruncation
            );
            params[paramName] = typeStr;
        } catch (e) {
            // (H) Skip params where type extraction fails
        }
    }

    return params;
}

function handleInit(input) {
    if (!ts) {
        return JSON.stringify({ init: true, status: 'unavailable', reason: 'typescript_not_found' });
    }

    const tsconfigPath = input.tsconfigPath || null;
    let resolvedTsconfig = tsconfigPath;

    if (!resolvedTsconfig) {
        return JSON.stringify({ init: true, status: 'no_tsconfig', reason: 'no_tsconfig_path' });
    }

    if (!fs.existsSync(resolvedTsconfig)) {
        resolvedTsconfig = findNearestTsconfig(path.dirname(resolvedTsconfig));
    }

    if (!resolvedTsconfig) {
        return JSON.stringify({ init: true, status: 'no_tsconfig', reason: 'tsconfig_not_found' });
    }

    try {
        const result = createLanguageServiceHost(resolvedTsconfig);
        if (!result) {
            return JSON.stringify({ init: true, status: 'error', reason: 'failed_to_parse_tsconfig' });
        }

        languageService = ts.createLanguageService(result.host, ts.createDocumentRegistry());
        programFiles = result.fileNames;

        return JSON.stringify({
            init: true,
            status: 'ok',
            fileCount: programFiles.length,
            tsconfig: resolvedTsconfig,
        });
    } catch (e) {
        return JSON.stringify({ init: true, status: 'error', reason: e.message });
    }
}

function handleQuery(input) {
    const filePath = input.file;

    if (!languageService) {
        return JSON.stringify({ file: filePath, functions: {}, error: 'not_initialized' });
    }

    const normalizedPath = path.resolve(filePath);
    const isInProgram = programFiles.some(f => path.resolve(f) === normalizedPath);

    if (!isInProgram) {
        return JSON.stringify({ file: filePath, functions: {}, error: 'not_in_program' });
    }

    try {
        program = languageService.getProgram();
        if (!program) {
            return JSON.stringify({ file: filePath, functions: {}, error: 'no_program' });
        }

        const sourceFile = program.getSourceFile(normalizedPath);
        if (!sourceFile) {
            return JSON.stringify({ file: filePath, functions: {}, error: 'source_file_not_found' });
        }

        const checker = program.getTypeChecker();
        const functions = extractFunctionTypes(sourceFile, checker);

        return JSON.stringify({ file: filePath, functions: functions, error: null });
    } catch (e) {
        return JSON.stringify({ file: filePath, functions: {}, error: e.message });
    }
}

async function main() {
    const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
        terminal: false,
    });

    rl.on('line', (line) => {
        try {
            const input = JSON.parse(line);

            if (input.init === true) {
                console.log(handleInit(input));
                return;
            }

            if (input.file) {
                console.log(handleQuery(input));
                return;
            }

            console.log(JSON.stringify({ error: 'unknown_command' }));
        } catch (e) {
            console.log(JSON.stringify({ error: 'parse_error', message: e.message }));
        }
    });

    rl.on('close', () => {
        process.exit(0);
    });
}

if (require.main === module) {
    main().catch((error) => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = { extractFunctionTypes, extractParameterTypes };
