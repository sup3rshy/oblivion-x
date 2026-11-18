# Contributing to Oblivion-X

## Development setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

The package supports Python 3.10+ and has no Windows dependency for the
offline workflow. Word/Excel COM is only needed for the authoritative corpus
builder and real-execution traces.

## Checks

```bash
make lint          # ruff
make test          # pytest
make check         # both
make test-cov      # coverage report
```

CI runs the same lint and test commands on Python 3.10, 3.11 and 3.12.

## Offline corpus

The pure-Python MS-OVBA writer produces valid `.docm`/`.xlsm` files that
oletools can read. This is enough for static analysis and for the simulator:

```bash
.venv/bin/python -m oblivionx corpus generate --out outputs/corpus
.venv/bin/python -m oblivionx corpus build --corpus outputs/corpus
.venv/bin/python -m oblivionx pipeline run --corpus outputs/corpus --out outputs/analysis
```

`corpus build` skips existing files unless `--overwrite` is passed, so it will
not clobber files authored with Word/Excel COM.

## Code layout

- `oblivionx/common.py` — behavior catalog, stages, families, ground truth
- `oblivionx/corpus/` — source generation, obfuscators, MS-OVBA/CFB writer
- `oblivionx/static/` — extraction, obfuscation detection, deobfuscation
- `oblivionx/telemetry/` — normalized event schema and segmentation
- `oblivionx/simulate/` — deterministic dynamic-telemetry simulator
- `oblivionx/reconstruction/` — evidence-to-stage-chain reconstruction
- `oblivionx/eval/` — metrics, experiments E1–E8, report generation

Every change to analysis logic should come with a unit test that does not
depend on the Windows-built corpus. End-to-end tests build a small corpus in
`tmp_path` with `oblivionx.corpus.builders`.
