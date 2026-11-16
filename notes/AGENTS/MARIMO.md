# Marimo notebook authoring

Write notebooks as readable documents: give them a clear title, a short purpose,
and focused sections that explain the question, show the result, and state its
limits. Prefer a single-column reading order, consistent headings, short paragraphs,
clearly labeled controls, and tables/charts with units and meaningful captions.
Keep setup details out of the main narrative. Preserve data provenance and
separate synthetic demonstrations from scientific findings.

## Dedicated native Markdown cells

Follow [marimo_markdown_example.py](../notebooks/marimo_markdown_example.py).
Keep notebooks in the usual `.py` format. In the marimo editor, create a cell
with the **Markdown** button or select Markdown through the cell action menu.
Write and edit narrative in that cell's Markdown editor.

All Markdown belongs in dedicated Markdown cells, fully separate from Python
computation cells. Do not mix narrative rendering with imports, assignments,
calculations, controls, charts, or table construction in the same cell. Do not
embed narrative `mo.md(...)` calls inside Python layouts or helper functions.

Marimo serializes native Markdown cells as Python using `mo.md(...)`. That
underlying representation is expected; the rule concerns cell separation and
the editor experience, not a ban on the serialized function call. Import
`marimo as mo` in a separate setup cell. When authoring the file directly, use
a standalone `@app.cell(hide_code=True)` whose only display expression is
`mo.md(...)`, followed by `return`, matching the supplied example:

```python
@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A clear research question

    Explain the question using **Markdown**.
    """)
    return
```

Put each control, calculation, chart, or table in an appropriate Python cell.
Introduce results in a preceding Markdown cell and interpret them in a following
Markdown cell. Keep one main idea per narrative cell. Hiding a mixed Python cell
alone does not make it a native Markdown cell. Do not require `.md` notebooks
or convert existing notebooks to that format for this convention.

## Review and verify

The [comparison notebook](../notebooks/markdown_cells_demo.py) shows the dedicated
Markdown pattern, an illustrative mixed-cell pattern to avoid, and a reactive
Python result between narrative cells. From the repository root:

```bash
uv run --project analysis --locked marimo edit notes/notebooks/markdown_cells_demo.py
uv run --project analysis --locked marimo check --strict notes/notebooks/markdown_cells_demo.py
uv run --project analysis --locked marimo export html notes/notebooks/markdown_cells_demo.py -o notes/notebooks/markdown_cells_demo.html --force
```

Verify cell structure and execute/export the notebook. In the live editor,
confirm narrative cells use the Markdown editor and code cells contain the
computation. HTML is a static snapshot; Python-backed interaction requires the
live notebook. All files under `notes/` remain local under the
[notes Git rule](README.md#before-finishing).
