**# Researcher guide: compound origin and herbicidal-activity labels**



Prepared **\*\*2026-10-29\*\*** for

\`analysis/outputs/chembl-review-2026-10-29-final/label_review_template.csv\`.

This guide describes the frozen dataset and the current label contract. It does

not approve a biological labeling policy or assign labels to individual compounds.



**## 1. What you are being asked to produce**



Review each compound's **\*\*identity\*\***, **\*\*natural occurrence\*\***, and \*\*measured plant

activity\*\*, then record only conclusions supported by traceable evidence.

An unresolved row is a legitimate research result: keep its label \`unknown\` and

explain the unresolved issue in the separate evidence log.



The project aims to predict herbicidal activity from chemical structure when

toxicity measurements are unavailable. The structural model uses formula

composition, RDKit descriptors and/or Morgan fingerprints with PCA and logistic

regression. Its strongest existing result, 91.9% balanced accuracy, predicts

membership in a selected herbicide versus natural-product collection. It does

not establish that an unfamiliar compound is biologically herbicidal.



The task here is to build defensible ground truth for two independent questions:



\| Question | Worksheet field | Model encoding |

\|---|---|---|

\| Is natural occurrence documented under the agreed origin-review definition? | \`natural_origin\` | \`natural\` = 1; \`synthetic\` = 0; \`unknown\` = missing |

\| Does the compound meet a specified plant-assay activity policy? | \`herbicidal_activity\` | \`active\` = 1; \`inactive\` = 0; \`unknown\` = missing |



A naturally occurring herbicide can be both \`natural\` and \`active\`. A substance

made by total synthesis can still be a naturally occurring compound. Unknown

activity never becomes an inactive training example. These labels do not mean

safe/unsafe, commercially registered/unregistered, or experimentally studied/not

studied. Mammalian toxicity, fish toxicity, ToxCast hits and TEST predictions are

separate evidence and cannot supply plant-activity labels by themselves.



**## 2. What is in this particular worksheet**



The worksheet contains **\*\*154 ChEMBL molecule IDs\*\***, initially all unknown for both

labels. It was derived from \*\*157 activity observations in 14 assays from 14

publications\*\*, retrieved from ChEMBL_37 on the preceding acquisition run. There

are 28 structural scaffold groups. Five structures overlap the original curated

selection, leaving 149 additional structures. The collection is a purposive

literature-derived sample, not a representative inventory of natural products

or a balanced active/inactive training set.



Thirteen assays concern *\*Amaranthus retroflexus\**; one concerns *\*A. blitum\** subsp.

*\*oleraceus\**. The assays differ in application dose, timing, endpoints and exposure

methods. Source assay descriptions containing “herbicidal” are discovery clues,

not reviewed binary labels. Individual papers can contain a close analogue series

with many rows but little independent chemical diversity.



The frozen observations include 109 exact-value relations, 45 inequalities and

three records without numeric outcomes. Two outcomes use millimetres rather than

percent. The dataset includes the explicit comment “Not Determined.” These are

reasons to inspect methods and source tables before interpreting a numeric value.



Two molecule IDs have repeated observations: \`CHEMBL452197\` has three and

\`CHEMBL95764\` has two. The worksheet has one row per molecule, so the evidence log

must retain the distinct studies before a policy-specific compound decision is made.



**## 3. Start with the supplied materials**



Paths below are relative to the repository root. The raw snapshots and generated

outputs are local ignored files; a researcher receiving only a Git clone will

also need this dataset and its source snapshots.



\| Material | Location and use |

\|---|---|

\| Frozen label template | \`analysis/outputs/chembl-review-2026-10-29-final/label_review_template.csv\`; preserve as the baseline |

\| Frozen source observations | Same directory, \`activity_review\.csv\`; join \`molecule_chembl_id\` to worksheet \`compound_id\` |

\| Frozen structures | Same directory, \`candidates.csv\`; join on \`compound_id\` |

\| Frozen provenance | Same directory, \`manifest.json\`; records input/code/lock/product hashes |

\| Full source bundles | \`analysis/outputs/chembl-2026-10-28/raw/chembl/\<assay_id>.json\` |

\| Researcher working pack | \`analysis/outputs/chembl-researcher-handoff-2026-10-29/\` |

\| Working label copy | Working pack, \`reviewed_labels.csv\`; edit this copy, not the frozen template |

\| Compound navigation | Working pack, \`compound_index.csv\`; 154 rows in worksheet order, with molecule links and evidence summaries |

\| Per-compound evidence | Working pack, \`compound_evidence_packets.md\`; one section for every worksheet ID, including supplied SMILES, observations and source links |

\| Observation-level review log | Working pack, \`evidence_log.csv\`; 157 prefilled source rows, with reviewer decisions left blank/unreviewed |

\| Policy worksheet | Working pack, \`policy_draft.md\`; an explicitly unapproved draft to complete before assigning known activity labels |



The working pack is a handoff aid, not another evidence source. Its metadata

comes from the frozen files. Live ChEMBL pages can change after a release; retain

the frozen ID, original record, version and source hash when recording corrections.

Do not overwrite a source outcome or silently substitute a live structure.



The maintained export command can rebuild frozen review products in a **\*\*new\*\***

directory; it does not recover later manual annotations:



\`\`\`bash

analysis/.venv/bin/python analysis/review_assays.py \\

&#x20; \--snapshots analysis/outputs/chembl-2026-10-28 \\

&#x20; \--output analysis/outputs/chembl-review-fresh-copy

\`\`\`



**## 4. Exact worksheet field definitions**



Keep these seven column names. The CSV importer rejects additional columns;

reviewer names, dates, confidence, search history and alternative outcomes belong

in the evidence log. Preserve compound IDs, capitalization and unique rows.



\| Field | Accepted content | What a researcher should enter |

\|---|---|---|

\| \`compound_id\` | An existing, unique worksheet ID | Preserve the supplied ChEMBL **\*\*molecule\*\*** ID. An assay/document ID cannot replace it. |

\| \`activity_context\` | Text | For a known activity label: species, life stage, endpoint, observed value and qualifier, units, dose/concentration and units, exposure/application method, pre-/post-emergence timing, duration, controls/reference treatment, and relevant source location. Mark unreported details explicitly. |

\| \`activity_policy\` | Text identifying a reviewed policy | For known activity: the agreed, versioned policy ID shared by every known activity label in the training file. This identifies a written biological rule, not just a convenient batch name. |

\| \`activity_reference\` | Text citation | For known activity: primary DOI or stable publication reference, table/figure/page/SI and source compound number, plus ChEMBL assay/activity IDs where available. An unresolved search query or placeholder is not adequate evidence. |

\| \`herbicidal_activity\` | \`active\`, \`inactive\`, \`unknown\` or blank | Use known labels only when evidence meets the agreed policy. Prefer explicit \`unknown\` for unresolved, excluded, conflicting, intermediate or untested cases. |

\| \`natural_origin\` | \`natural\`, \`synthetic\`, \`unknown\` or blank | Record the reviewed origin category independently of activity. \`synthetic\` requires an agreed operational meaning and affirmative supporting provenance; absence of an occurrence citation is insufficient. |

\| \`origin_reference\` | Text citation | Required for a known origin label. Cite exact-structure occurrence/provenance evidence, organism and source location; explain the basis in the log. |



The code strips surrounding whitespace but categorical values remain

case-sensitive. Known origin requires a nonempty \`origin_reference\`. Known

activity requires nonempty \`activity_reference\`, \`activity_context\` and

\`activity_policy\`. Blank/unknown labels become null targets and are excluded

from that supervised task. Unknown rows may retain citations and context while

research remains unresolved.



There is \*\*no separate activity-confidence, origin-policy, reviewer, or review

status column\*\* in this schema. Record those in the log/policy document. Numeric

codes such as \`0\`, \`1\`, \`yes\`, \`no\` and \`uncertain\` are not accepted label values.

Do not paste predicted probabilities, descriptors or assay values into label cells.



**## 5. Agree on a biological policy before labeling a batch**



There is currently **\*\*no approved activity policy for all 14 assays\*\***. Complete

\`policy_draft.md\` with the research lead and record its status, reviewer, date and

version. The present software accepts one activity policy across known activity

labels in a training dataset. It does not verify that species, endpoints and

exposures actually satisfy that policy.



A usable policy defines:



1\. The claim being predicted: for example, a specified whole-plant response under

&#x20;  stated conditions, rather than universal “herbicidal potential.”

2\. Eligible species, stages, assay endpoints, application modes and exposure times.

3\. Eligible concentrations/application rates, units, dose basis and formulations.

4\. Minimum controls, replication, measurement quality and source-verification rules.

5\. Explicit active and inactive thresholds and a gray zone that remains unknown.

6\. Treatment of exact values, ranges, inequalities, text-only outcomes and missing data.

7\. Treatment of multiple doses, discordant replicates and multiple publications.

8\. Identity rules for salts, esters, stereoisomers, mixtures and parent structures.

9\. Any scientifically justified cross-assay pooling and which differences prevent it.

10\. Publication/analogue-series grouping and the plan for reserving independent validation data.



Thresholds should be justified biologically before evaluating model performance.

Do not choose them to produce attractive class balance or classifier accuracy.

A source's reported bins are not automatically the project's policy. A low

response is a negative only within the eligible assay/exposure definition; it

is not proof that the molecule cannot affect any plant at any dose.



If assays require different policies, keep separate policy-specific label files

and corresponding evidence logs. Do not reuse one policy ID to disguise

heterogeneous outcomes. For an initial coherent dataset, keep out-of-scope rows

unknown rather than forcing all 154 IDs into known categories.



**## 6. Repeat this workflow for every compound ID**



**### A. Locate the evidence and confirm identity**



Open the matching section in \`compound_evidence_packets.md\`, then the molecule

report and all linked assays/publications. ChEMBL distinguishes compound, assay,

activity and document entities; its bioactivity views connect the measured results

to those entities. The official [search guide]\(https\://www\.ebi.ac.uk/training/online/courses/chembl-quick-tour/accessing-chembl-data/searching-using-the-web-interface/)

and [results guide]\(https\://www\.ebi.ac.uk/training/online/courses/chembl-quick-tour/accessing-chembl-data/viewing-results-from-the-web-interface/)

explain navigation; the [API resource reference]\(https\://github.com/chembl/GLaDOS-docs/blob/master/web-services/chembl-data-web-services.md)

provides molecule, assay, activity and document endpoints.



Compare the supplied SMILES with the exact compound in the paper/SI, using its

source compound number. Check substitution positions, stereochemistry, charge,

salt/ester versus parent, and mixture status. A matching common name, formula

or similar drawing alone is insufficient. Use InChIKey/structure records as

identity checks where available; do not transfer evidence between related

structures without an explicit normalization policy.



If identity is ambiguous, mark the log \`identity_unresolved\` and leave affected

labels unknown. Document the proposed mapping/correction without editing the

frozen source or guessing a replacement compound ID. Keep this compound out of

known-label training until the structure/evidence mapping is reviewed.



**### B. Read the original assay methods and results**



Use the DOI to locate the paper and supplementary information through a

publisher, institutional library or legitimate repository. Record what was

actually accessed. Abstracts, assay descriptions and secondary databases are

useful leads; they do not replace a missing method or compound-specific result.

If the required source is unavailable, record \`source_unavailable\` and retain

unknown labels until the evidence requirement is met.



For each observation, transcribe the endpoint, qualifier, value, units, organism,

application method/rate, duration, controls and source location. Distinguish

measurement units from application units: percent growth inhibition, necrosis

in mm and g active ingredient/ha are different quantities. Do not silently

convert or repair a suspicious dose transcription.



The frozen review row contains readable fields and \`raw_activity_json\`. The raw

bundle also contains the full cached assay/document metadata. Inspect those when

fields are absent or abbreviated; even the full cache may lack methods that

require reading the publication.



**### C. Record an observation-level judgment**



Use \`evidence_log.csv\` to record reviewer/date, primary-source location, identity

match, method details, policy eligibility, proposed decision and unresolved issues.

Keep the original source fields intact. If a paper corrects a database extraction,

record the original value, corrected interpretation, citation and reason.

Add separate log rows for newly found assays or natural-occurrence evidence;

multiple observations must not be collapsed into one unlabeled note.



Recommended status terms in the **\*\*log only\*\*** are \`unreviewed\`, \`in_progress\`,

\`source_unavailable\`, \`identity_unresolved\`, \`out_of_scope\`, \`conflict\`,

\`reviewed_unknown\`, and \`reviewed_known\`. They are not new CSV label categories.



**### D. Resolve the activity label under the selected policy**



Use eligible experimental outcomes only. Resolve conflicting evidence according

to the written policy and record the chosen source(s) in the label reference.

Do not average across species/doses, take a majority vote of assays, select only

the strongest response, or turn every missing measurement into inactive.

When conflict or eligibility remains unresolved, retain \`unknown\` and explain why.



For a known label, fill all three supporting fields. A useful context format is:



\`\`\`text

species=\<verified taxon>; stage=\<reported stage>; endpoint=\<defined endpoint>;

response=\<qualifier and value with units>; application=\<rate and units>;

mode=\<pre/post-emergence and application method>; duration=\<reported interval>;

controls=\<verified control/reference>; source=\<DOI, table/SI, compound number>;

policy=\<agreed version>; interpretation=\<why the evidence meets the rule>

\`\`\`



This is a formatting example, not a filled label or a recommended threshold.

Use a semicolon-separated citation string if several primary sources support the

same policy-specific conclusion. Preserve contrary evidence in the log.



**### E. Research natural occurrence separately**



Begin with the confirmed structure, names and identifiers. Search occurrence

records and follow their cited isolation/identification literature. The project's

[source assessment]\(compound_sources.md) covers LOTUS, COCONUT and KNApSAcK as

research starting points. Database inclusion or a search hit alone does not prove

occurrence of the exact stereoisomer/chemical form in the row.



For \`natural\`, seek traceable documentation of occurrence/identification in a

named organism and confirm exact identity and source location. Record an

organism/taxon and a primary citation where available. If a compound is both

isolated from nature and synthesized in a laboratory, synthesis does not remove

its documented natural occurrence.



For \`synthetic\`, first agree what that operational class asserts and what

positive provenance evidence establishes it. A paper describing synthesis,

absence from a natural-product database, or commercial herbicide status does

not independently prove nonoccurrence in nature. If the agreed definition cannot

be supported, use \`unknown\`. The schema has no origin-policy field; record the

origin-review definition and its version in the policy document and log.



Origin and activity can be reviewed independently. A defensible known activity

label can coexist with unknown origin, and vice versa.



**### F. Finish the compound review**



Save one row per original ID in \`reviewed_labels.csv\`. Preserve unknowns and

blank supporting fields where conclusions are unresolved. Update the log status,

reviewer/date, source access and remaining questions. Ask for a second scientific

review of disputed identity, origin or threshold interpretations before accepting

known labels. A reviewed-unknown row counts as completed research when its

reason and search coverage are documented.



**## 7. Decision rules for common difficult cases**



\| Observation | Appropriate treatment |

\|---|---|

\| No paper, no assay, or missing numeric value | Unknown unless sufficient eligible evidence is obtained elsewhere; log the gap |

\| “Not Determined” | Not an inactive result |

\| Exact 0% response | Potential policy-specific negative only after checking endpoint meaning, exposure, controls and source identity |

\| Exact 100% response | Potential positive under eligible conditions; not automatic proof across other species/doses |

\| \`<=50%\`, \`<50%\`, \`>80%\` | Preserve the inequality and determine whether its entire possible range satisfies the policy's rule |

\| Intermediate response or an interval crossing a threshold | Unknown/gray zone unless the policy explicitly resolves it |

\| Millimetres of leaf necrosis | Retain as that endpoint; do not convert into percent whole-plant inhibition |

\| Different outcomes in different studies | Keep all observations; resolve under the chosen policy or leave unknown |

\| Similar analogue, salt or ester has a result | Do not transfer it to this row without identity/normalization review |

\| No natural-occurrence record found | Unknown origin; the search result is not affirmative synthetic provenance |

\| Favorable SA, Lipinski/Tice, formula or model score | Structural/model information only; it does not supply a training label |



For an **\*\*illustrative, unapproved\*\*** rule defining active as at least 80% and

inactive as at most 20%, \`>80%\` guarantees the active bound, whereas \`<=50%\`

does not guarantee inactivity. The values 80 and 20 here demonstrate logic,

not a recommended policy. Strict versus inclusive thresholds matter: \`<=50%\`

would still be ambiguous under a rule requiring strictly less than 50%.



**## 8. Concrete cases already present in this batch**



These are frozen database observations, **\*\*not completed scientific reviews\*\***.

Their primary papers have not been verified by this handoff.



\- **\*\*CHEMBL1881194\*\***: activity \`12342582\`, assay \`CHEMBL3048455\`, source

&#x20; [10.1021/jf203383s]\(https\://doi.org/10.1021/jf203383s), has “Not Determined”

&#x20; and no numeric outcome. Start with unknown activity; do not infer inactivity.

\- **\*\*CHEMBL452197\*\***: recorded responses are 100%, 0% and 73.3% in three assays

&#x20; (\`CHEMBL970505\`, \`CHEMBL3047330\`, \`CHEMBL3047983\`). This is a priority

&#x20; multi-context review; none of the three values supplies a universal label.

\- **\*\*CHEMBL95764\*\***: two observations both report 90%, but one is post-emergence

&#x20; and the other pre-emergence. Matching numeric values do not make their

&#x20; exposure conditions interchangeable.

\- **\*\*CHEMBL469706\*\*** and **\*\*CHEMBL2393053\*\***: the frozen leaf-necrosis assay

&#x20; \`CHEMBL3053086\` has no numeric outcome for these rows. Consult raw text and

&#x20; the paper/SI; retain unknown if an eligible result cannot be established.

\- **\*\*CHEMBL1235774\*\***: activity \`12344237\` records 100% in the pre-emergence

&#x20; assay \`CHEMBL3048455\`. Verify the original compound and method before any

&#x20; policy-specific positive label; this value says nothing by itself about origin.



Assay descriptions for \`CHEMBL3047983\`, \`CHEMBL3051568\` and \`CHEMBL3066743\`

contain application rates written as 150 or 375 **\*\*kg/ha\*\***. Verify those units

against the original papers; do not assume the intended unit or silently repair

it. \`CHEMBL3079324\` uses g/a and a different species, while \`CHEMBL3053086\`

uses a leaf-puncture endpoint. These contexts require explicit eligibility review.

The per-compound packets preserve links to the source assay for every observation.



The 24-record assay \`CHEMBL3066645\` reports >80% and <50% response bins. Earlier

exploratory modeling of those bins performed poorly and lacked support for

five-/three-fold scaffold validation. Those pilot bins are not an approved

labeling policy, and their model predictions must not be used as ground truth.



**## 9. Validate the worksheet without fitting a model**



From the repository root, after saving the working copy:



\`\`\`bash

analysis/.venv/bin/python - <<'PY'

import csv

import sys

from collections import Counter

from pathlib import Path

sys.path.insert(0, str(Path('analysis').resolve()))

from labels import LABEL_FIELDS, attach_labels

from screen import prepare

root = Path('analysis/outputs/chembl-researcher-handoff-2026-10-29')

source = Path('analysis/outputs/chembl-review-2026-10-29-final')



def read(path):

&#x20;   with path.open(encoding='utf-8-sig', newline='') as stream:

&#x20;       reader = csv.DictReader(stream)

&#x20;       if path.name == 'reviewed_labels.csv':

&#x20;           if len(reader.fieldnames or []) != len(LABEL_FIELDS) or set(reader.fieldnames or []) != LABEL_FIELDS:

&#x20;               raise ValueError('Preserve exactly the seven label columns')

&#x20;       return list(reader)



candidates = read(source / 'candidates.csv')

labels = read(root / 'reviewed_labels.csv')

if len(labels) != len(candidates) or {r['compound_id'] for r in labels} != {r['compound_id'] for r in candidates}:

&#x20;   raise ValueError('Preserve one row for every original compound ID')

attached = attach_labels(prepare(candidates), labels)

print('Rows:', len(attached))

print('Activity:', Counter(r['activity_target'] for r in attached))

print('Origin:', Counter(r['origin_target'] for r in attached))

print('Schema/identity-conflict checks passed; biological evidence still requires review.')

PY

\`\`\`



This checks the project schema, IDs, required text, policy consistency and

contradictory known labels for identical canonical structures. It does not

validate a citation, biological comparability, threshold rationale or the truth

of a label. It performs local chemistry preparation but does not fit a classifier

or make network requests. Save CSVs in UTF-8, preserve exact headers, and use

proper CSV quoting for commas or multiline context. Both this check and the current screening reader

accept a UTF-8 byte-order mark from a spreadsheet export.



Do not run model evaluation until the labels and policy have passed scientific

review. Once accepted, a later modeling run can use the same candidate structures

as its compound table and the reviewed file as \`--labels\`:



\`\`\`bash

analysis/.venv/bin/python analysis/screen.py \\

&#x20; \--compounds analysis/outputs/chembl-review-2026-10-29-final/candidates.csv \\

&#x20; \--labels analysis/outputs/chembl-researcher-handoff-2026-10-29/reviewed_labels.csv \\

&#x20; \--output analysis/outputs/chembl-reviewed-model-run

\`\`\`



Choose a fresh output directory. Do not attach this file directly to the original

176-compound table: its PUBCHEM IDs differ from this worksheet's ChEMBL IDs, and

orphan label IDs are rejected. Combining datasets needs an explicit reviewed

identity crosswalk, deduplication and conflict handling first.



**## 10. Acceptance criteria and return package**



Return the working label CSV, evidence log, agreed policy document(s), and source

citations/access notes. Keep all original IDs, unresolved rows and adverse or

contradictory evidence. Include review status counts and the main unresolved

identity, method, origin and access issues; explain any proposed source correction.

A second reviewer should be able to reconstruct each known label from the

referenced compound, source location and stated rule without relying on memory.



Known activity labels must share one accepted policy in a training file. Keep

policy-specific datasets separate where necessary. The label importer/model rejects

conflicting known labels for identical structures; resolve those explicitly in

context instead of deleting whichever row is inconvenient. Multiple papers or

assay rows on one compound do not create independent training compounds.



For default five-fold structural validation, each class needs at least five

unique labeled compounds and five scaffold groups, and each actual train/test

partition must contain both classes. All acyclic molecules share one group.

Meeting those minimum checks is not a guarantee of useful or externally valid

performance. The current set has only 28 scaffolds in total; adding many close

analogues or repeatedly testing the same compounds does not solve this limitation.

Reserve independent publications/scaffold families for later validation rather

than repeatedly revising labels to improve the same reported score.



No target percentage of filled cells is required. The deliverable is an auditable

set of supported conclusions and explicit unknowns, suitable for deciding what

additional experiments or literature searches are needed next.



**## 11. Repository references**



\- [Independent labels and schema]\(../labels.py)

\- [Structural feature preparation and screening]\(../screen.py)

\- [Model evaluation and support rules]\(../structure_models.py)

\- [Frozen review exporter]\(../review_assays.py)

\- [Scientific policy record]\(decisions.md)

\- [Source acquisition assessment]\(compound_sources.md)

\- [Actual validation and acquisition checkpoint]\(structural_validation_check.md)

\- [Analysis commands and public contract]\(../README.md)



The exact dataset files and working pack are local artifacts outside Git. Preserve

source copies and their manifests when handing the project to another researcher;

only the guide and other maintained documentation are part of the repository.
