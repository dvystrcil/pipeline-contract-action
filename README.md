# pipeline-contract-action

GitHub composite action — PR-time contract validation for OWUI Pipeline files.

Sister action to [`dvystrcil/pipeline-lint-action`](https://github.com/dvystrcil/pipeline-lint-action) (async-correctness lint). The two complete Tier 2 of the homelab testing ladder defined in [`architecture/ways-of-working.md` D-001](https://github.com/dvystrcil/homelab/blob/main/architecture/ways-of-working.md#d-001--tiered-testing-slow--skipped).

Closes ACs 2-5 of [`dvystrcil/homelab#25`](https://github.com/dvystrcil/homelab/issues/25). Catches the shape bugs that have shipped to prod twice without the unit-test layer noticing:

- **2026-05-08** — Pipeline dropped `pipelines: list[str]` from `Valves`; OWUI's admin UI hid every Pipeline because `/v1/models` returned 500
- **2026-05-09** — Pipeline `inlet` was sync; uvicorn event loop froze on every chat turn

## What it checks

Pure-AST (no module import, no OWUI runtime needed). One Pipeline class per file is assumed.

| Check | Rule |
|---|---|
| AC2 | `inlet` / `outlet` methods are `async def` when present |
| AC3 | `on_startup` / `on_shutdown` / `on_valves_updated` are `async def` when present |
| AC4 | Nested `class Valves` has a `pipelines` field annotation |
| AC5 | `__init__` assigns `self.type`, `self.name`, `self.valves` |

Files that do NOT define a `class Pipeline:` are silently skipped — helper modules, test files, conftest, etc.

## Usage

```yaml
- uses: actions/checkout@v6
- uses: dvystrcil/pipeline-contract-action@v0.1.0
  with:
    paths: pipelines
```

Multiple roots are space-separated. Globs are supported but expanded by the shell:

```yaml
- uses: dvystrcil/pipeline-contract-action@v0.1.0
  with:
    paths: |
      pipelines
      prompts/owui/filters
```

### Inputs

| Name | Required | Default | Description |
|---|---|---|---|
| `paths` | yes | — | Space-separated paths and/or globs to discover Pipeline files |
| `exclude` | no | `*/.venv` + `*__pycache__*` + `*/eval/*` + `*/tests/*` | Newline-separated `find -path` patterns to prune |

### Output

`<file>:<line>:<col>: <message>` to stderr, with parallel `::error file=...,line=...,col=...::<msg>` lines when `GITHUB_ACTIONS=true` so the error annotations land in the PR UI. Exit code 0 on clean, 1 on any violation.

## Pair with the lint action

```yaml
jobs:
  pipeline-checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: dvystrcil/pipeline-lint-action@v0.1.0    # async-call correctness
        with:
          paths: pipelines
      - uses: dvystrcil/pipeline-contract-action@v0.1.0  # this — shape contract
        with:
          paths: pipelines
```

Two consumers in flight at `v0.1.0`: [`dvystrcil/open-webui`](https://github.com/dvystrcil/open-webui) and [`dvystrcil/homelab`](https://github.com/dvystrcil/homelab). Each touches Pipeline files; this action is what catches regressions before the next prod bug.

## Local development

```bash
python3 tests/test_contract.py
# → 7 tests, exit 0 if clean
```

Fixtures under `tests/fixtures/` cover the good case + one bad case per AC.

## License

[MIT](./LICENSE) — Copyright (c) 2026 Daniel Vystrcil
