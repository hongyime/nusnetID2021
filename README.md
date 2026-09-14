# NUSNET IDs 2021

An offline generator of strings matching the historical NUS matriculation checksum.
A generated string does not establish that an account or person exists.

## Usage

Python 3.8 or newer is sufficient; the generator uses only the standard library.
Run a small, explicit range first:

```sh
python generate.py --prefix A --start 1 --stop 4 --output-dir sample-output --quiet
```

`--stop` is exclusive. Use `--prefix U` for the other format or `--prefix both`
for both. Without range options, a direct invocation writes numbers 1 through
9,999,999 for each selected prefix. Importing `generate` performs no generation.

Output is appended to `nusnetidA.txt` and/or `nusnetidU.txt` in the output directory.
Existing contents are preserved. A run emits each selected range once; rerunning
the same range intentionally appends it again. `--quiet` suppresses per-ID output.

## Validation

Tests use small synthetic ranges and temporary files, including comparison with
the original JavaScript checksum. Node.js is required only for that reference test.
No retained datasets or real accounts are accessed by the tests.

```sh
python -m unittest discover -s tests -v
python -m pip install pylint
pylint $(git ls-files '*.py')
```

CI runs the tests and lints every tracked Python file on Python 3.8, 3.9 and 3.10.
The shared bot helper keeps its existing ownership, current-SHA, required-check
and ordinary-merge gates; its existing CLI filename has a narrow naming allowance
in `.pylintrc`. The label workflow uses the repository's `.github/labels.yml`.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

2026-09-12 maintenance: the LFS guard now checks out one commit because it scans the current index. Git scan errors fail the job instead of appearing to be a successful empty scan. The shared source change is verified in [sourcerepo PR #51](https://github.com/hongyime/sourcerepo/pull/51), with all ten Linux fixtures passing. Existing pointer rejection, opt-out behavior and action references are preserved. This workflow-only change leaves application code and data unchanged. Release requires passing hosted checks, followed by verification of the merged main workflow.
