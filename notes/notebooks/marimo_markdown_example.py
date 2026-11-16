import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Create a "Markdown" cell by clicking the `Markdown` button below,
    or through the cell action menu.

    Markdown is represented as Python under-the-hood, using the `mo.md()`
    function — so you'll need to import marimo as mo into your notebook
    first!

    This is the correct way to do all markdown. 
    Any markdown in any notebook should always be done this way.
    It should be fully separated from Python cells. 
    No markdown should exist in Python cells.
    """)
    return

if __name__ == "__main__":
    app.run()
