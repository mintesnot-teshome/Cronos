import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List

# ---------- CONFIG: YOU WILL EDIT THIS PART AFTER INSPECTION ----------

@dataclass
class FieldSpec:
    name: str       # column name
    offset: int     # byte offset in the record
    length: int     # byte length
    ftype: str = "str"  # "str", "int", "float" etc. (for now we treat everything as text)


# EXAMPLE ONLY – replace with real values after inspection.
# Offsets are 0-based relative to the start of each record.
SCHEMA: List[FieldSpec] = [
    # FieldSpec("ID",        0,   10, "str"),
    # FieldSpec("LASTNAME", 10,   40, "str"),
    # FieldSpec("FIRSTNAME",50,   40, "str"),
    # FieldSpec("BIRTHDATE",90,   10, "str"),
    # ...
]

# If records seem to be separated by CRLF or other separators, you can
# override this later. For now we assume strictly fixed-size records.
RECORD_SIZE = None  # If None, it will be computed as sum(field.length)

# Encoding – МВД data is usually cp1251
ENCODING = "cp1251"


# ---------- CORE PARSER LOGIC ----------

def compute_record_size():
    global RECORD_SIZE
    if RECORD_SIZE is None:
        if not SCHEMA:
            raise ValueError(
                "RECORD_SIZE is None and SCHEMA is empty. "
                "Fill SCHEMA with fields after inspection or set RECORD_SIZE explicitly."
            )
        RECORD_SIZE = sum(f.length for f in SCHEMA)
    return RECORD_SIZE


def load_records(dat_path: Path):
    """Read raw records from CroBank.dat as fixed-size chunks."""
    size = dat_path.stat().st_size
    rec_size = compute_record_size()
    if size % rec_size != 0:
        print(
            f"WARNING: file size {size} is not a multiple of record size {rec_size}. "
            f"There may be a header/footer or the schema is wrong."
        )
    with dat_path.open("rb") as f:
        while True:
            chunk = f.read(rec_size)
            if not chunk or len(chunk) == 0:
                break
            if len(chunk) < rec_size:
                print("WARNING: truncated record at end of file.")
                break
            yield chunk


def decode_field(raw: bytes, ftype: str) -> str:
    txt = raw.rstrip(b"\x00 ").decode(ENCODING, errors="replace")
    txt = txt.replace("\r", "").replace("\n", "")
    # You can add type casting here if needed (int/float/parsing dates)
    return txt


def parse_record(raw_record: bytes):
    row = {}
    for field in SCHEMA:
        start = field.offset
        end = field.offset + field.length
        slice_bytes = raw_record[start:end]
        row[field.name] = decode_field(slice_bytes, field.ftype)
    return row


# ---------- INSPECTION HELPERS ----------

def dump_struct_info(stru_path: Path, out_txt: Path):
    """Dump CroStru.dat as hex + best-effort cp1251 text to help reverse engineer."""
    data = stru_path.read_bytes()

    with out_txt.open("w", encoding="utf-8") as out:
        out.write("=== HEX DUMP (first 1024 bytes) ===\n\n")
        max_len = min(len(data), 1024)
        for i in range(0, max_len, 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            out.write(f"{i:08X}  {hex_part:<48}  {ascii_part}\n")

        out.write("\n\n=== ATTEMPTED CP1251 TEXT DECODE (entire file) ===\n\n")
        try:
            text = data.decode(ENCODING, errors="replace")
        except Exception as e:
            text = f"<decode error: {e}>"
        out.write(text)


def dump_sample_records(dat_path: Path, out_txt: Path, max_records: int = 5, guessed_record_size: int = 256):
    """
    Dump first few records in hex and cp1251 text to help guess RECORD_SIZE and field layout.
    If SCHEMA is empty, uses guessed_record_size for slicing.
    """
    data = dat_path.read_bytes()
    rec_size = compute_record_size() if SCHEMA else guessed_record_size

    with out_txt.open("w", encoding="utf-8") as out:
        out.write(f"File size: {len(data)} bytes\n")
        out.write(f"Using record size: {rec_size} bytes (change guessed_record_size if needed)\n\n")

        num = min(max_records, len(data) // rec_size)
        for i in range(num):
            out.write(f"=== RECORD {i} ===\n")
            rec = data[i*rec_size:(i+1)*rec_size]
            # Hex dump
            for off in range(0, len(rec), 16):
                chunk = rec[off:off+16]
                hex_part = " ".join(f"{b:02X}" for b in chunk)
                ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
                out.write(f"{off:04X}  {hex_part:<48}  {ascii_part}\n")

            # Attempt decoded text (as one line)
            try:
                txt = rec.decode(ENCODING, errors="replace")
            except Exception as e:
                txt = f"<decode error: {e}>"
            out.write("\nDecoded (cp1251, best effort):\n")
            out.write(txt)
            out.write("\n\n")


# ---------- MODES: INSPECT & EXPORT ----------

def cmd_inspect(args):
    base = Path(args.base_dir)

    stru_path = base / "CroStru.dat"
    bank_path = base / "CroBank.dat"

    if not stru_path.exists():
        raise FileNotFoundError(f"{stru_path} not found")
    if not bank_path.exists():
        raise FileNotFoundError(f"{bank_path} not found")

    out_stru = base / "CroStru_dump.txt"
    out_bank = base / "CroBank_sample_records.txt"

    print(f"[+] Dumping structure info from {stru_path} to {out_stru}")
    dump_struct_info(stru_path, out_stru)

    print(f"[+] Dumping sample records from {bank_path} to {out_bank}")
    dump_sample_records(bank_path, out_bank, max_records=args.max_records, guessed_record_size=args.guess_record_size)

    print("\n[✓] Inspection files written:")
    print(f"    {out_stru}")
    print(f"    {out_bank}")
    print("Open them in a text editor and infer fields (names, offsets, lengths).")
    print("Then edit SCHEMA and (optionally) RECORD_SIZE at the top of this script.")


def cmd_export(args):
    base = Path(args.base_dir)
    bank_path = base / "CroBank.dat"
    if not bank_path.exists():
        raise FileNotFoundError(f"{bank_path} not found")

    out_csv = Path(args.output)
    rec_size = compute_record_size()
    print(f"[+] Using record size = {rec_size} bytes")
    print(f"[+] Fields: {[f.name for f in SCHEMA]}")
    print(f"[+] Reading {bank_path}")

    with out_csv.open("w", newline="", encoding="utf-8") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=[f.name for f in SCHEMA])
        writer.writeheader()
        count = 0
        for raw in load_records(bank_path):
            row = parse_record(raw)
            writer.writerow(row)
            count += 1

    print(f"[✓] Exported {count} records to {out_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Minimal Tad/Dat-style CroBank parser (manual schema)."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_inspect = sub.add_parser("inspect", help="Inspect structure & sample records to reverse-engineer schema")
    p_inspect.add_argument("base_dir", help="Directory containing CroBank.dat, CroStru.dat, etc.")
    p_inspect.add_argument("--max-records", type=int, default=5, help="How many example records to dump")
    p_inspect.add_argument("--guess-record-size", type=int, default=256,
                           help="Guessed record size in bytes when SCHEMA is empty")
    p_inspect.set_defaults(func=cmd_inspect)

    p_export = sub.add_parser("export", help="Export CroBank.dat to CSV using SCHEMA")
    p_export.add_argument("base_dir", help="Directory containing CroBank.dat")
    p_export.add_argument("--output", "-o", default="CroBank_export.csv", help="Output CSV file")
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
