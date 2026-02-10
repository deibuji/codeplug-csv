# Codeplug and Flashing Feasibility

Date: February 10, 2026

## Goal

Enable a one-command workflow that takes a DMR `RADIO_ID` and flashes a radio without requiring vendor GUI CPS tooling.

## Research summary

### 1) Native Anytone CPS `.rdt` binary generation

- Feasible in principle only through reverse engineering.
- Not recommended as the first implementation path in this repo.

Why:

- Vendor CPS formats are proprietary binaries (`.rdt`) and typically tied to Windows-first tooling.
- Binary format details can change across CPS/radio firmware revisions.
- Maintaining robust `.rdt` emitters requires constant compatibility testing against model/firmware variants.

### 2) Open CLI toolchain (`dmrconfig`) generation + direct write

- Feasible today.
- Cross-platform enough for practical automation (Linux/macOS/Windows environments with serial USB support).
- Best fit for an OS-agnostic task command in this project.

Why:

- `dmrconfig` supports D878-family radios and provides direct read/write actions.
- Config format is text-based and can be generated from this repo's existing CSV outputs.
- We can keep all radio data generation in this codebase and delegate hardware protocol details to a mature external tool.

### 3) QDMR as an alternate backend

- Also feasible.
- Could be added later as a secondary backend if needed.

Why:

- QDMR supports Anytone AT-D878UV/II and has CLI operations (including write).
- Useful fallback if users prefer QDMR ecosystem over dmrconfig.

## Implemented branch scope

This branch implements Option 2 with an experimental workflow:

1. Generate CSVs as before (`task run`).
2. Resolve operator profile from `users.csv` by `RADIO_ID`.
3. Render a `dmrconfig` config file (`output/codeplug-<id>.conf`).
4. Optionally flash with `dmrconfig -c`.

Task commands:

- `task prepare-flash RADIO_ID=<id>`
- `task flash RADIO_ID=<id>`

## Risks and constraints

- `dmrconfig` must be installed by the user.
- Mapping from CPS CSV columns to dmrconfig semantics is not one-to-one; some advanced per-channel options are simplified.
- Hardware flashing is inherently high-risk if a backend bug exists; test with backups first.

## Recommended next steps

1. Add `task backup` (read current radio image first) and require running it before `task flash` in CI/docs.
2. Add hardware-in-the-loop validation for AT-D878UV and AT-D878UVII profiles.
3. Add optional QDMR backend parity once dmrconfig path stabilizes.

## Sources

- dmrconfig repository: https://github.com/OpenRTX/dmrconfig
- dmrconfig man page: https://manpages.debian.org/testing/dmrconfig/dmrconfig.1.en.html
- QDMR supported radios: https://dm3mat.darc.de/qdmr/manual/ch01s03.html
- QDMR repository: https://github.com/hmatuschek/qdmr
- Vendor CPS context and `.rdt` references:
  - https://support.bridgecomsystems.com/support/solutions/articles/63000282632-codeplug-2-0-conversion-guide
  - https://support.bridgecomsystems.com/support/solutions/articles/63000268352-at-d878uvii-plus-faq
