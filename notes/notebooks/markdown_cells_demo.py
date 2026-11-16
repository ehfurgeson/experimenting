import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Dedicated Markdown cells

    This notebook follows `marimo_markdown_example.py`: narrative lives in native
    **Markdown cells**, and computation lives in separate **Python cells**.
    Open it in **edit** mode to review the cell types and authoring experience.

    ## 1. The intended pattern

    This entire cell is Markdown. Create one with the **Markdown** button or
    the cell action menu, then type Markdown directly into its editor.

    Marimo saves it in the `.py` source as a standalone `mo.md(...)` expression
    inside `@app.cell(hide_code=True)`. That serialization is expected.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. Compare the cell boundaries

    **Avoid mixing computation and narrative in a Python cell.** This is an
    illustrative code sample only; it does not execute:

    ```python
    observed = 12
    total = 20
    mo.md(f"Coverage: {100 * observed / total:.0f}%")
    ```

    **Preferred:** use a Markdown cell to introduce the result, a Python cell
    to compute/display it, and another Markdown cell to explain it. The next
    three cells demonstrate this separation.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3. A small reactive example

    Choose how many of **20 synthetic records** have an observation. The control
    and result are Python outputs in the next cell; this explanation stays in
    its own Markdown cell. No research files are read or changed.
    """)
    return


@app.cell
def _(mo):
    observed_records = mo.ui.slider(
        start=0, stop=20, value=12, step=1,
        label="Records with an observation (out of 20)", show_value=True,
    )
    observed_records
    return (observed_records,)


@app.cell
def _(mo, observed_records):
    mo.ui.table(
        [{
            "Records with observation": observed_records.value,
            "Total records": 20,
            "Coverage (%)": round(100 * observed_records.value / 20, 1),
        }],
        selection=None,
        pagination=False,
        label="Synthetic evidence coverage",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ### Interpretation

    At the default setting, 12 of 20 records gives **60% coverage**. Moving the
    slider to 0 or 20 gives 0% or 100%. Coverage describes evidence availability;
    these synthetic values make no claim about toxicity or safety.

    ## Review checklist

    1. Confirm narrative cells open in the Markdown editor, like the supplied example.
    2. Confirm imports, controls, and calculations are in separate Python cells.
    3. Inspect the `.py` source: Markdown cells have `hide_code=True` and only
       a standalone `mo.md(...)` display expression.
    4. Move the slider in the live notebook and check the table updates.

    The HTML preview captures the default view. Use the live notebook for
    Python-backed interaction. All files remain local under `notes/`.
    """)
    return


if __name__ == "__main__":
    app.run()
