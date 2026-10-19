#!/usr/bin/env python3
"""Build and verify KILCRITIC_KORA_8.8.4_CLEAN_CTO_HARDENED.zip.

Enforces clean-release boundaries:
- Excludes __pycache__, *.pyc, *.pyo, *.pyd
- Excludes .env, .env.* (preserves .env.example)
- Excludes runtime *.db, *.db-wal, *.db-shm, *.log
- Excludes runtime storage contents (preserves .gitkeep placeholders)
- Verifies archive integrity post-creation
- Computes and prints exact file count, byte size, and SHA-256 hash.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
ARCHIVE_NAME = "KILCRITIC_KORA_8.8.4_CLEAN_CTO_HARDENED.zip"
TARGET_ZIP = DIST_DIR / ARCHIVE_NAME

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
    "dist",
}

EXCLUDE_FILE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".db",
    ".db-wal",
    ".db-shm",
    ".log",
}

EXCLUDE_EXACT_NAMES = {
    ".env",
    "kilcritic.db",
    "Thumbs.db",
    ".DS_Store",
}


def should_include(rel_path: Path) -> bool:
    parts = rel_path.parts

    # Exclude designated directories anywhere in the path hierarchy
    if any(part in EXCLUDE_DIR_NAMES for part in parts):
        return False

    file_name = rel_path.name

    # Exclude exact blacklisted filenames (e.g. .env), but strictly preserve .env.example
    if file_name in EXCLUDE_EXACT_NAMES:
        return False

    # Exclude any .env.* variants (e.g. .env.local, .env.prod) while keeping .env.example
    if file_name.startswith(".env.") and file_name != ".env.example":
        return False

    # Exclude bytecode, compiled binaries, and database file extensions
    if rel_path.suffix.lower() in EXCLUDE_FILE_EXTENSIONS:
        return False

    # Exclude runtime storage contents while preserving structural .gitkeep anchors
    if parts[0] == "storage":
        if file_name != ".gitkeep":
            return False

    return True


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_and_verify() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if TARGET_ZIP.exists():
        TARGET_ZIP.unlink()

    packaged_files: list[str] = []

    # Deterministic file ordering
    all_candidates = sorted(ROOT.rglob("*"))

    with zipfile.ZipFile(TARGET_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in all_candidates:
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT)
            if should_include(rel):
                posix_arcname = rel.as_posix()
                zf.write(p, arcname=posix_arcname)
                packaged_files.append(posix_arcname)

    # Post-creation integrity verification
    try:
        with zipfile.ZipFile(TARGET_ZIP, "r") as zf:
            corrupt = zf.testzip()
            if corrupt is not None:
                print(f"ERROR: Corrupt file detected in archive: {corrupt}", file=sys.stderr)
                sys.exit(1)
            manifest = zf.namelist()
    except Exception as exc:
        print(f"ERROR: Failed to open and verify generated ZIP: {exc}", file=sys.stderr)
        sys.exit(1)

    # Validate absence of forbidden files
    forbidden = [
        name for name in manifest
        if "__pycache__" in name
        or name.endswith((".pyc", ".pyo", ".db", ".db-wal", ".db-shm"))
        or name == ".env"
        or (name.startswith(".env.") and name != ".env.example")
    ]
    if forbidden:
        print("ERROR: Forbidden runtime/secret artifacts found in ZIP:", file=sys.stderr)
        for item in forbidden:
            print(f" - {item}", file=sys.stderr)
        sys.exit(1)

    # Required baseline files check
    if ".env.example" not in manifest:
        print("ERROR: .env.example was omitted from the archive.", file=sys.stderr)
        sys.exit(1)

    size_bytes = TARGET_ZIP.stat().st_size
    checksum = compute_sha256(TARGET_ZIP)

    print("=================================================================")
    print("KILCRITIC 8.8.4 CLEAN CTO RELEASE VERIFICATION")
    print("=================================================================")
    print(f"Archive Path : {TARGET_ZIP.resolve()}")
    print(f"Archive Name : {ARCHIVE_NAME}")
    print(f"File Count   : {len(packaged_files)}")
    print(f"Archive Size : {size_bytes} bytes ({size_bytes / 1024:.2f} KB)")
    print(f"SHA-256 Hash : {checksum}")
    print("Integrity    : VERIFIED (testzip passed, 0 forbidden artifacts)")
    print("=================================================================")


if __name__ == "__main__":
    build_and_verify()