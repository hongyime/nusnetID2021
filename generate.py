"""Generate legacy NUSNET checksum strings only on explicit command execution.

The calculator preserves the original JavaScript matching/checksum behavior.
Generated strings do not establish that an account exists.
"""

import argparse
from pathlib import Path
import re
from typing import List, Optional

IDENTIFIER = re.compile(r"^A[0-9]{7}|U[0-9]{6,7}")
CHECKSUMS = "YXWURNMLJHEAB"
WEIGHTS = {"A": (1, 1, 1, 1, 1, 1), "U": (0, 1, 3, 1, 2, 7)}
STOP = 10_000_000


def calculate(identifier: str) -> Optional[str]:
    """Return the historical checksum, or None when the legacy pattern misses."""
    matched = IDENTIFIER.search(identifier.upper())
    if matched is None:
        return None
    value = matched.group(0)
    if value[0] == "U" and len(value) == 8:
        value = value[:3] + value[4:]
    total = sum(weight * int(digit) for weight, digit in zip(WEIGHTS[value[0]], value[-6:]))
    return value + CHECKSUMS[total % len(CHECKSUMS)]


def generate_ids(prefix: str, destination: Path, start: int, stop: int,
                 quiet: bool = False) -> int:
    """Append one bounded pass, preserving existing bytes and opening once."""
    if prefix not in WEIGHTS or not 1 <= start <= stop <= STOP:
        raise ValueError("Use A or U and 1 <= start <= stop <= 10000000")
    if start == stop:
        return 0
    with destination.open("a", encoding="utf-8") as output:
        for number in range(start, stop):
            value = calculate(prefix + str(number).zfill(7))
            output.write(value + "\n")
            if not quiet:
                print(value)
    return stop - start


def main(argv: Optional[List[str]] = None) -> None:
    """Parse explicit generation bounds; importing this module performs no I/O."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prefix", choices=("A", "U", "both"), default="both")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--stop", type=int, default=STOP, help="Exclusive upper bound")
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    if not 1 <= args.start <= args.stop <= STOP:
        parser.error("Use 1 <= start <= stop <= 10000000")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prefixes = ("A", "U") if args.prefix == "both" else (args.prefix,)
    for prefix in prefixes:
        generate_ids(prefix, args.output_dir / ("nusnetid" + prefix + ".txt"),
                     args.start, args.stop, args.quiet)


if __name__ == "__main__":
    main()
