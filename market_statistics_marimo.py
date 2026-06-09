import marimo

__generated_with = "0.23.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import pandas as pd
    import numpy as np
    import re
    from pathlib import Path

    # =========================================================
    # CONFIG
    # =========================================================
    folder_path = r"C:\Users\agallen002\OneDrive - PwC\Python\.venv\Scripts\tidy_outputs"
    folder = Path(folder_path)

    print(f"Checking folder: {folder}")

    if not folder.exists():
        print("❌ Folder does not exist")

    else:
        # =====================================================
        # HELPERS
        # =====================================================
        def clean_col(col):
            """Standardise column names to simple snake_case."""
            col = str(col).strip().lower()
            col = re.sub(r"[^\w\s]", "", col)
            col = re.sub(r"\s+", "_", col)
            return col

        def standardise_columns(df):
            """Apply standard column cleaning and map known synonyms."""
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
            """
            Convert accidentquarter values like 201503, 201506, 201509, 201512
            into Q1 / Q2 / Q3 / Q4.
            """
            if pd.isna(x):
                return None

            try:
                x_int = int(float(x))
                month = x_int % 100
                quarter_map = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}
                return quarter_map.get(month, None)
            except Exception:
                return None

        def year_from_accidentquarter(x):
            """Extract year from accidentquarter like 201503 -> 2015."""
            if pd.isna(x):
                return None
            try:
                x_int = int(float(x))
                return x_int // 100
            except Exception:
                return None

        def parse_half_year(x):
            """Keep values like 2015H1 / 2015H2 as they are if present."""
            if pd.isna(x):
                return None
            x = str(x).strip()
            if re.fullmatch(r"\d{4}H[12]", x):
                return x
            return None

        def infer_period_type(row):
            """
            Infer period granularity from available fields.
            Priority:
            - accidentquarter -> quarterly
            - yearh -> half_yearly
            - date/year -> annual
            """
            if pd.notna(row.get("accidentquarter")):
                return "quarterly"
            elif pd.notna(row.get("yearh")):
                return "half_yearly"
            elif pd.notna(row.get("date")) or pd.notna(row.get("year")):
                return "annual"
            return "unknown"

        def build_period_original(row):
            """
            Preserve original period signal for traceability.
            """
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
            """
            Heuristic grouping for convenience in analysis.
            This is a helper category, not a source field.
            """
            if pd.isna(metric_name):
                return "unknown"

            m = str(metric_name).lower()

            if "premium" in m:
                return "premium"
            elif "policy" in m:
                return "exposure"
            elif "claimant" in m or "claim" in m:
                return "claims"
            elif "compensation" in m or "settled cost" in m or "cost" in m:
                return "cost"
            elif "damage" in m or "injury" in m or "total" in m:
                return "claim_split"
            else:
                return "other"

        # =====================================================
        # LOAD FILES
        # =====================================================
        paths = list(folder.glob("*.csv"))
        print(f"✅ Found {len(paths)} CSV files")

        if len(paths) > 0:
            dfs = []

            for p in paths:
                df = pd.read_csv(p)
                df["source_file"] = p.name
                dfs.append(df)

            # =================================================
            # STANDARDISE INPUTS
            # =================================================
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

            # Raw stitched table (traceability layer)
            master_raw_df = pd.concat(aligned, ignore_index=True)

            # =================================================
            # BUILD ANALYSIS-READY MASTER TABLE
            # =================================================
            master_analysis_df = master_raw_df.copy()

            # Remove derived analytics field from base fact table if present
            if "yoy_change" in master_analysis_df.columns:
                master_analysis_df = master_analysis_df.drop(columns=["yoy_change"])

            # Numeric coercion
            if "value" in master_analysis_df.columns:
                master_analysis_df["value"] = pd.to_numeric(
                    master_analysis_df["value"], errors="coerce"
                )

            if "date" in master_analysis_df.columns:
                master_analysis_df["date"] = pd.to_numeric(
                    master_analysis_df["date"], errors="coerce"
                )

            if "year" in master_analysis_df.columns:
                master_analysis_df["year"] = pd.to_numeric(
                    master_analysis_df["year"], errors="coerce"
                )

            if "accidentquarter" in master_analysis_df.columns:
                master_analysis_df["accidentquarter"] = pd.to_numeric(
                    master_analysis_df["accidentquarter"], errors="coerce"
                )

            # Unify metric fields: measure + variable -> metric_name
            if "measure" not in master_analysis_df.columns:
                master_analysis_df["measure"] = np.nan
            if "variable" not in master_analysis_df.columns:
                master_analysis_df["variable"] = np.nan

            master_analysis_df["metric_name"] = master_analysis_df["measure"].combine_first(
                master_analysis_df["variable"]
            )

            # Keep source table label for traceability
            master_analysis_df["metric_source_table"] = (
                master_analysis_df["source_file"]
                .astype(str)
                .str.replace(".csv", "", regex=False)
            )

            # Build clean year field
            derived_year_from_aq = (
                master_analysis_df["accidentquarter"].apply(year_from_accidentquarter)
                if "accidentquarter" in master_analysis_df.columns
                else pd.Series([None] * len(master_analysis_df))
            )

            master_analysis_df["year_clean"] = master_analysis_df["year"].combine_first(
                master_analysis_df["date"]
            ).combine_first(derived_year_from_aq)

            # Quarter + half-year fields
            if "accidentquarter" in master_analysis_df.columns:
                master_analysis_df["quarter"] = master_analysis_df["accidentquarter"].apply(
                    quarter_from_accidentquarter
                )
            else:
                master_analysis_df["quarter"] = None

            if "yearh" in master_analysis_df.columns:
                master_analysis_df["half_year"] = master_analysis_df["yearh"].apply(parse_half_year)
            else:
                master_analysis_df["half_year"] = None

            # Period handling
            master_analysis_df["period_original"] = master_analysis_df.apply(
                build_period_original, axis=1
            )
            master_analysis_df["period_type"] = master_analysis_df.apply(
                infer_period_type, axis=1
            )

            # Standardise cover type
            if "covertype" not in master_analysis_df.columns:
                master_analysis_df["covertype"] = "All"
            else:
                master_analysis_df["covertype"] = (
                    master_analysis_df["covertype"]
                    .astype("string")
                    .fillna("All")
                    .replace("<NA>", "All")
                )

            # Metric grouping helper
            master_analysis_df["metric_category"] = master_analysis_df["metric_name"].apply(
                metric_category
            )

            # Final tidy column order
            preferred_cols = [
                "metric_name",
                "metric_category",
                "value",
                "year_clean",
                "quarter",
                "half_year",
                "period_type",
                "period_original",
                "covertype",
                "source_file",
                "metric_source_table",
                "accidentquarter",
                "year",
                "yearh",
                "date",
                "measure",
                "variable",
            ]

            final_cols = [c for c in preferred_cols if c in master_analysis_df.columns]
            other_cols = [c for c in master_analysis_df.columns if c not in final_cols]

            master_analysis_df = master_analysis_df[final_cols + other_cols]

            # Annual-only analysis table
            master_annual_df = master_analysis_df[
                master_analysis_df["period_type"] == "annual"
            ].copy()

            # =================================================
            # OUTPUT
            # =================================================
            print("\n✅ TABLES CREATED")
            print(f"Raw stitched table rows: {len(master_raw_df):,}")
            print(f"Analysis-ready master rows: {len(master_analysis_df):,}")
            print(f"Annual-only master rows: {len(master_annual_df):,}")

            print("\n✅ Analysis-ready columns:")
            print(master_analysis_df.columns.tolist())

            print("\n✅ Annual master preview:")
            master_annual_df.head(20)
    return (master_analysis_df,)


@app.cell
def _(master_analysis_df):
    master_analysis_df
    return


@app.cell
def _(master_analysis_df):
    master_analysis_df.head()
    return


@app.cell
def _(master_analysis_df):
    import marimo as mo

    # Convert year to STRING (this is the key fix)
    master_analysis_df["year_str"] = master_analysis_df["year_clean"].astype(str)

    years = sorted(master_analysis_df["year_str"].dropna().unique().tolist())

    year_filter = mo.ui.dropdown(
        options=years,
        value=years[0] if years else None,
        label="Year"
    )

    year_filter
    return mo, year_filter


@app.cell
def _(master_analysis_df, year_filter):
    def _():
        df = master_analysis_df.copy()

        # ✅ compare STRING to STRING (guaranteed match)
        df["year_str"] = df["year_clean"].astype(str)

        if year_filter.value:
            filtered_df = df[df["year_str"] == year_filter.value]
        else:
            filtered_df = df

        print("Selected year:", year_filter.value)
        print("Rows:", len(filtered_df))
        return filtered_df


    _()
    return


@app.cell
def _(master_analysis_df, mo):
    metrics = sorted(
        master_analysis_df["metric_name"]
        .dropna()
        .unique()
        .tolist()
    )

    metric_filter = mo.ui.dropdown(
        options=["All"] + metrics,
        value="All",
        label="Metric"
    )

    metric_filter

    return (metric_filter,)


@app.cell
def _(master_analysis_df, metric_filter, year_filter):
    def _():
        df = master_analysis_df.copy()
        df["year_str"] = df["year_clean"].astype(str)

        # Year filter ✅
        filtered_df = df[df["year_str"] == year_filter.value]

        # Metric filter ✅
        if metric_filter.value != "All":
            filtered_df = filtered_df[
                filtered_df["metric_name"] == metric_filter.value
            ]

        print("Rows:", len(filtered_df))
        return filtered_df


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The code above is a working year filter and metric filter.
    """)
    return


@app.cell
def _(metric_filter, year_filter):
    def _():
        import marimo as mo
        return mo.vstack([
            mo.md("## 📊 Filters"),
            mo.hstack([year_filter, metric_filter])
        ])


    _()
    return


@app.cell
def _(master_analysis_df, metric_filter, year_filter):
    def _():
        df = master_analysis_df.copy()
        df["year_str"] = df["year_clean"].astype(str)

        filtered_df = df[df["year_str"] == year_filter.value]

        if metric_filter.value != "All":
            filtered_df = filtered_df[
                filtered_df["metric_name"] == metric_filter.value
            ]
        return filtered_df


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    The above code combines the two filters and they both work!
    """)
    return


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

    return (year_range,)


@app.cell
def _(master_analysis_df, year_range):
    def _():
        df = master_analysis_df.copy()

        filtered_df = df[
            (df["year_clean"] >= year_range.value[0]) &
            (df["year_clean"] <= year_range.value[1])
        ]
        return filtered_df


    _()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    This slider filter allows us to select a range of years and it works!
    """)
    return


if __name__ == "__main__":
    app.run()
