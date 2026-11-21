# Making a good incremental commit in `agrochem-toxicity`

A guide for agents (and people) making one small, reviewable change in this
repository.

**Scope.** This document covers how to turn one unit of work into one commit
that a reviewer can read in a few minutes, and the branch, safety, and
reporting rules that surround it. It does not describe the science, the data
model, or the pipeline stages themselves. For those, read
`pipeline/README.md` (the public contract), `pipeline/docs/decisions.md` (the
policy record), and `complete/PIPELINE_IMPLEMENTATION_GUIDE.md` (the plan).

**Evidence base.** Every rule below is derived from the 21 commits in this
repository's history: the 17 commits that implemented plan steps 01-17 on
2026-10-15, plus the three that preceded the plan (the initial commit, the
research-document dump, and the standalone prototype script). Measured numbers
appear in [Appendix A](#appendix-a--measured-history-of-landed-commits).

---

## 1. The one-paragraph version

Every commit in this repository does exactly one thing, at one layer, is proven
by one test file, and explains itself in one sentence. If your change needs two
sentences to describe, it is two commits.

The repository was built one behavior boundary at a time, 3 to 17 minutes apart.
The result is a history where every commit can be read on its own, where
reverting one step is a normal operation, and where the documentation that
describes a feature was written in the same breath as the feature.

New work happens on a dedicated local branch, one commit per step, and every
commit stays local until the user reviews it and approves a push. Nothing is
pushed, merged, or force-pushed without that approval.

---

## 2. Where the work comes from

### 2.1 The plan is the source of truth for the commit message

`complete/PIPELINE_IMPLEMENTATION_GUIDE.md` (gitignored) is the development
plan for rebuilding `pipeline/`. It defines 28 numbered steps in dependency
order:

```
inputs/identity -> storage -> retrieval -> flattening -> normalization
-> coverage -> analysis/audit -> workflow/report/CLI
```

Each step pre-declares the exact commit message to use:

```
### 08 - Implement the PubChem adapter

**Subject:** `feat: add PubChem source adapter`

**Body:** Resolve names and retrieve validated identity and toxicity responses.
```

**Use the declared subject and body verbatim.** This is not a suggestion; it is
the mechanism by which the plan and the history stay in sync. Every landed step
commit matches its step's declared subject and body exactly, character for
character. Do not paraphrase the body, do not add a trailer, do not append
the step number.

If the step's declared body no longer describes what you actually implemented,
that is a signal to split the step and land a smaller piece, not to rewrite the
message. Changing the plan is a separate, explicit decision.

### 2.2 Where the plan stands

| Steps | Status | Landed as |
| --- | --- | --- |
| 01 - 07 | done | `797a635` .. `8aa6c6f` |
| 08 - 17 | done | `af2e7a5` .. `d978a1a` |
| 18 - 28 | not started | - |

The next step is **18 - Consolidate matching evidence**
(`feat: consolidate comparable toxicity records`). Steps 18 and 19 are optional
in the sense that the plan allows 27 and 28 to arrive late, but 18-26 are the
core of the rebuild.

The plan is a *development plan*, not a request to implement everything at once.
Take one step. If the step is too large for one commit, take its first coherent
half and record the rest.

### 2.3 The plan's own sizing rule

The plan says, verbatim:

> Aim for one behavior boundary and one focused review session per commit,
> usually about 50-200 implementation lines plus tests. This is a sizing
> heuristic, not a quota. Split a step if it changes multiple policies or
> becomes difficult to review. ... Never enlarge a commit just to meet a line
> count.

Treat that as authoritative. Everything in section 5 is measurement of how the
repo actually applied it, not a new rule.

---

## 3. Anatomy of a commit in this repository

Every `feat:` commit in the history touches the same five kinds of file. Plan
all five before you write the first line of code.

| Part | Location | Typical size | What it does |
| --- | --- | --- | --- |
| Implementation | `pipeline/src/agrotox/*.py` | 50-300 lines | the new behavior |
| Tests | `pipeline/tests/test_<area>.py` | 90-320 lines | the proof; usually at least as long as the implementation |
| Public contract | `pipeline/README.md` | 20-60 lines | one new `##` section describing the new API |
| Policy record | `pipeline/docs/decisions.md` | 15-55 lines | one new `##` section recording the choice and its limits |
| Supporting artifacts | `pipeline/examples/`, `pipeline/tests/fixtures/`, `pipeline/docs/live_retrieval_check.md`, `pipeline/docs/walkthrough.md` | varies | runnable demo, fixture data, live-run notes |

Added only when genuinely required:

| Extra | When | Notes |
| --- | --- | --- |
| `pipeline/pyproject.toml` + `pipeline/uv.lock` | a new runtime or dev dependency | commit `24bb70d` added PyYAML this way; regenerate the lock with `uv lock` and commit both files together |
| A new module file | a new stage or a new concern | `identity.py`, `units.py`, `coverage.py`, `_context.py` |
| A new test file | a new area of behavior | `tests/test_<area>.py`, named after the behavior, not the module |
| A new fixture | a new data shape | `tests/fixtures/*.json`, `*.yaml` with a note in `tests/fixtures/README.md` |

**The documentation is part of the commit, not a follow-up.** The plan says:
"Record significant policy choices, not a diary of every edit." A feature
commit that ships code without updating `README.md` and `docs/decisions.md`
leaves the repository in a worse state than before it started, because the next
agent cannot tell what the code is supposed to guarantee.

**Documentation-only changes are still commits.** Commit `aa987d5` is a
`chore:` commit that changed `.gitignore` and trimmed the prototype script. It
is a valid commit. It is also an example of a subject that does not describe
the diff (see section 6.4).

---

## 4. Choosing the boundary: one behavior boundary

A **behavior boundary** is one rule that (a) a reviewer can restate in one
sentence, and (b) one test file can prove.

Ask this question before writing code:

> Reading only the diff, can a reviewer answer "what is now true that was not
> true before?" in a single sentence without using the word "and"?

If not, split.

### 4.1 Split signals

Split the work when any of these is true:

- The change establishes two independent policies (for example: "how to
  canonicalize a query" and "how to merge two curated records" - these were
  steps 02 and 03, two commits, 3 minutes apart).
- The change adds two public entry points.
- The change adds a new dependency *and* a new behavior (land the dependency
  alone, or fold it in only if it is trivially small and the step needs it).
- The change adds a new behavior *and* a new output file format.
- The change is a refactor plus a behavior change. Land the refactor first, on
  its own, or leave it out. This repository has no formatting-only or
  rename-only commits in the feature series; keep it that way.
- The implementation would exceed roughly 300 lines.
- The diff would touch more than roughly 12 files.
- You cannot write the test file name without a conjunction.

### 4.2 Do not split when

- The test cannot exist without the implementation. Tests and implementation
  ship together, always.
- The README section cannot be written without the behavior existing.
- The decision record cannot be written without the policy existing.
- A live/manual check depends on the code being present (that check goes in
  the same commit, per the plan's "Live checkpoint" notes).

### 4.3 A worked example

Step 15 ("Interpret annotation context") is the largest landed commit
(`f73d416`, 300 implementation lines, 323 test lines, 10 files). It was
acceptable because it was a single behavior - "extract supported endpoints and
explicit exposure context while retaining review rows" - even though it added a
new module (`_context.py`), a new contract, and a table integration. Compare
with the plan's advice to split "numeric parsing or retry handling" if it
becomes hard to review.

---

## 5. Size: what "good size" means here

### 5.1 Measured from the 17 landed feature steps

| Measure | Median | Range |
| --- | ---: | ---: |
| Implementation lines (`pipeline/src/`) | 98 | 51 - 300 |
| Test lines (`pipeline/tests/`) | 175 | 86 - 323 |
| Documentation/config lines | 76 | 28 - 330 |
| Files touched | 6 | 3 - 12 |
| Total diff | ~380 | 162 - 801 |

The plan's heuristic of "about 50-200 implementation lines plus tests" matches
the measured median well.

### 5.2 How to apply the numbers

- **50-200 implementation lines** is the target band. Below 50 is usually fine
  but check that the commit is not a trivial fragment that should have been
  folded into a neighbor.
- **Tests should be at least as many lines as the implementation.** Every
  landed feature commit satisfies this. Tests are the deliverable; the
  implementation is the shorter half.
- **A 600-line commit that is one behavior is good. A 200-line commit that is
  two behaviors is bad.** Size is a proxy for reviewability, not the goal.
- **Never inflate** a commit to reach a line count. Never delete a test to
  shrink one. Never defer a test to a later commit to keep a diff small.
- **The whole diff should be skimmable in one sitting.** If a reviewer would
  need to open four files to check one claim, the commit is too wide.

### 5.3 When a step is genuinely too big

Do this instead of one enormous commit:

1. Land the first coherent behavior with its test, README section, and decision
   record.
2. Leave the rest for the next commit, whose subject is a *new* behavior
   statement, not a continuation ("also ...").
3. If the plan's step is one indivisible behavior that happens to be large, land
   it large and say so in the body. That is an accepted exception, not a
   default.

---

## 6. The commit message

### 6.1 Format

```
<prefix>: <subject>

<one-sentence body>
```

| Element | Rule | Examples from the history |
| --- | --- | --- |
| Prefix | one of `feat:`, `chore:`, `docs:` | `feat: validate endpoint matching rules` |
| Subject | lowercase, imperative, no trailing period, at most ~60 characters, names the *capability* | `feat: write atomic raw snapshots` |
| Body | exactly one sentence, present tense, states the guarantee, ends with a period | `Preserve raw JSON with atomic replacement and explicit storage paths.` |
| Trailer | none | - |

The `docs:` prefix is reserved for the plan's step 26 (final documentation
sweep). Do not use it for ordinary doc updates that accompany a feature.

### 6.2 The body is a claim, not a summary

The body should be checkable against the diff. Compare:

| Weak | Strong |
| --- | --- |
| "Updated storage handling" | "Preserve raw JSON with atomic replacement and explicit storage paths." |
| "Refactored the pubchem client" | "Bound transient retries and honor Retry-After using injectable clocks." |
| "Added tests and docs" | "Distinguish complete, missing, pending, and corrupt cached records." |
| "Fixed a bug in coverage counting" | "Count distinct compounds while preserving unresolved and zero-data denominators." |

The strong column is what every landed commit does: it states what the code now
guarantees, in the vocabulary of the domain, without naming a file, a function,
a class, or a test.

### 6.3 What the body must not contain

- The list of files changed.
- "Refactor", "update", "improve", "fix", "misc", "WIP", "address review
  comments".
- "As requested", "per the plan", "step 08", "as discussed".
- A second sentence. One behavior, one sentence.
- Anything the diff does not support.

### 6.4 The one bad message in this history

`aa987d5 chore: small change to documentation` actually deleted 22 lines from
`prototype/pubchem_toxicity.py` and changed `.gitignore`. The subject described
an effect that the diff did not have.

Use this as the counter-example. If your subject line cannot be verified
against the diff by reading the diff, rewrite the subject. The `chore:` prefix
does not exempt a commit from having an accurate subject.

### 6.5 Subjects for `chore:` commits

The two landed `chore:` commits have no body. That is fine when the change is
genuinely small and self-evident. If a `chore:` commit changes behavior,
give it a body that states the behavior, exactly as a `feat:` commit would.

---

## 7. The build loop

The plan prescribes this loop; follow it in order.

### 7.1 Before writing code

1. Re-read the plan step. Extract its `Subject`, `Body`, `Test first`, `Build`,
   `Done`, `Read`, and any `Verify` / `Demonstrate` / `Live checkpoint`
   subsection.
2. Write the expected end state in one sentence. If you cannot, the step is
   still too big; find the first sentence you *can* write.
3. Decide the boundary: which files will this commit touch? Write the list
   down. If the list contains a file that does not serve the behavior, remove it.
4. Decide the test file name. Usually `tests/test_<area>.py`, created new or
   extended. Extend an existing file when the behavior belongs to an area that
   already has one.

### 7.2 Red

5. Write the smallest test that demonstrates the behavior.
6. Run it. **Confirm it fails for the intended reason.** An import error, a
   typo, or a missing fixture is not a red test. This is the step most often
   skipped, and it is the step that makes the green meaningful.
7. The test must exercise the public contract, not a private helper name, a
   regex spelling, or a particular aggregation expression.

### 7.3 Green

8. Implement enough to pass. Not the whole step if the step is large - enough
   for this commit's boundary.
9. Add closely related edge cases. Prefer parameterized cases over a long list
   of near-duplicate test functions.
10. Add a case for each distinct contract or known failure. Do not add cases to
    reach a count.

### 7.4 Refactor

11. Refactor while green. Keep the refactor inside the same behavior boundary,
    or leave it for a separate commit later.
12. Do not reformat files you did not otherwise touch. Do not rename public
    names. Do not "clean up" nearby code.

### 7.5 Document

13. Add the `README.md` section: heading is a noun phrase naming the
    capability, body states the contract concretely, ends with the focused
    test command.
14. Add the `docs/decisions.md` section: heading is a noun phrase, body states
    the policy and then its limits, and includes a table when the behavior is a
    state machine.

### 7.6 Verify

15. Run the focused test file, then the whole suite, then lint. See
    section 10.

### 7.7 Commit

16. Stage only this step's files, by explicit path. `git add -A` and
    `git add .` are forbidden, because they will sweep in the user's
    pre-existing modifications. `git diff --staged --stat` must show the file
    list you wrote down in 7.1. Anything extra is a mistake.
17. Read the staged diff once, in full.
18. Commit with the plan's declared subject and body. The commit lands on your
    branch, locally.
19. Move to the next slice.

---

## 8. Change-type checklists

### 8.1 New stage or new module

- [ ] New module in `pipeline/src/agrotox/` with a single responsibility.
- [ ] New or extended `tests/test_<area>.py`.
- [ ] New `README.md` `##` section.
- [ ] New `docs/decisions.md` `##` section.
- [ ] If the stage produces a new artifact, add it to the plan's output
      compatibility checklist section in `docs/decisions.md` or the README
      project layout list.
- [ ] If the stage is a new pipeline stage, make the runnable example reach it.

### 8.2 New policy or new validation

- [ ] Tests cover the accept case and at least one reject case, including the
      error type and the error message content.
- [ ] `docs/decisions.md` section states the policy **and** what it does not
      guarantee.
- [ ] README section states the failure mode, not just the success path.

### 8.3 New dependency

- [ ] Add to `pipeline/pyproject.toml` under `dependencies` or
      `[dependency-groups].dev`.
- [ ] Regenerate the lock: `uv lock` from `pipeline/`.
- [ ] Commit `pyproject.toml` and `uv.lock` together with the code that needs
      it.
- [ ] Never hand-edit `uv.lock`. Never let the lockfile churn because a
      formatter changed a hash.
- [ ] Confirm the dependency is actually imported by committed code.

### 8.4 New output file or format

- [ ] The name matches the plan's output compatibility checklist.
- [ ] The README documents the name and the location.
- [ ] A test asserts the file exists and its content is semantically right -
      not that the file byte-matches a fixture.
- [ ] Generated artifacts (`.live-smoke/`, caches) stay uncommitted. Check
      `pipeline/.gitignore`.

### 8.5 New configuration file

- [ ] The config is validated by code with a test, not only parsed.
- [ ] Unknown fields are rejected or explicitly preserved - never silently
      dropped.
- [ ] A small synthetic config lives in `tests/fixtures/`.
- [ ] The example config in `pipeline/examples/` is realistic but does not
      hard-code provider responses.

### 8.6 Bug fix

- [ ] A test fails before the fix, for the intended reason.
- [ ] The fix is minimal and does not change neighboring behavior.
- [ ] If the fix changes a documented contract, the README and decision
      sections are updated in the same commit.
- [ ] The subject states the corrected behavior, not "fix bug in X".

### 8.7 Documentation only

- [ ] Subject names the documentation, and matches the diff.
- [ ] No code changes. If code changed, it is not a documentation-only commit.
- [ ] Links resolve; commands were run.

### 8.8 Refactor only

- [ ] Behavior is provably unchanged; the existing suite passes unchanged.
- [ ] No public name changed without a decision record.
- [ ] Prefer not to make this commit at all, unless it unblocks a behavior
      commit that follows immediately.

---

## 9. Writing the two documentation sections

### 9.1 `pipeline/README.md` - the public contract

Style observed in every landed commit:

- Heading is a noun phrase naming the capability: `## Cache validation`,
  `## Raw JSON storage`, `## Endpoint definitions and matching`.
- The first paragraph names the exact public function or type and states what
  it does, in the present tense.
- Subsequent paragraphs give the concrete rules: accepted inputs, exact
  outputs, the error types raised, and the precise cases that are handled
  differently.
- The section states what the guarantee does *not* cover, when that matters.
- The section ends with the command to run the focused checks:
  `Run the focused checks with `uv run pytest tests/test_storage.py -q`.`

The README is written for a user of the package, not for a reviewer of the
diff. Do not mention commit numbers, plan steps, or what changed relative to a
previous version.

### 9.2 `pipeline/docs/decisions.md` - the policy record

Style observed in every landed commit:

- Heading is a noun phrase: `## Cache state and recovery`,
  `## Compound coverage denominators`.
- First paragraph states the policy plainly, often in the negative: "It does
  not infer synonyms.", "No alias is chosen as authoritative based on traversal
  order."
- The limits of the guarantee are stated explicitly: "Atomic replacement
  protects one file from partial writes. It does not make a
  properties/toxicity/metadata bundle transactional or serialize concurrent
  writers."
- State machines are documented as a Markdown table with columns like
  `Saved state | Reader behavior | Complete? | Recovery`.
- Where a choice differs from the reference implementation in `complete/`, the
  difference and its reason are recorded. The plan requires this:
  "Other deliberate differences from the reference should be captured in
  `docs/decisions.md` as they are introduced."

Do not turn this file into a changelog. It records *why the current behavior is
what it is*, not what changed when.

### 9.3 The other docs

- `pipeline/docs/live_retrieval_check.md` - observations from a manual live
  PubChem run. Written as evidence to review, never as permanent test
  expectations. Extended in the same commit as the behavior that made the check
  possible (steps 10, 11, 12, 15).
- `pipeline/docs/walkthrough.md` - the runnable narrative for a human. Extended
  when a new stage becomes demonstrable.
- `pipeline/docs/candidate_review.md` - the scientific review of a real
  snapshot. Separate from implementation.

---

## 10. Verification

Run from `pipeline/`, using the project's own environment. Never install
packages into the agent kernel to make a project import work.

```bash
cd pipeline
uv sync --locked
uv run pytest tests/test_<area>.py -q   # the focused file for this step
uv run pytest -q                         # the accumulated suite
uv run ruff check .
```

Notes that matter in this repository:

- **`ruff format` is deliberately disabled for Python.** `pyproject.toml`
  excludes `*.py` from `[tool.ruff.format]` because the project uses one space
  on each side of `=` (including keyword arguments and parameter defaults) and
  Ruff's formatter cannot preserve that. `uv run ruff format --check .` is
  therefore a no-op for the project's own code. Do not enable it, and do not
  run a Python formatter over the tree.
- **If the default uv cache is unavailable**, prefix each command with
  `UV_CACHE_DIR=.uv-cache`. That cache lives inside `pipeline/` and is
  gitignored.
- **Tests must never touch the network.** `tests/conftest.py` installs an
  autouse Requests blocker. If a new test needs HTTP, inject a fake source or
  a fake HTTP object.
- **A live PubChem run is a manual check**, never a pytest fixture, and never
  a source of hard-coded expected values.
- **A present, zero-row typed table is valid.** Missing required files raise.
  Do not "fix" a failing test by making a missing file look empty.

---

## 11. Anti-patterns

Each of these has been anticipated by the plan, and each has a real cost in
this repository.

**Manufacturing green.**

- Adding `xfail`, `skip`, or a loosened assertion so a test passes.
- Copying every failing course test or stub into the active package up front.
- Porting `test_setup.py` verbatim - it checks course-specific files and
  signatures, and should be replaced with a small package-install/import check.
- Deleting or skipping a test that is inconvenient.

**Scope creep.**

- "While I was here" refactors, renames, or formatting of untouched files.
- Two policies in one commit.
- Fixing an unrelated bug in the same commit.
- A documentation-only sweep riding along with a feature commit.

**Sizing.**

- Padding a commit to look substantial.
- Splitting a behavior into pieces that individually prove nothing.
- A commit that touches 20 files because it "needed to".

**Testing.**

- Tests that assert private helper names, regex spelling, or a particular
  aggregation expression.
- Tests that merely restate the contents of a configuration file.
- Re-running the parser's full numeric matrix through the workflow and the CLI.
- Pixel snapshots or cosmetic assertions.
- Parameterized cases added to hit a count rather than to cover a distinct
  contract.

**Evidence.**

- Committing generated data, `.live-smoke/` output, or caches.
- Hard-coding live provider responses as permanent test expectations.
- Committing secrets, tokens, or `.env` files.

**Process.**

- Committing without running the focused test and seeing it fail first.
- Committing without running the whole suite.
- Amending or squashing a landed commit to tidy it up. The history is the
  deliverable; leave it append-only.
- Editing the plan's declared subject/body to match what you happened to
  implement.

---

## 12. Git workflow: branches, commits, and safety

### 12.1 Work on a dedicated branch, never on `main`

`main` is the shared, published line. In this repository it tracks
`origin/main`. Every change belongs on a branch, and that branch stays local
until the user reviews it.

```bash
git switch main
git switch -c feat/<short-slug>
```

- One branch per logical unit of work. Usually one plan step, or a small group
  of steps that only make sense together.
- Name the branch after what it delivers, not after the person or the
  session: `feat/consolidate-matching-evidence`, `fix/pending-metadata-order`,
  `docs/curated-input-reference`.
- Never commit directly to `main`.
- Record the base commit before you start: `git log --oneline -1`. The full
  change you deliver is then `git diff main...HEAD`.

All 21 existing commits in this repository are on `main`. That was the practice
before this workflow was adopted; it is not a precedent to continue. New work
goes on a branch.

### 12.2 Uncommitted work that is not yours

Check `git status` before branching. Uncommitted changes follow you onto the
new branch, and they belong to the user, not to the plan.

As of 2026-10-21, `main` carries three pre-existing modified files:
`.gitignore`, `pipeline/docs/candidate_review.md`, and
`pipeline/docs/walkthrough.md`. They are not part of any plan step.

Rules:

- Never sweep unrelated modifications into a commit. Stage by path. `git add -A`
  and `git add .` are forbidden.
- Never discard them. `git checkout -- .`, `git restore .`, `git reset --hard`,
  and `git clean -fd` are forbidden.
- If a pre-existing change genuinely has to land with your work, say so
  explicitly in the commit body and in the final report.
- If they block you, ask rather than guess.

### 12.3 The step loop

For each logical step:

1. Implement the functionality for that step, and nothing else.
2. Add or update the relevant tests.
3. Run the focused test file, then the full suite, and record the results.
4. Review the diff: `git status --short`, `git diff`, and
   `git diff --staged --stat`. Confirm no unrelated change is included.
5. Create one local commit containing only that step's changes.

The repository must be green at every commit boundary. A commit whose suite
fails is a checkpoint you cannot return to, so fix it before committing rather
than after.

Multiple commits may touch the same files. That is expected: the sequence of
commits is the record of how the behavior was built, and each commit is
internally consistent on its own. Commit logical milestones, not groups of
files.

### 12.4 Commit subject: Conventional Commits

The subject is `type: subject`, where type is one of:

| Type | Use for |
| --- | --- |
| `feat` | a new capability |
| `fix` | a defect fix |
| `refactor` | behavior-preserving restructuring |
| `test` | tests only |
| `docs` | documentation only |
| `chore` | tooling, config, dependencies, housekeeping |
| `build`, `ci`, `perf` | build pipeline, automation, performance |

This repository's plan uses `feat:`, `chore:`, and `docs:`. Use `fix:` for a
defect fix. Use `test:` or `refactor:` only when the change is a
self-contained logical unit worth its own commit.

Subject rules: lowercase, imperative, no trailing period, at most about 60
characters, and it names the capability rather than the mechanism. See
section 6.

### 12.5 Commit body

Every commit gets a body that explains what changed and why.

- For a plan step, use the plan's declared body verbatim (section 2.1).
- Otherwise write one or two sentences: the behavior that changed, and the
  reason. A body that only restates the subject adds nothing.

```
fix: publish pending metadata before refreshing properties

Readers cannot distinguish a mixed-generation bundle from a complete one
when properties are replaced while terminal metadata is still in place.
```

### 12.6 Git safety rules

**Never, without explicit approval from the user:**

- push to any remote;
- merge a branch;
- force-push;
- discard or overwrite existing uncommitted changes;
- rewrite commits that existed before the task. No rebase, amend,
  filter-branch, or `reset --hard` on pre-existing history.

**Also never:**

- include secrets, tokens, `.env` files, or generated credentials;
- include generated data, caches, or unrelated refactors;
- commit a failing suite to get it out of the way;
- use `git add -A`, `git add .`, or `git commit -a`. Always name paths.

Leave every commit local. The user will review, modify, squash, reorder, or
remove them before anything reaches GitHub.

### 12.7 Recovering from a mistake

Only ever for commits made during the current task.

| Mistake | Recovery |
| --- | --- |
| Wrong file staged | `git restore --staged <path>` |
| Commit contains unrelated files | `git reset --soft HEAD~1`, then `git restore --staged <unrelated paths>`, then commit again |
| Commit message typo | `git commit --amend` (only for commits made in this task) |
| Work must be parked temporarily | `git stash push -- <paths>`, then `git stash pop` later. Never stash blindly over the user's changes |

Never use `git reset --hard`. It destroys work that cannot be recovered.

---

## 13. Final deliverable report

When the work is complete, hand back a report with these five parts.

1. **A numbered summary of each commit**, with its short hash and subject.

   ```
   1. a1b2c3d feat: consolidate comparable toxicity records
   2. e4f5g6h feat: summarize exact values by compound and group
   ```

2. **The files modified by each commit.** Use
   `git log --name-only --format='%h %s' main..HEAD` or
   `git show --stat <sha>`.

3. **The purpose of each change.** One or two sentences per commit: what
   behavior it adds, and why it was separated from its neighbors.

4. **The tests run and their results.** The commands and the outcome.

   ```
   uv run pytest tests/test_comparisons.py -q   -> 18 passed
   uv run pytest -q                              -> 96 passed
   uv run ruff check .                           -> clean
   ```

5. **Unresolved issues and follow-up work.** Anything not done, anything
   deferred, anything that needs a decision from the user. State it plainly
   rather than leaving it implied by a missing commit.

Also state the branch name, the base commit, and confirm explicitly that
nothing was pushed, no branch was merged, no pre-existing commit was rewritten,
and no pre-existing uncommitted change was modified or discarded.

---

## 14. Pre-commit checklist

Run through this before every commit.

**Branch and safety**

- [ ] I am on a feature branch, not `main`.
- [ ] The branch is local; nothing has been pushed.
- [ ] I staged by explicit path, not with `git add -A` / `git add .`.
- [ ] No pre-existing uncommitted change is included or discarded.
- [ ] No secrets, generated data, or unrelated edits are staged.

**Boundary**

- [ ] This commit does exactly one thing, statable in one sentence.
- [ ] The subject and body come from the plan step, verbatim.
- [ ] The subject is verifiable against the diff.
- [ ] The file list matches what I planned, with nothing extra.

**Tests**

- [ ] I watched the new test fail first, for the intended reason.
- [ ] The focused test file passes.
- [ ] The full suite passes.
- [ ] The test exercises the public contract.
- [ ] Edge cases are parameterized where they share a contract.
- [ ] No `skip`, `xfail`, or loosened assertion was added to get green.

**Code**

- [ ] `uv run ruff check .` is clean.
- [ ] No file was reformatted or renamed that I did not otherwise need to touch.
- [ ] No new dependency was added unless the step required one, and if so
      `pyproject.toml` and `uv.lock` are both committed.
- [ ] Errors are explicit and typed; nothing is silently dropped or coerced.

**Documentation**

- [ ] `pipeline/README.md` has a new `##` section for this behavior.
- [ ] `pipeline/docs/decisions.md` has a new `##` section stating the policy
      and its limits.
- [ ] Any deliberate difference from the reference in `complete/` is recorded.
- [ ] Any new artifact or output filename is documented.

**Hygiene**

- [ ] No generated data, caches, `.live-smoke/`, or secrets are staged.
- [ ] No changes to `complete/`, `reconstruction/`, or `notes/` (all
      gitignored).
- [ ] I read the staged diff in full.

---

## 15. Templates

### 15.1 Commit message

```
feat: <capability in lowercase, imperative, <= 60 chars>

<One sentence stating the guarantee the code now provides.>
```

```
chore: <what changed, accurately>

<Optional body, only if behavior changed.>
```

### 15.2 Step worksheet (fill this in before coding)

```
Plan step:      NN - <title>
Subject:        feat: ...
Body:           ...

Behavior boundary (one sentence):
  <...>

Done when (observable):
  <...>

Files this commit will touch:
  - pipeline/src/agrotox/<module>.py     (new or extended)
  - pipeline/tests/test_<area>.py        (new or extended)
  - pipeline/README.md                   (new ## section)
  - pipeline/docs/decisions.md           (new ## section)
  - ...

Focused test command:
  uv run pytest tests/test_<area>.py -q

Split plan if the step is larger than one commit:
  <...>
```

### 15.3 New decision record section

```markdown
## <Noun phrase naming the policy>

<The rule, stated plainly. Say what it does not do.>

<Table of states, if the behavior is a state machine.>
```

### 15.4 Branch setup

```bash
git switch main
git status --short              # note anything already modified
git log --oneline -1            # record the base commit
git switch -c feat/<short-slug>
```

### 15.5 Final report template

```
Branch:  feat/<short-slug>
Base:    <short hash> (<subject>)
Status:  local only, not pushed, not merged

Commits
1. <short hash> <subject>
   - <file> - <file>
   Purpose: <what behavior this adds and why it is separate>
2. ...

Tests run
  uv run pytest tests/test_<area>.py -q   -> <result>
  uv run pytest -q                        -> <result>
  uv run ruff check .                    -> <result>

Unresolved / follow-up
  - <item>
  - none
```

---

## Appendix A - Measured history of landed commits

`feat:` commits only, from `pipeline/`'s rebuild (guide steps 01-17). `src` is
changed lines under `pipeline/src/`, `test` under `pipeline/tests/`, `doc` is
Markdown, TOML, lock, YAML, CSV and TXT changes, `other` is everything else.

| sha | subject | files | src | test | doc | other |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `8096f2b` | feat: canonicalize chemical queries | 4 | 51 | 86 | 28 | 0 |
| `010e074` | feat: load curated chemical inputs | 3 | 93 | 138 | 42 | 0 |
| `4029e27` | feat: reconcile compound identities | 6 | 183 | 204 | 84 | 0 |
| `d196852` | feat: write atomic raw snapshots | 4 | 53 | 121 | 47 | 0 |
| `8585a79` | feat: validate PubChem cache state | 4 | 106 | 178 | 66 | 0 |
| `8aa6c6f` | feat: persist typed tables with provenance | 5 | 71 | 146 | 70 | 0 |
| `af2e7a5` | feat: add PubChem source adapter | 8 | 168 | 198 | 65 | 0 |
| `45ef1a5` | feat: pace and retry PubChem requests | 4 | 82 | 211 | 79 | 0 |
| `ab8c8ac` | feat: resume PubChem retrieval safely | 8 | 146 | 259 | 121 | 1 |
| `236ac24` | feat: flatten PubChem toxicity annotations | 7 | 179 | 173 | 79 | 0 |
| `f162a14` | feat: build compound and annotation tables | 9 | 78 | 209 | 91 | 41 |
| `d0e9434` | feat: normalize toxicity units and durations | 4 | 68 | 87 | 62 | 0 |
| `bf619d5` | feat: parse toxicity values conservatively | 5 | 104 | 96 | 73 | 0 |
| `f73d416` | feat: normalize toxicity annotation context | 10 | 300 | 323 | 153 | 38 |
| `24bb70d` | feat: validate endpoint matching rules | 10 | 155 | 217 | 110 | 0 |
| `d978a1a` | feat: report compound endpoint coverage | 12 | 59 | 140 | 330 | 72 |

The remaining commits, for contrast. Note that step 01 declares a `chore:`
subject, so it appears here rather than in the table above, and that the
prototype predates the plan:

| sha | subject | shape |
| --- | --- | --- |
| `4066e58` | Initial commit | 2 files, 4 lines |
| `84b5162` | chore: added background documents for research | research data dump, no code |
| `7b14185` | feat: add PubChem toxicity retrieval prototype | pre-package prototype, 599-line script, before the plan |
| `797a635` | chore: scaffold pipeline package (step 01) | tooling scaffold: 11 files, 3 src lines, 198 test lines |
| `aa987d5` | chore: small change to documentation | 2 files, 4 insertions, 23 deletions |

**Cadence.** The 10 feature commits from `af2e7a5` to `d978a1a` landed over
80 minutes on 2026-10-15, between 3 and 17 minutes apart. This is the tempo of
a red/green/refactor loop run continuously, committing at each green. It is
the clearest signal of the intended working style.

## Appendix B - Plan step to commit map

Every step in `complete/PIPELINE_IMPLEMENTATION_GUIDE.md` declares its own
subject and body. The landed commits reproduce them exactly.

| Step | Declared subject | Landed as |
| --- | --- | --- |
| 01 | `chore: scaffold pipeline package` | `797a635` |
| 02 | `feat: canonicalize chemical queries` | `8096f2b` |
| 03 | `feat: load curated chemical inputs` | `010e074` |
| 04 | `feat: reconcile compound identities` | `4029e27` |
| 05 | `feat: write atomic raw snapshots` | `d196852` |
| 06 | `feat: validate PubChem cache state` | `8585a79` |
| 07 | `feat: persist typed tables with provenance` | `8aa6c6f` |
| 08 | `feat: add PubChem source adapter` | `af2e7a5` |
| 09 | `feat: pace and retry PubChem requests` | `45ef1a5` |
| 10 | `feat: resume PubChem retrieval safely` | `ab8c8ac` |
| 11 | `feat: flatten PubChem toxicity annotations` | `236ac24` |
| 12 | `feat: build compound and annotation tables` | `f162a14` |
| 13 | `feat: normalize toxicity units and durations` | `d0e9434` |
| 14 | `feat: parse toxicity values conservatively` | `bf619d5` |
| 15 | `feat: normalize toxicity annotation context` | `f73d416` |
| 16 | `feat: validate endpoint matching rules` | `24bb70d` |
| 17 | `feat: report compound endpoint coverage` | `d978a1a` |
| 18 | `feat: consolidate comparable toxicity records` | next |
| 19 | `feat: summarize exact values by compound and group` | - |
| 20 | `feat: audit extraction and review gaps` | - |
| 21 | `feat: compose reproducible offline analysis` | - |
| 22 | `feat: export traceable toxicity reports` | - |
| 23 | `feat: visualize coverage and toxicity uncertainty` | - |
| 24 | `feat: expose offline pipeline commands` | - |
| 25 | `feat: run the pipeline with resumable fetching` | - |
| 26 | `docs: document curated inputs and pipeline behavior` | - |
| 27 | `feat: add read-only exploration notebook` | optional parity |
| 28 | `chore: package pipeline execution` | optional parity |

## Appendix C - Naming conventions

| Thing | Convention | Example |
| --- | --- | --- |
| Package module | one responsibility, lowercase, no underscores unless private | `identity.py`, `coverage.py` |
| Private module | leading underscore | `_context.py` |
| Subpackage | plural noun | `parsers/`, `sources/` |
| Test file | `test_<area>.py`, named for the behavior | `tests/test_matching.py` |
| Test function | `test_<observable behavior>` | `test_aliases_merge_without_losing_unresolved` |
| README section | noun phrase | `## Compound endpoint coverage` |
| Decision section | noun phrase | `## Cache state and recovery` |
| Data artifact | reference names, with `.metadata.json` sidecars | `compounds.parquet` |

## Appendix D - Where scratch work goes

The repository root `.gitignore` excludes `notes/`, `complete/`,
`reconstruction/`, `results/`, and `todo.md`.

- `notes/` - agent scratch notes, plans, and this guide. Nothing here is
  committed.
- `complete/` - the reference implementation being rebuilt. Read-only
  reference.
- `reconstruction/` - the teaching package with contracts and milestone tests.
  Read-only reference.
- `pipeline/.live-smoke/` - live PubChem caches and local outputs. Never
  committed.

If you write a plan, a worksheet, an investigation log, or a guide, put it in
`notes/`. Do not commit it, and do not add it to `.gitignore` again - the rule
already exists.

## Appendix E - Quick reference card

```
BRANCH
  git switch main
  git status --short          # note the user's uncommitted changes
  git log --oneline -1        # record the base commit
  git switch -c feat/<slug>   # never work on main

BEFORE
  Read the plan step. Take its Subject and Body verbatim.
  Write one sentence: what is now true that was not true before?
  If it needs "and", split.
  Write the file list.

RED
  Smallest test that proves it. Run it. Confirm it fails for the
  intended reason.

GREEN
  Implement enough. Add parameterized edge cases.

REFACTOR
  Only inside the boundary. No reformatting of untouched files.

DOCUMENT
  README.md      -> one new ## section: the public contract
  decisions.md   -> one new ## section: the policy and its limits

VERIFY
  uv run pytest tests/test_<area>.py -q
  uv run pytest -q
  uv run ruff check .

COMMIT
  git add <only this step's files>   # by path, never -A or .
  git diff --staged --stat           # must match the planned list
  git commit  (plan's subject + plan's body)

REPORT
  1. numbered commits: short hash + subject
  2. files modified per commit
  3. purpose of each change
  4. tests run and results
  5. unresolved issues / follow-up
  + branch, base commit, and confirmation that nothing was pushed or merged

NEVER
  xfail/skip to get green      two behaviors in one commit
  reformat untouched files     live network in a test
  commit generated data        hard-code provider responses
  edit the plan's message      amend a landed commit

NEVER, WITHOUT EXPLICIT APPROVAL
  push to any remote            merge a branch
  force-push                    rewrite pre-existing commits
  discard the user's uncommitted changes
```
