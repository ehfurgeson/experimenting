# The seven project endpoints

**Document status:** Dated endpoint definition/coverage checkpoint, 2026-10-22. Reviewed for organization 2026-11-02.

All seven structured EPA endpoints are supported; local coverage below is dated, while current policy contracts live in tracked guides.

Current guidance: [topic note](../../current/evidence-and-identities.md) · [notes index](../../README.md). Historical figures, checkboxes and branch/session instructions below retain their original context. The old `notes/notes.md` section 10 citation below resolves to the [preserved pre-split source](../sources/research-notes-2026-11-02.md#10-toxicity-endpoints-of-interest).

Verified: 2026-10-22 against `pipeline/` and the selected cached evidence.
This answers the endpoint-identification acceptance item in
`notes/current/evidence-and-identities.md` and records the implemented support.

## Definitions and research priorities

`notes/notes.md` section 10, "Toxicity Endpoints of Interest", lists seven types:

1. **LD50**: dose associated with 50% lethality in a test population.
2. **LC50**: concentration associated with 50% lethality.
3. **EC50**: concentration associated with a specified effect in 50% of the
   test population or response range.
4. **NOAEL**: highest tested dose with no observed adverse effect.
5. **LOAEL**: lowest tested dose at which an adverse effect is observed.
6. **BMD**: modeled dose associated with a specified benchmark response.
7. **BMDL**: lower confidence bound on the benchmark dose.

These endpoint labels alone do not establish comparability across species,
routes, durations, effects, or benchmark definitions.

The notes' four highest-priority research comparisons are mammalian oral LD50
(typically rat), fish LC50 (preferably 96 h), Daphnia EC50/LC50 (preferably 48 h),
and algal growth EC50 (often 72–96 h). They are distinct from the example YAML
policies: the YAML has broad mammalian availability, two fish policies, a
Daphnia policy, and four daily-dose chronic/model-derived availability policies.
It does not yet configure an algal comparison.

## Implemented endpoint support

All seven endpoint types are supported by structured EPA hazard normalization,
definition matching, coverage, comparison records, and context-constrained
summaries. PubChem prose extraction remains limited to LD50/LC50/EC50.

| Endpoint | Standard units | Evidence basis | Default summary mode |
| --- | --- | --- | --- |
| LD50 | mg/kg | source-admitted experimental observation | potency |
| LC50 | mg/L | source-admitted experimental observation | potency |
| EC50 | mg/L | source-admitted experimental observation | potency |
| NOAEL | mg/kg or mg/kg-day | observed | availability |
| LOAEL | mg/kg or mg/kg-day | observed | availability |
| BMD | mg/kg or mg/kg-day | model_derived | availability |
| BMDL | mg/kg or mg/kg-day | model_derived | availability |

Point of departure definitions must explicitly select a standard unit; daily
doses never become total doses. Reported qualifiers are preserved rather than
rewriting a NOAEL or BMDL into an inequality. EPA records require the source's
explicit experimental mark; nonexperimental and undetermined rows remain
reviewable. BMD/BMDL retain their model-derived basis even with that source mark.

Availability policies retain observations and counts but leave potency medians,
minima, and maxima null. A point of departure potency policy must explicitly
constrain species, route, exposure hours, study type, and effect. BMD/BMDL also
require response, response interpretation, and model; BMDL requires confidence
level. Missing required context fails matching.

BMD and BMDL remain distinct observations. A source may report a BMDL without a
BMD; the pipeline retains it without inventing a partner or link. Parenthetical
response labels such as `BMDL (10)` retain the token and original source record
without assuming a risk interpretation, model, or confidence level.

## Current cached evidence

Over the selected 176 resolved compounds (60 herbicides, 116 natural products):

| Policy | PubChem herbicides | PubChem natural products | EPA herbicides | EPA natural products |
| --- | ---: | ---: | ---: | ---: |
| Mammalian oral LD50 | 39 | 30 | 36 | 14 |
| Fish LC50 | 4 | 4 | 0 | 0 |
| Rainbow-trout 96-hour LC50 | 4 | 0 | 0 | 0 |
| Daphnia magna 48-hour EC50 | 0 | 0 | 0 | 0 |
| Mammalian oral daily-dose NOAEL | 0 | 0 | 34 | 16 |
| Mammalian oral daily-dose LOAEL | 0 | 0 | 32 | 8 |
| Mammalian oral daily-dose BMD | 0 | 0 | 0 | 0 |
| Mammalian oral daily-dose BMDL | 0 | 0 | 2 | 0 |

EPA covers only approved identities (136 compounds), with all selected compounds
retained in the new workflow's denominators. Counts mean eligible compounds,
not independent studies or toxicity scores. PubChem chronic zeros reflect the
current text parser's scope. EPA BMD zeros reflect no BMD records in the caches.

The saved `experiments/data/epa_endpoint_coverage.csv` reports 76 EPA oral LD50
compounds, but rebuilding under the existing experimental-only policy gives 50.
The pre-branch adapter produces the same 50 from these raw records: the saved
comparison product is stale, not evidence of an acute-coverage regression.

Use `agrotox.epa_workflow.build_epa_hazard_offline` or
`pipeline/examples/analyze_epa_hazards.py` to rebuild from raw caches. The full
manual checkpoint and reproduction command are in
`pipeline/docs/point_of_departure_check.md`.

Aquatic PubChem evidence is sparse rather than entirely absent. The present EPA
hazard cache supplies additional mammalian and chronic evidence but no eligible
aquatic results under these definitions; an aquatic source integration remains
separate work.
