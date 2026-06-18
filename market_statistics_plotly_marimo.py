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


@app.cell
def _(mo):
    file = mo.ui.file(filetypes=[".csv"])

    mo.vstack([
        mo.md("## Upload your CSV"),
        file
    ])
    return (file,)


@app.cell
def _(file, io, pd):
    df = None

    if file.value:
        df = pd.read_csv(io.BytesIO(file.contents()))

        if "Year" in df.columns:
            df = df.drop(columns=["Year"])

    df
    return (df,)


@app.cell
def _(df, mo):
    def _():
        if df is not None:
            cols = list(df.columns)

            x_select = mo.ui.dropdown(
                cols,
                value="year" if "year" in cols else cols[0],
                label="X-axis"
            )

            y_select = mo.ui.dropdown(
                cols,
                value="value" if "value" in cols else cols[-1],
                label="Y-axis"
            )

            color_select = mo.ui.dropdown(
                ["None"] + cols,
                value="CoverType" if "CoverType" in cols else "None",
                label="Colour grouping"
            )
        return mo.vstack([
                mo.md("## Choose your axes"),
                x_select,
                y_select,
                color_select
            ])


    _()
    return


@app.cell
def _(color_select, df, mo, px, x_select, y_select):
    def _():
        if df is not None:
            x_col = x_select.value
            y_col = y_select.value
            color_col = color_select.value

            if color_col == "None":
                color_col = None

            # Build grouped data so chart changes are visible
            group_cols = [x_col]
            if color_col is not None:
                group_cols.append(color_col)

            df_plot = df.groupby(group_cols, as_index=False)[y_col].sum()

            debug_text = mo.md(f"""
            ### Current selection
            - X: {x_col}
            - Y: {y_col}
            - Colour: {color_col}
            """)

            fig = px.line(
                df_plot,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"{y_col} vs {x_col}"
            )

            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title=y_col,
                hovermode="x unified"
            )
        return mo.vstack([debug_text, fig])


    _()
    return


if __name__ == "__main__":
    app.run()
