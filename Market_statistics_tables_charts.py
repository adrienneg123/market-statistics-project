import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo

    import pandas as pd

    import numpy as np

    import re

    import io

    from pathlib import Path

    import altair as alt

    return Path, alt, io, mo, np, pd, re


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Insurance CSV Analysis - Flexible Marimo App

    This notebook provides an end-to-end, reactive workflow for:

    1. loading one or more CSV files from **uploads** or a **folder**,
    2. cleaning and harmonising schemas,
    3. building a standardised **master analysis dataframe**,
    4. interactively filtering the data,
    5. building custom summary tables,
    6. calculating generic ratios,
    7. and visualising the output.

    The design avoids hardcoded ratio cells and instead uses reusable logic throughout.
    """)
    return


@app.cell(hide_code=True)
def _(pd, re):
    # -----------------------------

    # Helper functions

    # -----------------------------


    def clean_col(col):

        """Normalise column names into a safe snake_case style."""

        col = str(col).strip().lower()

        col = re.sub(r"[^\w\s]", "", col)

        col = re.sub(r"\s+", "_", col)

        return col


    def standardise_columns(df):

        """Standardise columns and apply a small alias map for common names."""

        df = df.copy()

        df.columns = [clean_col(c) for c in df.columns]


        alias_map = {

            "cover_type": "covertype",

            "cover": "covertype",

            "sourcefile": "source_file",

            "source": "source_file",

            "accident_quarter": "accidentquarter",

            "year_h": "yearh",

            "year_half": "yearh",

            "metric": "measure",

        }


        df = df.rename(columns={c: alias_map.get(c, c) for c in df.columns})

        return df


    def safe_read_csv_from_upload(file_obj, pd, io):

        """Read a CSV uploaded through marimo, defensively."""

        try:

            contents = file_obj.contents

            if isinstance(contents, bytes):

                text = contents.decode("utf-8", errors="replace")

            else:

                text = str(contents)

            df = pd.read_csv(io.StringIO(text))

            return df, None

        except Exception as e:

            return None, f"Failed to read uploaded file '{getattr(file_obj, 'name', 'unknown')}': {e}"


    def safe_read_csv_from_path(path, pd):

        """Read a CSV from disk, defensively."""

        try:

            df = pd.read_csv(path)

            return df, None

        except Exception as e:

            return None, f"Failed to read file '{path}': {e}"


    def quarter_from_accidentquarter(x):

        """Parse numeric YYYYMM-style accidentquarter into Q1-Q4."""

        if pd.isna(x):

            return None

        try:

            x_int = int(float(x))

            month = x_int % 100

            return {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}.get(month, None)

        except Exception:

            return None


    def year_from_accidentquarter(x):

        """Extract year from YYYYMM-style accidentquarter."""

        if pd.isna(x):

            return None

        try:

            return int(float(x)) // 100

        except Exception:

            return None


    def parse_half_year(x):

        """Keep values like 2020H1 / 2020H2."""

        if pd.isna(x):

            return None

        x = str(x).strip()

        return x if re.fullmatch(r"\d{4}H[12]", x) else None


    def metric_category(metric_name):

        """Simple heuristic metric categorisation."""

        if pd.isna(metric_name):

            return "unknown"


        m = str(metric_name).strip().lower()


        if "premium" in m:

            return "premium"

        if "policy" in m:

            return "exposure"

        if "claimant" in m or "claim" in m:

            return "claims"

        if "commission" in m:

            return "commission"

        if "expense" in m or "management" in m:

            return "expense"

        if "compensation" in m or "cost" in m:

            return "cost"

        if "damage" in m or "injury" in m or "total" in m:

            return "claim_split"

        return "other"


    def infer_period_type(row):

        """Infer annual / quarterly / half_yearly / unknown from period fields."""

        if pd.notna(row.get("accidentquarter")):

            return "quarterly"

        if pd.notna(row.get("yearh")):

            return "half_yearly"

        if pd.notna(row.get("date")) or pd.notna(row.get("year")):

            return "annual"

        return "unknown"


    def build_period_original(row):

        """Preserve the original source period value where possible."""

        if pd.notna(row.get("accidentquarter")):

            return str(row.get("accidentquarter"))

        if pd.notna(row.get("yearh")):

            return str(row.get("yearh"))

        if pd.notna(row.get("date")):

            return str(row.get("date"))

        if pd.notna(row.get("year")):

            return str(row.get("year"))

        return None


    def align_schemas(dfs, np):

        """Union-align schemas across multiple dataframes."""

        if not dfs:

            return []


        all_cols = set()

        for df in dfs:

            all_cols.update(df.columns)


        ordered_cols = sorted(all_cols)

        aligned = []


        for df in dfs:

            tmp = df.copy()

            for c in ordered_cols:

                if c not in tmp.columns:

                    tmp[c] = np.nan

            aligned.append(tmp[ordered_cols])


        return aligned


    def build_master_analysis_df(raw_df, np, pd):

        """Build the standardised master analysis dataframe."""

        if raw_df is None or raw_df.empty:

            return pd.DataFrame()


        df = raw_df.copy()


        # Drop noisy columns if present

        if "yoy_change" in df.columns:

            df = df.drop(columns=["yoy_change"])


        # Ensure expected columns exist

        expected_cols = [

            "measure", "variable", "value", "date", "year", "yearh",

            "accidentquarter", "covertype", "source_file"

        ]

        for c in expected_cols:

            if c not in df.columns:

                df[c] = np.nan


        # Coerce likely numeric columns

        for c in ["value", "date", "year", "accidentquarter"]:

            if c in df.columns:

                df[c] = pd.to_numeric(df[c], errors="coerce")


        # Metric naming

        df["metric_name"] = (

            df["measure"].astype("string").replace("<NA>", pd.NA)

            .combine_first(df["variable"].astype("string").replace("<NA>", pd.NA))

        )


        # Metadata / lineage

        df["metric_source_table"] = (

            df["source_file"]

            .astype("string")

            .fillna("unknown_source")

            .str.replace(".csv", "", regex=False)

        )


        # Derived year

        derived_year_from_aq = df["accidentquarter"].apply(year_from_accidentquarter)

        year_from_year = pd.to_numeric(df["year"], errors="coerce")

        year_from_date = pd.to_numeric(df["date"], errors="coerce")


        df["year_clean"] = (

            year_from_year

            .combine_first(year_from_date)

            .combine_first(derived_year_from_aq)

        )


        # time fields

        df["quarter"] = df["accidentquarter"].apply(quarter_from_accidentquarter)

        df["half_year"] = df["yearh"].apply(parse_half_year)


        df["period_original"] = df.apply(build_period_original, axis=1)

        df["period_type"] = df.apply(infer_period_type, axis=1)


        # cover type defensive fill

        df["covertype"] = (

            df["covertype"]

            .astype("string")

            .replace("<NA>", pd.NA)

            .fillna("All")

        )


        # metric category

        df["metric_category"] = df["metric_name"].apply(metric_category)


        # stable ordering

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

            "measure",

            "variable",

            "year",

            "date",

            "yearh",

            "accidentquarter",

        ]


        final_cols = [c for c in preferred_cols if c in df.columns]

        other_cols = [c for c in df.columns if c not in final_cols]

        df = df[final_cols + other_cols]


        return df


    def build_load_status(file_metadata_df, master_df, pd):

        """Build a compact status summary dataframe."""

        if file_metadata_df is None or file_metadata_df.empty:

            return pd.DataFrame(

                {

                    "status": ["No files loaded"],

                    "details": ["Provide uploaded CSVs or a valid folder containing CSV files."],

                }

            )


        total_rows = int(file_metadata_df["row_count"].sum()) if "row_count" in file_metadata_df.columns else 0

        total_files = len(file_metadata_df)


        summary_rows = [

            {

                "status": "Files loaded",

                "details": total_files,

            },

            {

                "status": "Total rows loaded",

                "details": total_rows,

            },

            {

                "status": "Master dataframe rows",

                "details": len(master_df) if master_df is not None else 0,

            },

            {

                "status": "Master dataframe columns",

                "details": len(master_df.columns.tolist()) if master_df is not None else 0,

            },

        ]


        return pd.DataFrame(summary_rows)


    def safe_sorted_unique(series):

        """Sorted list of non-null unique values."""

        if series is None:

            return []

        vals = pd.Series(series).dropna().astype(str).unique().tolist()

        try:

            return sorted(vals)

        except Exception:

            return vals


    def numeric_sorted_unique(series):

        """Sorted numeric unique values, coerced where possible."""

        if series is None:

            return []

        s = pd.to_numeric(pd.Series(series), errors="coerce").dropna()

        if s.empty:

            return []

        return sorted(s.astype(int).unique().tolist())


    def apply_filters(

        df,

        year_range_value,

        period_types,

        cover_types,

        source_files,

        metric_categories,

        metric_names,

    ):

        """Apply all interactive filters defensively."""

        if df is None or df.empty:

            return df


        out = df.copy()


        if "year_clean" in out.columns and year_range_value is not None:

            lo, hi = year_range_value

            out = out[

                pd.to_numeric(out["year_clean"], errors="coerce").between(lo, hi, inclusive="both")

            ]


        if period_types and "period_type" in out.columns:

            out = out[out["period_type"].astype(str).isin(period_types)]


        if cover_types and "covertype" in out.columns:

            out = out[out["covertype"].astype(str).isin(cover_types)]


        if source_files and "source_file" in out.columns:

            out = out[out["source_file"].astype(str).isin(source_files)]


        if metric_categories and "metric_category" in out.columns:

            out = out[out["metric_category"].astype(str).isin(metric_categories)]


        if metric_names and "metric_name" in out.columns:

            out = out[out["metric_name"].astype(str).isin(metric_names)]


        return out


    def flatten_columns(df):

        """Flatten MultiIndex columns after pivot operations."""

        if df is None or df.empty:

            return df


        if isinstance(df.columns, pd.MultiIndex):

            flat_cols = []

            for tup in df.columns:

                parts = [str(x) for x in tup if str(x) not in ["", "None"]]

                flat_cols.append(" | ".join(parts))

            df = df.copy()

            df.columns = flat_cols

        return df


    def build_summary_table(df, rows, cols, values, aggfunc, pd):

        """Generic pivot-style summary table."""

        if df is None or df.empty:

            return pd.DataFrame()


        if not values:

            return pd.DataFrame({"message": ["Select at least one value field."]})


        valid_rows = [c for c in rows if c in df.columns]

        valid_cols = [c for c in cols if c in df.columns]

        valid_values = [c for c in values if c in df.columns]


        if not valid_values:

            return pd.DataFrame({"message": ["None of the selected value fields exist in the filtered dataset."]})


        working = df.copy()

        for c in valid_values:

            working[c] = pd.to_numeric(working[c], errors="coerce")


        # If no rows and no columns, return simple aggregate

        if not valid_rows and not valid_cols:

            result = working[valid_values].agg(aggfunc).to_frame().T

            result.insert(0, "summary_level", "overall")

            return result


        pivot = pd.pivot_table(

            working,

            index=valid_rows if valid_rows else None,

            columns=valid_cols if valid_cols else None,

            values=valid_values,

            aggfunc=aggfunc,

            dropna=False,

        )


        pivot = pivot.reset_index()

        pivot = flatten_columns(pivot)

        return pivot


    def apply_ratio_preset(preset_name):

        """Optional prebuilt ratio presets."""

        presets = {

            "Custom": {

                "ratio_name": "Custom Ratio",

                "numerator_metrics": [],

                "denominator_metrics": [],

            },

            "Loss Ratio": {

                "ratio_name": "Loss Ratio",

                "numerator_metrics": ["Net Claims Incurred"],

                "denominator_metrics": ["Gross Earned Premium / Insurance Revenue"],

            },

            "Commission Ratio": {

                "ratio_name": "Commission Ratio",

                "numerator_metrics": ["Commission Payable (Third Party & Related)"],

                "denominator_metrics": ["Gross Written Premium"],

            },

            "Combined Ratio": {

                "ratio_name": "Combined Ratio",

                "numerator_metrics": [

                    "Net Claims Incurred",

                    "Management Expenses",

                    "Other Expenses",

                    "Commission Payable (Third Party & Related)",

                ],

                "denominator_metrics": ["Gross Earned Premium / Insurance Revenue"],

            },

            "Expense Ratio": {

                "ratio_name": "Expense Ratio",

                "numerator_metrics": [

                    "Management Expenses",

                    "Other Expenses",

                ],

                "denominator_metrics": ["Gross Earned Premium / Insurance Revenue"],

            },

        }

        return presets.get(preset_name, presets["Custom"])


    def build_ratio_table(

        df,

        ratio_name,

        numerator_metrics,

        denominator_metrics,

        group_cols,

        aggfunc,

        pd,

        np,

    ):

        """

        Generic ratio engine:

        - filters metric_name to numerator/denominator selections,

        - aggregates each side,

        - safely divides numerator by denominator.

        """

        if df is None or df.empty:

            return pd.DataFrame()


        if not numerator_metrics or not denominator_metrics:

            return pd.DataFrame(

                {

                    "message": [

                        "Select at least one numerator metric and one denominator metric."

                    ]

                }

            )


        if "metric_name" not in df.columns or "value" not in df.columns:

            return pd.DataFrame(

                {

                    "message": [

                        "Filtered data must contain 'metric_name' and 'value' to calculate a ratio."

                    ]

                }

            )


        working = df.copy()

        working["value"] = pd.to_numeric(working["value"], errors="coerce")


        valid_group_cols = [c for c in group_cols if c in working.columns]


        num_df = working[working["metric_name"].astype(str).isin(numerator_metrics)].copy()

        den_df = working[working["metric_name"].astype(str).isin(denominator_metrics)].copy()


        if valid_group_cols:

            numerator = (

                num_df.groupby(valid_group_cols, dropna=False)["value"]

                .agg(aggfunc)

                .reset_index(name="numerator_value")

            )

            denominator = (

                den_df.groupby(valid_group_cols, dropna=False)["value"]

                .agg(aggfunc)

                .reset_index(name="denominator_value")

            )

            ratio_df = numerator.merge(denominator, on=valid_group_cols, how="outer")

        else:

            numerator_value = num_df["value"].agg(aggfunc)

            denominator_value = den_df["value"].agg(aggfunc)

            ratio_df = pd.DataFrame(

                {

                    "numerator_value": [numerator_value],

                    "denominator_value": [denominator_value],

                }

            )


        ratio_df["numerator_value"] = pd.to_numeric(ratio_df["numerator_value"], errors="coerce")

        ratio_df["denominator_value"] = pd.to_numeric(ratio_df["denominator_value"], errors="coerce")


        ratio_df[ratio_name] = np.where(

            ratio_df["denominator_value"].fillna(0) == 0,

            np.nan,

            ratio_df["numerator_value"] / ratio_df["denominator_value"],

        )


        return ratio_df


    def aggregate_for_chart(df, x_col, y_col, color_col, aggfunc, pd):

        """Aggregate data for visualisation."""

        if df is None or df.empty:

            return pd.DataFrame()


        if x_col not in df.columns or y_col not in df.columns:

            return pd.DataFrame()


        working = df.copy()

        working[y_col] = pd.to_numeric(working[y_col], errors="coerce")


        group_cols = [x_col]

        if color_col and color_col in working.columns and color_col != x_col:

            group_cols.append(color_col)


        chart_df = (

            working.groupby(group_cols, dropna=False)[y_col]

            .agg(aggfunc)

            .reset_index()

        )


        return chart_df

    return (
        aggregate_for_chart,
        align_schemas,
        apply_filters,
        build_load_status,
        build_master_analysis_df,
        build_ratio_table,
        build_summary_table,
        numeric_sorted_unique,
        safe_read_csv_from_path,
        safe_read_csv_from_upload,
        safe_sorted_unique,
        standardise_columns,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. Inputs
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    source_mode = mo.ui.radio(

        options=["Auto", "Uploaded files", "Folder path"],

        value="Auto",

        label="Input source",

    )


    folder_input = mo.ui.text(

        value="tidy_outputs",

        placeholder="Enter a folder path containing CSV files",

        label="Folder path",

    )


    file_input = mo.ui.file(

        multiple=True,

        label="Upload one or more CSV files",

    )


    mo.vstack(

        [

            source_mode,

            folder_input,

            file_input,

        ]

    )
    return file_input, folder_input, source_mode


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. Data loading and harmonisation
    """)
    return


@app.cell(hide_code=True)
def _(
    Path,
    align_schemas,
    build_master_analysis_df,
    file_input,
    folder_input,
    io,
    pd,
    safe_read_csv_from_path,
    safe_read_csv_from_upload,
    source_mode,
    standardise_columns,
):
    # Determine input mode reactively

    uploaded_files = list(file_input.value) if file_input.value else []

    folder_path = str(folder_input.value).strip()

    folder = Path(folder_path) if folder_path else None


    if source_mode.value == "Uploaded files":

        use_uploaded_files = len(uploaded_files) > 0

    elif source_mode.value == "Folder path":

        use_uploaded_files = False

    else:

        # Auto mode prioritises uploaded files if any are present

        use_uploaded_files = len(uploaded_files) > 0


    loaded_dfs = []

    load_errors = []

    file_metadata = []


    # Load uploaded files

    if use_uploaded_files:

        for file_obj in uploaded_files:

            df, err = safe_read_csv_from_upload(file_obj, pd, io)

            if err:

                load_errors.append(err)

                continue


            df = standardise_columns(df)

            df["source_file"] = getattr(file_obj, "name", "uploaded_file.csv")

            loaded_dfs.append(df)


            file_metadata.append(

                {

                    "source_file": getattr(file_obj, "name", "uploaded_file.csv"),

                    "row_count": len(df),

                    "column_count": len(df.columns),

                    "columns_detected": ", ".join(df.columns.tolist()),

                    "load_source": "upload",

                }

            )


    # Load folder files

    else:

        if folder is None or not folder.exists():

            load_errors.append(f"Folder does not exist: {folder_path}")

        else:

            csv_paths = sorted(folder.glob("*.csv"))

            if not csv_paths:

                load_errors.append(f"No CSV files found in folder: {folder_path}")


            for path in csv_paths:

                df, err = safe_read_csv_from_path(path, pd)

                if err:

                    load_errors.append(err)

                    continue


                df = standardise_columns(df)

                df["source_file"] = path.name

                loaded_dfs.append(df)


                file_metadata.append(

                    {

                        "source_file": path.name,

                        "row_count": len(df),

                        "column_count": len(df.columns),

                        "columns_detected": ", ".join(df.columns.tolist()),

                        "load_source": "folder",

                    }

                )


    # Align schemas and build master datasets

    if loaded_dfs:

        aligned_dfs = align_schemas(loaded_dfs, __import__("numpy"))

        master_raw_df = pd.concat(aligned_dfs, ignore_index=True)

        master_analysis_df = build_master_analysis_df(master_raw_df, __import__("numpy"), pd)

    else:

        master_raw_df = pd.DataFrame()

        master_analysis_df = pd.DataFrame()


    file_metadata_df = pd.DataFrame(file_metadata)

    master_annual_df = (

        master_analysis_df[master_analysis_df["period_type"] == "annual"].copy()

        if not master_analysis_df.empty and "period_type" in master_analysis_df.columns

        else pd.DataFrame()

    )
    return file_metadata_df, load_errors, master_analysis_df, master_raw_df


@app.cell(hide_code=True)
def _(
    build_load_status,
    file_metadata_df,
    load_errors,
    master_analysis_df,
    mo,
    pd,
):
    status_df = build_load_status(file_metadata_df, master_analysis_df, pd)


    error_text = (

        "\n".join([f"- {e}" for e in load_errors]) if load_errors else "No load errors."

    )


    mo.vstack(

        [

            mo.md("### Load summary"),

            status_df,

            mo.md("### File-level detail"),

            file_metadata_df if not file_metadata_df.empty else pd.DataFrame({"info": ["No file metadata available."]}),

            mo.md("### Load errors / warnings"),

            mo.md(error_text),

        ]

    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 3. Master data preview
    """)
    return


@app.cell(hide_code=True)
def _(master_analysis_df, master_raw_df, mo, pd):
    preview_message = (

        f"Master raw rows: **{len(master_raw_df):,}**  \n"

        f"Master analysis rows: **{len(master_analysis_df):,}**  \n"

        f"Master analysis columns: **{len(master_analysis_df.columns):,}**"

        if not master_analysis_df.empty

        else "No master dataframe available yet."

    )


    mo.vstack(

        [

            mo.md(preview_message),

            mo.md("### Master analysis preview"),

            master_analysis_df.head(50) if not master_analysis_df.empty else pd.DataFrame({"info": ["No data loaded"]}),

        ]

    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 4. Filters
    """)
    return


@app.cell(hide_code=True)
def _(master_analysis_df, mo, numeric_sorted_unique, safe_sorted_unique):
    if master_analysis_df is None or master_analysis_df.empty:

        years = []

        period_types = []

        cover_types = []

        source_files = []

        metric_categories = []

        metric_names = []

    else:

        years = numeric_sorted_unique(master_analysis_df.get("year_clean"))

        period_types = safe_sorted_unique(master_analysis_df.get("period_type"))

        cover_types = safe_sorted_unique(master_analysis_df.get("covertype"))

        source_files = safe_sorted_unique(master_analysis_df.get("source_file"))

        metric_categories = safe_sorted_unique(master_analysis_df.get("metric_category"))

        metric_names = safe_sorted_unique(master_analysis_df.get("metric_name"))


    # Default year range

    if years:

        yr_min, yr_max = min(years), max(years)

        default_year_range = (yr_min, yr_max)

        year_range = mo.ui.range_slider(

            start=yr_min,

            stop=yr_max,

            value=default_year_range,

            label="Year range",

        )

    else:

        year_range = mo.ui.text(

            value="No valid years found",

            label="Year range unavailable",

            disabled=True,

        )


    period_type_filter = mo.ui.multiselect(

        options=period_types,

        value=period_types,

        label="Period type",

    )


    cover_type_filter = mo.ui.multiselect(

        options=cover_types,

        value=cover_types,

        label="Cover type",

    )


    source_file_filter = mo.ui.multiselect(

        options=source_files,

        value=source_files,

        label="Source file",

    )


    metric_category_filter = mo.ui.multiselect(

        options=metric_categories,

        value=metric_categories,

        label="Metric category",

    )


    metric_name_filter = mo.ui.multiselect(

        options=metric_names,

        value=metric_names,

        label="Metric name",

    )


    mo.vstack(

        [

            year_range,

            period_type_filter,

            cover_type_filter,

            source_file_filter,

            metric_category_filter,

            metric_name_filter,

        ]

    )
    return (
        cover_type_filter,
        metric_category_filter,
        metric_name_filter,
        period_type_filter,
        source_file_filter,
        year_range,
    )


@app.cell(hide_code=True)
def _(
    apply_filters,
    cover_type_filter,
    master_analysis_df,
    metric_category_filter,
    metric_name_filter,
    period_type_filter,
    source_file_filter,
    year_range,
):
    if master_analysis_df is None or master_analysis_df.empty:

        filtered_df = master_analysis_df.copy()

    else:

        year_range_value = (

            year_range.value if hasattr(year_range, "value") and isinstance(year_range.value, tuple) else None

        )


        filtered_df = apply_filters(

            master_analysis_df,

            year_range_value=year_range_value,

            period_types=period_type_filter.value,

            cover_types=cover_type_filter.value,

            source_files=source_file_filter.value,

            metric_categories=metric_category_filter.value,

            metric_names=metric_name_filter.value,

        )
    return (filtered_df,)


@app.cell(hide_code=True)
def _(filtered_df, mo, pd):
    mo.vstack(

        [

            mo.md(f"### Filtered data rows: **{len(filtered_df):,}**" if filtered_df is not None else "No filtered data"),

            filtered_df.head(100) if filtered_df is not None and not filtered_df.empty else pd.DataFrame({"info": ["No filtered rows"]}),

        ]

    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 5. Table builder
    """)
    return


@app.cell(hide_code=True)
def _(filtered_df, mo, pd):
    if filtered_df is None or filtered_df.empty:

        available_columns = []

        numeric_columns = []

    else:

        available_columns = filtered_df.columns.tolist()

        numeric_columns = [

            c for c in filtered_df.columns

            if pd.api.types.is_numeric_dtype(filtered_df[c]) or c == "value"

        ]


    row_dimensions = mo.ui.multiselect(

        options=available_columns,

        value=[c for c in ["year_clean", "metric_name"] if c in available_columns],

        label="Row dimensions",

    )


    column_dimensions = mo.ui.multiselect(

        options=available_columns,

        value=[c for c in ["quarter"] if c in available_columns],

        label="Column dimensions",

    )


    value_fields = mo.ui.multiselect(

        options=numeric_columns,

        value=[c for c in ["value"] if c in numeric_columns],

        label="Value field(s)",

    )


    aggregation_method = mo.ui.dropdown(

        options=["sum", "mean", "count", "min", "max"],

        value="sum",

        label="Aggregation method",

    )


    mo.vstack(

        [

            row_dimensions,

            column_dimensions,

            value_fields,

            aggregation_method,

        ]

    )
    return aggregation_method, column_dimensions, row_dimensions, value_fields


@app.cell(hide_code=True)
def _(
    aggregation_method,
    build_summary_table,
    column_dimensions,
    filtered_df,
    pd,
    row_dimensions,
    value_fields,
):
    summary_table_df = build_summary_table(

        df=filtered_df,

        rows=row_dimensions.value,

        cols=column_dimensions.value,

        values=value_fields.value,

        aggfunc=aggregation_method.value,

        pd=pd,

    )
    return (summary_table_df,)


@app.cell(hide_code=True)
def _(filtered_df, mo, pd, summary_table_df):
    mo.vstack(

        [

            mo.md("### Summary table output"),

            summary_table_df if summary_table_df is not None and not summary_table_df.empty else pd.DataFrame({"info": ["No summary table output"]}),

            mo.md("### Underlying filtered data used for the table"),

            filtered_df.head(200) if filtered_df is not None and not filtered_df.empty else pd.DataFrame({"info": ["No filtered data available"]}),

        ]

    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 6. Ratio builder
    """)
    return


@app.cell(hide_code=True)
def _(filtered_df, mo, numeric_sorted_unique, safe_sorted_unique):
    if filtered_df is None or filtered_df.empty:
        ratio_metric_options = []
        ratio_group_options = []
        ratio_year_options = []
    else:
        ratio_metric_options = safe_sorted_unique(filtered_df.get("metric_name"))
        ratio_group_options = [
            c
            for c in [
                "year_clean",
                "quarter",
                "half_year",
                "period_type",
                "covertype",
                "source_file",
                "metric_source_table",
            ]
            if c in filtered_df.columns
        ]
        ratio_year_options = numeric_sorted_unique(filtered_df.get("year_clean"))

    ratio_name_input = mo.ui.text(
        value="Custom Ratio",
        label="Ratio name",
        placeholder="Enter a ratio name",
    )

    numerator_metrics_widget = mo.ui.multiselect(
        options=ratio_metric_options,
        value=[],
        label="Numerator metric(s)",
    )

    denominator_metrics_widget = mo.ui.multiselect(
        options=ratio_metric_options,
        value=[],
        label="Denominator metric(s)",
    )

    ratio_grouping = mo.ui.multiselect(
        options=ratio_group_options,
        value=[c for c in ["year_clean"] if c in ratio_group_options],
        label="Grouping columns",
    )

    ratio_aggregation = mo.ui.dropdown(
        options=["sum", "mean", "count", "min", "max"],
        value="sum",
        label="Aggregation for numerator / denominator",
    )

    ratio_years_widget = mo.ui.multiselect(
        options=ratio_year_options,
        value=ratio_year_options,
        label="Years to include in ratio calculation",
    )

    mo.vstack(
        [
            ratio_name_input,
            numerator_metrics_widget,
            denominator_metrics_widget,
            ratio_grouping,
            ratio_aggregation,
            ratio_years_widget,
        ]
    )

    return (
        denominator_metrics_widget,
        numerator_metrics_widget,
        ratio_aggregation,
        ratio_grouping,
        ratio_name_input,
        ratio_years_widget,
    )


@app.cell(hide_code=True)
def _(
    denominator_metrics_widget,
    filtered_df,
    numerator_metrics_widget,
    ratio_name_input,
    ratio_years_widget,
):
    effective_ratio_name = (
        ratio_name_input.value.strip()
        if ratio_name_input.value.strip()
        else "Custom Ratio"
    )

    effective_numerators = numerator_metrics_widget.value
    effective_denominators = denominator_metrics_widget.value

    if (
        filtered_df is not None
        and not filtered_df.empty
        and "year_clean" in filtered_df.columns
        and ratio_years_widget.value
    ):
        ratio_base_df = filtered_df[
            filtered_df["year_clean"].isin(ratio_years_widget.value)
        ].copy()
    else:
        ratio_base_df = filtered_df.copy()

    return (
        effective_denominators,
        effective_numerators,
        effective_ratio_name,
        ratio_base_df,
    )


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(
    build_ratio_table,
    effective_denominators,
    effective_numerators,
    effective_ratio_name,
    np,
    pd,
    ratio_aggregation,
    ratio_base_df,
    ratio_grouping,
):
    if not effective_numerators or not effective_denominators:
        ratio_table_df = pd.DataFrame(
            {
                "message": [
                    "Select at least one numerator metric and one denominator metric."
                ]
            }
        )
    else:
        ratio_table_df = build_ratio_table(
            df=ratio_base_df,
            ratio_name=effective_ratio_name,
            numerator_metrics=effective_numerators,
            denominator_metrics=effective_denominators,
            group_cols=ratio_grouping.value,
            aggfunc=ratio_aggregation.value,
            pd=pd,
            np=np,
        )

    ratio_table_df
    return (ratio_table_df,)


@app.cell(hide_code=True)
def _(
    effective_denominators,
    effective_numerators,
    effective_ratio_name,
    mo,
    pd,
    ratio_table_df,
):
    numerator_text = ", ".join(effective_numerators) if effective_numerators else "None selected"

    denominator_text = ", ".join(effective_denominators) if effective_denominators else "None selected"


    mo.vstack(

        [

            mo.md(f"### Ratio definition: **{effective_ratio_name}**"),

            mo.md(f"**Numerator:** {numerator_text}  \n**Denominator:** {denominator_text}"),

            ratio_table_df if ratio_table_df is not None and not ratio_table_df.empty else pd.DataFrame({"info": ["No ratio output"]}),

        ]

    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 7. Visualisations
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    chart_dataset_choice = mo.ui.dropdown(

        options=["Filtered data", "Summary table", "Ratio table"],

        value="Filtered data",

        label="Dataset to chart",

    )


    # Placeholder widgets are created here; available column lists are populated in the next cell.

    mo.vstack([chart_dataset_choice])
    return (chart_dataset_choice,)


@app.cell(hide_code=True)
def _(
    chart_dataset_choice,
    filtered_df,
    mo,
    pd,
    ratio_table_df,
    summary_table_df,
):
    if chart_dataset_choice.value == "Filtered data":
        chart_source_df = filtered_df.copy() if filtered_df is not None else pd.DataFrame()
    elif chart_dataset_choice.value == "Summary table":
        chart_source_df = summary_table_df.copy() if summary_table_df is not None else pd.DataFrame()
    else:
        chart_source_df = ratio_table_df.copy() if ratio_table_df is not None else pd.DataFrame()

    if chart_source_df is None or chart_source_df.empty:
        chart_all_columns = []
        chart_numeric_columns = []
    else:
        chart_all_columns = chart_source_df.columns.tolist()
        chart_numeric_columns = [
            c
            for c in chart_source_df.columns
            if pd.api.types.is_numeric_dtype(chart_source_df[c])
        ]

    x_axis = mo.ui.dropdown(
        options=chart_all_columns,
        value=chart_all_columns[0] if chart_all_columns else None,
        label="X-axis",
    )

    y_axis = mo.ui.dropdown(
        options=chart_numeric_columns,
        value=chart_numeric_columns[0] if chart_numeric_columns else None,
        label="Y-axis",
    )

    colour_by = mo.ui.dropdown(
        options=["None"] + chart_all_columns if chart_all_columns else ["None"],
        value="None",
        label="Colour / grouping",
    )

    chart_type = mo.ui.dropdown(
        options=["line", "bar", "point", "area"],
        value="line",
        label="Chart type",
    )

    chart_aggregation = mo.ui.dropdown(
        options=["sum", "mean", "count", "min", "max"],
        value="sum",
        label="Aggregation for chart",
    )

    mo.vstack(
        [
            chart_dataset_choice,
            x_axis,
            y_axis,
            colour_by,
            chart_type,
            chart_aggregation,
        ]
    )
    return (
        chart_aggregation,
        chart_source_df,
        chart_type,
        colour_by,
        x_axis,
        y_axis,
    )


@app.cell(hide_code=True)
def _(
    aggregate_for_chart,
    alt,
    chart_aggregation,
    chart_source_df,
    chart_type,
    colour_by,
    mo,
    pd,
    x_axis,
    y_axis,
):
    if (
        chart_source_df is None
        or chart_source_df.empty
        or x_axis.value is None
        or y_axis.value is None
    ):
        chart_df = pd.DataFrame({"info": ["No chartable data available"]})
        chart = None
    else:
        color_col = None if colour_by.value == "None" else colour_by.value

        chart_df = aggregate_for_chart(
            df=chart_source_df,
            x_col=x_axis.value,
            y_col=y_axis.value,
            color_col=color_col,
            aggfunc=chart_aggregation.value,
            pd=pd,
        )

        if chart_df is None or chart_df.empty:
            chart = None
        else:
            base = alt.Chart(chart_df).encode(
                x=alt.X(f"{x_axis.value}:N", title=x_axis.value),
                y=alt.Y(f"{y_axis.value}:Q", title=y_axis.value),
                tooltip=list(chart_df.columns),
            )

            if color_col and color_col in chart_df.columns:
                base = base.encode(color=alt.Color(f"{color_col}:N", title=color_col))

            if chart_type.value == "line":
                chart = base.mark_line(point=True)
            elif chart_type.value == "bar":
                chart = base.mark_bar()
            elif chart_type.value == "area":
                chart = base.mark_area(opacity=0.6)
            else:
                chart = base.mark_point(size=80)

            chart = chart.properties(width="container", height=400)

    mo.vstack(
        [
            mo.md("### Chart"),
            chart if chart is not None else mo.md("No chart to display yet."),
            mo.md("### Chart data"),
            chart_df,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 8. Debug / extended preview
    """)
    return


@app.cell(hide_code=True)
def _(master_analysis_df, pd):
    pd.DataFrame({"column_name": master_analysis_df.columns.tolist()}) if master_analysis_df is not None and not master_analysis_df.empty else pd.DataFrame({"column_name": []})
    return


if __name__ == "__main__":
    app.run()
