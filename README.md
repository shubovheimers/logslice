# logslice

A CLI tool for slicing and filtering large log files by time range, pattern, or log level with minimal memory overhead.

---

## Installation

```bash
pip install logslice
```

Or install from source:

```bash
git clone https://github.com/yourname/logslice.git && cd logslice && pip install .
```

---

## Usage

```bash
# Filter by time range
logslice app.log --from "2024-01-15 08:00:00" --to "2024-01-15 09:00:00"

# Filter by log level
logslice app.log --level ERROR

# Filter by pattern
logslice app.log --pattern "timeout|connection refused"

# Combine filters and write output to a file
logslice app.log --level WARNING --from "2024-01-15 08:00:00" --out filtered.log
```

### Options

| Flag | Description |
|------|-------------|
| `--from` | Start of time range (inclusive) |
| `--to` | End of time range (inclusive) |
| `--level` | Minimum log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `--pattern` | Regex pattern to match against log lines |
| `--out` | Write results to a file instead of stdout |

---

## Why logslice?

Log files can grow to gigabytes in production environments. `logslice` streams files line by line, keeping memory usage flat regardless of file size — no need to load the entire file into memory or reach for heavyweight tools.

---

## License

MIT © 2024 [yourname](https://github.com/yourname)