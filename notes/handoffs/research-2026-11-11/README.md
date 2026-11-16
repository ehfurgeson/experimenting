# Research handoff: start here

**Checkpoint: 11 November 2026.** This folder is a portable research handoff for the agrochemical-toxicity project. Start with the handoff, then assign one guide to each research lead. The two workstreams can proceed independently and exchange evidence records using stable compound/result IDs.

1. [Project handoff](01_PROJECT_HANDOFF.md): research questions, completed work, accepted decisions, results, limitations, files and operating rules.
2. [Toxicity research guide](02_TOXICITY_RESEARCH_GUIDE.md): recover aquatic study context, evaluate 16 rat LD50 records and adjudicate the 26 priority overlap pairs.
3. [Biological evidence research guide](03_BIOLOGICAL_EVIDENCE_GUIDE.md): find defensible low-response evidence, expand scaffold diversity and prepare separately reviewed activity datasets.

Each document also has a same-name `.html` reading copy. Open **`index.html`** in a browser for an offline landing page. No server or Python installation is needed to read the HTML.

## What to send colleagues

Send this entire folder, or the sibling `research-handoff-2026-11-11.zip`. It contains the three guides, compact read-only evidence inputs and a hash inventory. Keep the directory structure intact. Sending only an individual document omits its linked evidence.

The compact inputs let a literature researcher begin without the full repository. They include the 41 aquatic records, 16 rat cases, relevant native metadata, publication leads, 26 priority overlap pairs, biological review decisions, structures and policy-specific labels. They do **not** include full-text papers, the full ECOTOX archive, all research caches, credentials or the code checkout. Use library/publisher access to retrieve original papers.

## Work without waiting for the project owner

Create `work/<your-initials>-<date>-<run>/`. Leave `reference_inputs/` and original project bundles unchanged. Each guide specifies a first assignment, fields to return, decision rules, stop conditions and a completion checklist. A documented unresolved result is a valid deliverable; do not force a positive decision to finish a task.

Research findings may be collected and peer-checked under the existing policies. A new policy, changed identity, conflicting source interpretation or proposed software integration needs a written, qualified scientific/technical review; it need not wait for the project owner if an appropriate team reviewer can handle it. Do not silently change the project's scientific definitions.

The latest code lives on the **local-only** branch `feat/weekly-research-pilots`, at `b771c87` when this package was prepared. A GitHub clone alone may not contain that branch or any ignored research assets. Code execution instructions are optional for literature researchers and require the authorized checkout and listed caches. No push or publication is authorized by this handoff.

See [reference-input notes](reference_inputs/README.md) and `PACKAGE_INVENTORY.json` for contents and provenance. Verify a transferred package with the commands in the project handoff.

## Suggested first working week

| Period | Toxicity lead | Biological lead | Integrating analyst |
|---|---|---|---|
| Day 1 | Check inputs; assign the three natural-overlap aquatic references and seven rat references | Choose the assay question and policy scope; screen for full series with negative results and new scaffolds | Confirm checkout/access; note overlay and duplicate-decision integration gaps |
| Days 2–3 | Extract by publication, peer-check important mappings, review rat pairs while papers are open | Transcribe prioritized studies, exact structures and origin evidence; retain rejected/unknown leads | Check stable IDs, structured return fields and source hashes |
| Days 4–5 | Return verified or explicitly unresolved dispositions and coverage implications | Return policy-separated decisions and actual scaffold-support gains | Review integration/test needs and prepare a new run only where supported |

This is a first-pass schedule, not a promise that inaccessible sources or model support will be resolved in five days. Continue independent tasks when one source or scientific question is blocked. Measure progress by usable evidence and explicit gaps, not papers downloaded or model scores.
