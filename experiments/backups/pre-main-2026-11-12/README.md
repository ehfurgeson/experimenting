# Local pre-main research preservation

Research snapshot: f597eed0cb60b705f77d8fb807a0386da3649363 (includes the final
preflight provenance fix). The original ten experimental commits and prior
repository history are in repository.bundle. Later documentation records this
archive; it does not change the archived research snapshot.

research-preservation.tar.gz contains 677 workspace files plus Git bundle,
inventory and creation script. verification.json records all file hashes verified
by streaming the archive, resolving three internal hard links without extracting
over the checkout. A bare clone from the bundle passed full Git fsck and contains
the snapshot commit. This is a same-disk local preservation copy, not an off-device
backup or a publicly distributed dataset. Do not upload source PDFs/private
research notes merely because the archive exists.

The workspace files include every dated experimental root (including failed and
unfinished Daphnia work) and hash-linked dependencies from input/output/code/lock
manifests. No dependency paths are missing or outside the repository. Absolute
paths inside historical manifests remain unchanged; restoring elsewhere requires
an explicit path mapping and historical environment/version handling.

historical-supplement.tar.gz additionally preserves the exact original weekly
literature acquisition resource, its manifest and the verification/recovery tools.
The newer maintained resource is also preserved. Forty-four of45 differences
between historical manifest hashes and current files resolve to exact archived
files or code in the Git bundle. One unresolved hash belongs only to the
superseded, non-final experimental-publication-transfer-2026-11-12 run: its exact
initial publication_transfer.py bytes have not been recovered. Its output is
preserved but should not be presented as fully code-reproducible. The canonical
-final transfer run's historical source is recoverable. No frozen manifest was
rewritten to erase this gap.

Verify without changing the checkout:

    uv run --project analysis --locked --offline python experiments/backups/pre-main-2026-11-12/verify_archive.py

For recovery, verify archive SHA256 against verification.json and the supplement
against supplement-verification.json, then unpack into a NEW empty directory.
Clone repository.bundle into another new checkout and select the recorded
snapshot commit explicitly (the bundled main ref is the earlier baseline).
Copy the workspace tree into the intended recovery root. Preserve inventory and
receipt; do not extract blindly over current research or rewrite manifest paths.
The verification script independently checks archived bytes, not scientific
correctness or historical software-environment reproducibility.
