These fixtures are hand-authored synthetic PUG-View shapes. Names, CIDs 101–103,
URLs and toxicity values are test placeholders, not chemical evidence. Never
submit them to PubChem or cite them as measured toxicity. Test helpers seed cache
files in temporary directories; no network is needed.

Alpha: rat oral exact 1000/3000 mg/kg (median 2000), lower threshold >8000,
trout 96h interval 2–4 mg/L, unsupported numeric array and custom narrative.
Beta: rat oral exact 10000 mg/kg. Gamma: resolved identity, missing section.
Unknown: no identity. Rat group medians: herbicide 2000, natural_product 10000;
natural-product denominator 3, including Gamma and Unknown.

The `snapshot_cache` fixture seeds validated raw envelopes for Alpha, Beta, and
Gamma under pytest's temporary directory. The `curated_queries` fixture also
selects unresolved Unknown. Offline table assembly yields four compounds and
seven annotations; selecting an additional Alpha alias adds no annotation rows.

`endpoints.yaml` and `comparisons.yaml` contain synthetic matching policies. The
first selects broad fish LC50 results; the second requires rainbow trout and
96-hour exposure. Display labels and notes are illustrative, not scientific
recommendations. Neither file supplies missing context to measurement rows.
