# CroBank Manual Parser 

Small, pure‑Python helper for inspecting and exporting Cronos/CroBank datasets when you want to hand‑craft schemas instead of relying on `cronodump`. You describe fixed‑width fields, preview raw records, then export to CSV.

## Contents
- [Prerequisites](#prerequisites)
- [Core Ideas](#core-ideas)
- [Workflow Overview](#workflow-overview)
- [Command Reference](#command-reference)
- [Building the Schema](#building-the-schema)
- [Advanced Tweaks](#advanced-tweaks)
- [Troubleshooting](#troubleshooting)

## Prerequisites
- Python 3.9+ (standard library only).
- Access to a CroBank dataset directory containing `CroBank.dat`, `CroBank.tad`, `CroStru.dat`, etc.
- Basic familiarity with fixed‑width records and CP1251 text (default encoding).

## Core Ideas
- **Manual schema**: Define every field with name, byte offset, and byte length in `SCHEMA`.
- **Fixed-size records**: Assumes constant record width; variable/complex records require custom parsing.
- **Two modes**:
  - `inspect`: dump helper views so you can reverse‑engineer offsets.
  - `export`: apply your schema to `CroBank.dat` and write a CSV.

## Workflow Overview
1. Inspect raw bytes to guess the layout.
2. Populate `SCHEMA` (and optionally `RECORD_SIZE`) in `tad_parser.py`.
3. Iterate until the decoded fields look correct.
4. Export to CSV.

## Command Reference

### Inspect
```bash
python tad_parser.py inspect "D:\Cronos\610.РФ Авиаперелеты 05.2021 (travellers)" ^
    --max-records 5 ^
    --guess-record-size 256
```
Outputs (saved beside the dataset):
- `CroStru_dump.txt`: first 1024 bytes of `CroStru.dat` (hex + cp1251 text).
- `CroBank_sample_records.txt`: first _N_ records sliced by `guess-record-size` (or computed size if `SCHEMA` exists).

Use these dumps to decide field offsets/lengths.

### Export
```bash
python tad_parser.py export "D:\Cronos\610.РФ Авиаперелеты 05.2021 (travellers)" ^
    --output travellers.csv
```
Prints the record size and field list, then writes a UTF‑8 CSV.

## Building the Schema
Edit the top of `tad_parser.py`:
```python
SCHEMA = [
    FieldSpec("ID",         0, 10),
    FieldSpec("LASTNAME",  10, 40),
    FieldSpec("FIRSTNAME", 50, 40),
    # ...
]
RECORD_SIZE = 256      # optional; otherwise sum of field lengths
ENCODING = "cp1251"    # change if your data uses another code page
```
Guidelines:
- Offsets are zero-based. Skip headers by starting the first field later.
- Lengths must cover the whole field; under-sizing truncates data.
- Set `RECORD_SIZE` if there is padding beyond your fields; otherwise it is computed.

## Advanced Tweaks
- Parse non-text fields: extend `decode_field()` to cast to int/date/float.
- Separator-based records: modify `parse_record()` to read up to a delimiter (e.g., `0x1E`) instead of fixed slices.
- Filtering: add logic in `cmd_export()` if you need to skip specific records.
- Large files: the script streams records, but you can flush the writer periodically for very large datasets.

## Troubleshooting
| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `RECORD_SIZE is None and SCHEMA is empty` | You ran `export` without defining a schema. | Fill `SCHEMA` or set `RECORD_SIZE`. |
| Garbled CSV fields | Wrong offsets/lengths or encoding. | Re-run `inspect`, adjust `SCHEMA`, verify `ENCODING`. |
| Warning: file size not multiple of record size | Record size guess is off or there is footer data. | Correct `RECORD_SIZE` or handle trailing bytes. |
| Lots of `�` characters | Wrong encoding. | Set `ENCODING` to the correct code page. |

Use `inspect` to explore, adjust `SCHEMA` until fields align, then `export` to dump the dataset. Remember: this tool assumes fixed-width records and plain text unless you extend it. 
