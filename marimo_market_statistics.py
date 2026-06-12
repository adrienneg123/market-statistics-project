import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo


    mo.md("## 📂 Select your input")


    folder_input = mo.ui.text(

        value="tidy_outputs",

        placeholder="Enter folder path (e.g. tidy_outputs or full path)"

    )


    file_input = mo.ui.file(multiple=True)


    folder_input

    file_input

    return file_input, folder_input, mo


@app.cell
def _(file_input, folder_input):
    import pandas as pd

    import numpy as np

    import re

    from pathlib import Path

    import io


    # =========================================================

    # CONFIG

    # =========================================================

    folder_path = folder_input.value

    folder = Path(folder_path)


    use_uploaded_files = len(file_input.value) > 0


    print(f"Selected folder: {folder}")

    print(f"Using uploaded files: {use_uploaded_files}")


    if not use_uploaded_files and not folder.exists():

        print("❌ Folder does not exist")



    # =========================================================

    # HELPERS

    # =========================================================

    def clean_col(col):

        col = str(col).strip().lower()

        col = re.sub(r"[^\w\s]", "", col)

        col = re.sub(r"\s+", "_", col)

        return col



    def standardise_columns(df):

        df = df.copy()

        df.columns = [clean_col(c) for c in df.columns]


        rename_map = {

            "measure": "measure",

            "variable": "variable",

            "value": "value",

            "date": "date",

            "year": "year",

            "yearh": "yearh",

            "accidentquarter": "accidentquarter",

            "covertype": "covertype",

            "source_file": "source_file",

            "yoy_change": "yoy_change",

        }


        df = df.rename(columns={c: rename_map.get(c, c) for c in df.columns})

        return df



    def quarter_from_accidentquarter(x):

        if pd.isna(x):

            return None

        try:

            x_int = int(float(x))

            month = x_int % 100

            return {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}.get(month, None)

        except Exception:

            return None



    def year_from_accidentquarter(x):

        if pd.isna(x):

            return None

        try:

            return int(float(x)) // 100

        except Exception:

            return None



    def parse_half_year(x):

        if pd.isna(x):

            return None

        x = str(x).strip()

        return x if re.fullmatch(r"\d{4}H[12]", x) else None



    def infer_period_type(row):

        if pd.notna(row.get("accidentquarter")):

            return "quarterly"

        elif pd.notna(row.get("yearh")):

            return "half_yearly"

        elif pd.notna(row.get("date")) or pd.notna(row.get("year")):

            return "annual"

        return "unknown"



    def build_period_original(row):

        if pd.notna(row.get("accidentquarter")):

            return str(row["accidentquarter"])

        elif pd.notna(row.get("yearh")):

            return str(row["yearh"])

        elif pd.notna(row.get("date")):

            return str(row["date"])

        elif pd.notna(row.get("year")):

            return str(row["year"])

        return None



    def metric_category(metric_name):

        if pd.isna(metric_name):

            return "unknown"


        m = str(metric_name).lower()


        if "premium" in m:

            return "premium"

        elif "policy" in m:

            return "exposure"

        elif "claimant" in m or "claim" in m:

            return "claims"

        elif "compensation" in m or "cost" in m:

            return "cost"

        elif "damage" in m or "injury" in m or "total" in m:

            return "claim_split"

        else:

            return "other"



    # =========================================================

    # LOAD FILES

    # =========================================================

    dfs = []


    if use_uploaded_files:

        print(f"✅ Using {len(file_input.value)} uploaded files")


        for f in file_input.value:

            content = f.contents.decode("utf-8")

            df = pd.read_csv(io.StringIO(content))


            df["source_file"] = getattr(f, "name", "uploaded_file")

            dfs.append(df)


    else:

        if folder.exists():

            paths = list(folder.glob("*.csv"))

            print(f"✅ Found {len(paths)} CSV files in folder")


            for p in paths:

                df = pd.read_csv(p)

                df["source_file"] = p.name

                dfs.append(df)



    # =========================================================

    # PROCESSING

    # =========================================================

    if len(dfs) > 0:


        dfs = [standardise_columns(df) for df in dfs]


        # Align schemas

        all_cols = set()

        for df in dfs:

            all_cols.update(df.columns)


        aligned = []

        for df in dfs:

            df_copy = df.copy()

            for c in all_cols:

                if c not in df_copy.columns:

                    df_copy[c] = np.nan

            aligned.append(df_copy[list(all_cols)])


        master_raw_df = pd.concat(aligned, ignore_index=True)


        master_analysis_df = master_raw_df.copy()


        if "yoy_change" in master_analysis_df.columns:

            master_analysis_df = master_analysis_df.drop(columns=["yoy_change"])


        for col in ["value", "date", "year", "accidentquarter"]:

            if col in master_analysis_df.columns:

                master_analysis_df[col] = pd.to_numeric(

                    master_analysis_df[col], errors="coerce"

                )


        master_analysis_df["measure"] = master_analysis_df.get("measure", np.nan)

        master_analysis_df["variable"] = master_analysis_df.get("variable", np.nan)


        master_analysis_df["metric_name"] = master_analysis_df["measure"].combine_first(

            master_analysis_df["variable"]

        )


        master_analysis_df["metric_source_table"] = (

            master_analysis_df["source_file"]

            .astype(str)

            .str.replace(".csv", "", regex=False)

        )


        derived_year_from_aq = master_analysis_df.get(

            "accidentquarter", pd.Series([None] * len(master_analysis_df))

        ).apply(year_from_accidentquarter)


        master_analysis_df["year_clean"] = (

            master_analysis_df.get("year")

            .combine_first(master_analysis_df.get("date"))

            .combine_first(derived_year_from_aq)

        )


        if "accidentquarter" in master_analysis_df:

            master_analysis_df["quarter"] = master_analysis_df["accidentquarter"].apply(

                quarter_from_accidentquarter

            )

        else:

            master_analysis_df["quarter"] = None


        if "yearh" in master_analysis_df:

            master_analysis_df["half_year"] = master_analysis_df["yearh"].apply(

                parse_half_year

            )

        else:

            master_analysis_df["half_year"] = None


        master_analysis_df["period_original"] = master_analysis_df.apply(

            build_period_original, axis=1

        )

        master_analysis_df["period_type"] = master_analysis_df.apply(

            infer_period_type, axis=1

        )


        if "covertype" not in master_analysis_df.columns:

            master_analysis_df["covertype"] = "All"

        else:

            master_analysis_df["covertype"] = (

                master_analysis_df["covertype"]

                .astype("string")

                .fillna("All")

            )


        master_analysis_df["metric_category"] = master_analysis_df["metric_name"].apply(

            metric_category

        )


        preferred_cols = [

            "metric_name", "metric_category", "value", "year_clean",

            "quarter", "half_year", "period_type", "period_original",

            "covertype", "source_file", "metric_source_table"

        ]


        final_cols = [c for c in preferred_cols if c in master_analysis_df.columns]

        other_cols = [c for c in master_analysis_df.columns if c not in final_cols]


        master_analysis_df = master_analysis_df[final_cols + other_cols]


        master_annual_df = master_analysis_df[

            master_analysis_df["period_type"] == "annual"

        ].copy()


        print("\n✅ TABLES CREATED")

        print(f"Raw rows: {len(master_raw_df):,}")

        print(f"Analysis rows: {len(master_analysis_df):,}")

        print(f"Annual rows: {len(master_annual_df):,}")


        print("\n✅ Columns:")

        print(master_analysis_df.columns.tolist())


        master_annual_df.head(20)


    else:

        print("❌ No files found or uploaded")
    return master_analysis_df, pd


@app.cell
def _(master_analysis_df, mo):
    years_numeric = sorted(master_analysis_df["year_clean"].dropna().unique())


    year_range = mo.ui.range_slider(

        start=int(min(years_numeric)),

        stop=int(max(years_numeric)),

        value=(2015, 2020),

        label="Year range"

    )


    year_range
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    LOSS RATIO
    """)
    return


@app.cell
def _(master_analysis_df, pd):
    pd.set_option('display.max_rows', None)
    def _():
        import pandas as pd

        df = master_analysis_df.copy()

        # Keep only needed columns
        df = df[["metric_name", "value", "year"]]

        # Create a pivot
        pivot = df.pivot_table(
            index="year",
            columns="metric_name",
            values="value",
            aggfunc="sum"
        ).reset_index()

        # Calculate Loss Ratio
        pivot["Loss Ratio"] = pivot["Net Claims Incurred"] / pivot["Gross Earned Premium / Insurance Revenue"]
        return print(pivot[["year", "Loss Ratio"]])


    _()

    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    COMMISSION RATIO
    """)
    return


@app.cell
def _(master_analysis_df):
    def _():
        import pandas as pd

        df = master_analysis_df.copy()

        df = df[["metric_name", "value", "year"]]

        pivot = df.pivot_table(
            index="year",
            columns="metric_name",
            values="value",
            aggfunc="sum"
        ).reset_index()

        pivot["Commission Ratio"] = (
            pivot["Commission Payable (Third Party & Related)"]
            / pivot["Gross Written Premium"]
        )
        return print(pivot[["year", "Commission Ratio"]])


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    COMBINED RATIO
    """)
    return


@app.cell
def _(master_analysis_df):
    def _():
        import pandas as pd

        df = master_analysis_df.copy()

        df = df[["metric_name", "value", "year"]]

        pivot = df.pivot_table(
            index="year",
            columns="metric_name",
            values="value",
            aggfunc="sum"
        ).reset_index()

        pivot["Combined Ratio"] = (
            pivot["Net Claims Incurred"]
            + pivot["Management Expenses"]
            + pivot["Other Expenses"]
            + pivot["Commission Payable (Third Party & Related)"]
        ) / pivot["Gross Earned Premium / Insurance Revenue"]
        return print(pivot[["year", "Combined Ratio"]])


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    EXPENSE RATIO
    """)
    return


@app.cell
def _(master_analysis_df):
    def _():
        import pandas as pd

        df = master_analysis_df.copy()

        df = df[["metric_name", "value", "year"]]

        pivot = df.pivot_table(
            index="year",
            columns="metric_name",
            values="value",
            aggfunc="sum"
        ).reset_index()

        pivot["Expense Ratio"] = (
            pivot["Management Expenses"]
            + pivot["Other Expenses"]
        ) / pivot["Gross Earned Premium / Insurance Revenue"]
        return print(pivot[["year", "Expense Ratio"]])


    _()
    return


if __name__ == "__main__":
    app.run()
