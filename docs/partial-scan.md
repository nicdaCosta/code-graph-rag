# Partial Scans with `--files`

The `start` command supports a `--files` flag that restricts a graph update to a specific set of files instead of scanning the entire repository. This is useful when you have a large codebase and only a small number of files have changed.

## Usage

`--files` **must be combined with `--update-graph`**. Without `--update-graph`, the flag is silently ignored and a normal chat session starts.

```bash
# Scan a single file
cgr start --repo-path /path/to/repo --update-graph --files src/services/payment.py

# Scan multiple files (repeat the flag for each)
cgr start --repo-path /path/to/repo --update-graph \
  --files src/services/payment.py \
  --files src/models/invoice.py
```

Paths provided to `--files` are **relative to the repo root** (i.e., relative to the value passed to `--repo-path`).

## How It Works

A normal full scan runs three passes:

1. **Pass 1 – Structure**: Discovers the repo layout (packages, folders, modules)
2. **Pass 2 – Definitions**: Parses each file and extracts functions, classes, imports, etc.
3. **Pass 3 – Call resolution**: Resolves all function call edges across the codebase

When `--files` is provided, the scan is modified as follows:

- **Pass 1 is skipped entirely.** Instead, the function registry is pre-loaded directly from the existing graph in Memgraph (all currently indexed function/method qualified names are fetched into memory).
- **Pass 2 runs only for the specified files.** All other files are ignored.
- **Pass 3 runs only for files that were processed in Pass 2.** Call edges are re-created for the scanned files, but the rest of the codebase's call graph is untouched.

## Limitations and Gotchas

### Orphan nodes from renamed or deleted symbols

All graph writes use Cypher `MERGE`, which creates a node if it does not exist or updates it if it does. There is **no pre-deletion step** for the files being re-scanned.

This means:

- If a function `process_payment` is renamed to `handle_payment` in `payment.py` and you run a partial scan on that file, the graph will contain **both** a `process_payment` node (now orphaned — its source code no longer exists) and a new `handle_payment` node.
- The old `process_payment` node retains all its previous relationships (CALLS edges, class memberships, etc.), making the graph incorrect.
- The only way to clean up orphan nodes is to run a full rescan with `--clean`:

  ```bash
  cgr start --repo-path /path/to/repo --update-graph --clean
  ```

### Stale CALLS relationships

Old `CALLS` edges from re-scanned files are not removed before new ones are added. If a call was removed from `payment.py`, the old `CALLS` relationship will persist alongside any new ones created by the partial scan.

By contrast, the real-time file watcher (`make watch`) handles this correctly: it deletes the module and all its descendants from the graph before re-indexing, then rebuilds the entire call graph.

### Orphaned nodes re-enter the function registry

When `--files` is active, the function registry is pre-loaded from the existing graph. This means orphaned function nodes (e.g., an old name left over from a previous partial scan) will be present in the registry during call resolution. If another file calls the old name, it may be incorrectly resolved to the stale node rather than flagged as unresolved.

### No structural updates

Pass 1 is skipped, so no new structural nodes are created. If any of the specified files reside in a **new directory or module** that was not present in the last full scan, the parent package/folder/module hierarchy will not be added to the graph and the file's nodes may be disconnected from the project tree.

### The flag is silently ignored without `--update-graph`

If `--files` is passed without `--update-graph`, the argument is accepted without error but has no effect — the tool simply starts an interactive chat session.

## When It Is Safe to Use

Partial scans are safe when the changes to the scanned files are **additive only**:

- Adding new functions or methods to an existing file
- Adding new files to directories that are already indexed
- Updating function bodies without changing signatures or names

Partial scans are **not safe** when:

- Functions, methods, or classes have been renamed or deleted
- Files have been moved or renamed
- New directories or packages need to be registered in the graph

In these cases, run a full rescan to keep the graph accurate.
