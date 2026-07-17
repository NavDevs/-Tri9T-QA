# Instructions for Antigravity — Implementation Phase (Tri9T AI Internship Assignment)

Context confirmed: `IMPORTANT_ASSIGNMENT_UPDATE.txt` exists in `data/` alongside
`ct200_manual.pdf` and `ct200_manual_v2.pdf` — input format is PDF, not
Markdown. `PRD.md`, `TRD.md`, `STRUCTURE.md`, and `CONTEXT.md` are already
written and included in this repo. Read all four before writing any code.

## Working rules (apply for the entire build)

1. **Read before you write.** Before creating or editing any file, read its
   entry in `CONTEXT.md` and its listing in `STRUCTURE.md`. Don't work from
   memory of what you intended a file to contain.

2. **Update CONTEXT.md in the same commit as the file it describes.** Every
   time you create or meaningfully change a file in `app/` or `tests/`, update
   that file's entry: status, real public interface (actual signatures, not
   aspirational ones), dependencies, and known gaps. An entry that says
   `NOT STARTED` for a file that already has code in it is a bug — fix it in
   the same commit.

3. **Update STRUCTURE.md whenever the folder structure changes** — new file,
   renamed file, deleted file. It must reflect what's actually on disk.

4. **Log as you go in PROGRESS_LOG.md.** For each implementation step: what
   you attempted, what you actually verified (tests run, output inspected),
   and any deviation from `TRD.md` with your reasoning. Don't summarize after
   the fact.

5. **When you hit one of the manual's real irregularities** (per TRD §3), stop
   and record it — in both `TRD.md` §3 and the relevant `CONTEXT.md` entry —
   before writing the workaround. The assignment explicitly wants this
   process documented, not just the fix.

6. **Small, incremental commits.** One logical change per commit, real
   messages. Write the irregularity-targeted unit tests alongside the parser
   code that handles them, not after.

7. **Don't guess silently.** If something in `PRD.md`/`TRD.md` is ambiguous
   once you're in the code, note the ambiguity and your resolution in
   `PROGRESS_LOG.md` rather than picking silently.

## Build order

1. `app/database.py`, `app/models.py` — SQL schema from TRD §2
2. `app/parser.py` + `tests/test_parser.py` — ingest `ct200_manual.pdf`,
   inspect real output, catalog irregularities in TRD §3 as you find them
3. `app/nosql.py` — TinyDB setup
4. `app/versioning.py` + `tests/test_versioning.py` — ingest
   `ct200_manual_v2.pdf`, verify matching/diff logic against TRD §4
5. `app/schemas.py`, `app/llm.py` — prompt + structured-output validation per
   TRD §5
6. `app/staleness.py` + `tests/test_staleness.py` — TRD §7
7. `app/main.py` — wire all endpoints from TRD §8
8. `tests/test_api.py` + `scripts/demo_flow.sh` — full end-to-end demo

Stop after each numbered step and show me: the diff, the updated `CONTEXT.md`
entries, the updated `PROGRESS_LOG.md` entry, and test output — before moving
to the next step.
