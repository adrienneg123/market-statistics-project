import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import io

    return io, mo, pd, px


@app.cell(hide_code=True)
def _(mo):
    file = mo.ui.file(
        label="Select CSV file",
        filetypes=[".csv"],
        multiple=False
    )

    file
    return (file,)


@app.cell(hide_code=True)
def _(file, io, mo, pd):
    if file.value:
        df = pd.read_csv(
            io.BytesIO(file.value[0].contents),
            sep=None,
            engine="python"
        )

        # Clean duplicate Year column
        if "Year" in df.columns:
            df = df.drop(columns=["Year"])

        mo.vstack([
            mo.md(f"✅ Loaded: **{file.value[0].name}**"),
            df.head()
        ])
    else:
        mo.md("❌ No file selected")
    return (df,)


@app.cell(hide_code=True)
def _(df, mo):
    cols = list(df.columns)

    mo.vstack([
        mo.md("### Available columns"),
        mo.md("\n".join([f"{i+1}. {col}" for i, col in enumerate(cols)]))
    ])
    return (cols,)


@app.cell(hide_code=True)
def _(cols, mo):
    x_col = mo.ui.dropdown(
        options=cols,
        value=cols[0] if cols else None,
        label="Select X-axis column"
    )

    y_col = mo.ui.dropdown(
        options=cols,
        value=cols[1] if len(cols) > 1 else cols[0] if cols else None,
        label="Select Y-axis column"
    )

    mo.vstack([x_col, y_col])
    return x_col, y_col


@app.cell(hide_code=True)
def _(cols, mo):
    use_colour = mo.ui.radio(
        options=["No", "Yes"],
        value="No",
        label="Split by category?"
    )

    color_col = mo.ui.dropdown(
        options=cols,
        value=cols[0] if cols else None,
        label="Select colour grouping column"
    )

    mo.vstack([use_colour, color_col])

    return color_col, use_colour


@app.cell(hide_code=True)
def _(color_col, df, mo, px, use_colour, x_col, y_col):
    selected_color_col = color_col.value if use_colour.value == "Yes" else None

    group_cols = [x_col.value]
    if selected_color_col:
        group_cols.append(selected_color_col)

    # Aggregate if duplicates exist
    if df.groupby(group_cols).size().max() > 1:
        df_plot = df.groupby(group_cols, as_index=False)[y_col.value].sum()
        agg_msg = "⚠️ Aggregating data (multiple rows per group detected)"
    else:
        df_plot = df.copy()
        agg_msg = "✅ No aggregation needed"

    # If colour grouping is measure, use facets instead
    facet = None
    final_color_col = selected_color_col

    if selected_color_col == "measure":
        facet = "measure"
        final_color_col = None
        facet_msg = "⚠️ Measures have different scales → using facet charts instead"
    else:
        facet_msg = "✅ Standard colour grouping"

    fig = px.line(
        df_plot,
        x=x_col.value,
        y=y_col.value,
        color=final_color_col,
        facet_col=facet,
        title=f"{y_col.value} vs {x_col.value}"
    )

    fig.update_layout(
        xaxis_title=x_col.value,
        yaxis_title=y_col.value,
        hovermode="x unified"
    )

    mo.vstack([
        mo.md(agg_msg),
        mo.md(facet_msg),
        mo.ui.plotly(fig)
    ])
    return


if __name__ == "__main__":
    app.run()
