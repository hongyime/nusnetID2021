# NUSNET IDs 2021
code to generate all possible IDs used in NUS.

## Setup

Install the project dependencies for the detected stack, then run the local entry point documented in the source tree.

## Usage

Review the repository source and configuration files for the current runtime entry points.


## Project Status

Unclear Singapore education utility pending fuller documentation and setup notes. The current Phase 3 pass standardises repository hygiene without inventing implementation details beyond what is visible in the repository.

## Setup

Review the source tree for the current runtime entry point, install the dependencies for the detected stack, and keep local secrets in environment files that are ignored by git.

## Usage

Run the project using the scripts or entry points already present in the repository. Update this section with exact commands once the runtime contract is confirmed.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

2026-09-12 maintenance: the LFS guard now checks out one commit because it scans the current index. Git scan errors fail the job instead of appearing to be a successful empty scan. The shared source change is verified in [sourcerepo PR #51](https://github.com/hongyime/sourcerepo/pull/51), with all ten Linux fixtures passing. Existing pointer rejection, opt-out behavior and action references are preserved. This workflow-only change leaves application code and data unchanged. Release requires passing hosted checks, followed by verification of the merged main workflow.
