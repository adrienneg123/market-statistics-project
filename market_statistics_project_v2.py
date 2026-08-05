import marimo

__generated_with = "0.23.9"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import re
    import io
    import altair as alt

    return alt, io, mo, np, pd, re


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Insurance CSV Analysis App

    This app provides a simplified, upload-based workflow for analysing insurance CSV files.

    ## What this app does
    1. **User uploads one or more CSV files**
    2. **Standardises and combines the files into one master analysis dataframe**
    3. **Filters the combined data interactively**
    4. **Builds a ratio using selected numerator and denominator metrics**
    5. **Creates a chart from either the filtered data or the ratio output**

    ## How to use it
    - Start by uploading one or more CSV files in section **1**
    - Use the filters in section **2** to narrow down the combined dataset
    - Use section **3** to calculate a ratio from the filtered data
    - Use section **4** to create a visualisation
    """)
    return


@app.cell(hide_code=True)
def _(pd, re):
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


    def build_master_analysis_df(raw_df, np, pd, keep_debug_cols=False):
        """Build a standardised master analysis dataframe."""
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()

        df = raw_df.copy()

        noisy_cols = [c for c in ["yoy_change"] if c in df.columns]
        if noisy_cols:
            df = df.drop(columns=noisy_cols)

        expected_cols = [
            "measure",
            "variable",
            "value",
            "date",
            "year",
            "yearh",
            "accidentquarter",
            "covertype",
            "source_file",
        ]

        for c in expected_cols:
            if c not in df.columns:
                df[c] = np.nan

        for c in ["value", "date", "year", "accidentquarter"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        df["metric_name"] = (
            df["measure"].astype("string").replace("<NA>", pd.NA)
            .combine_first(df["variable"].astype("string").replace("<NA>", pd.NA))
        )

        df["metric_source_table"] = (
            df["source_file"]
            .astype("string")
            .fillna("unknown_source")
            .str.replace(".csv", "", regex=False)
        )

        derived_year_from_aq = df["accidentquarter"].apply(year_from_accidentquarter)
        year_from_year = pd.to_numeric(df["year"], errors="coerce")
        year_from_date = pd.to_numeric(df["date"], errors="coerce")

        df["year_clean"] = (
            year_from_year
            .combine_first(year_from_date)
            .combine_first(derived_year_from_aq)
        )

        df["year_clean"] = pd.to_numeric(df["year_clean"], errors="coerce").astype("Int64")

        df["quarter"] = df["accidentquarter"].apply(quarter_from_accidentquarter)
        df["half_year"] = df["yearh"].apply(parse_half_year)
        df["period_original"] = df.apply(build_period_original, axis=1)
        df["period_type"] = df.apply(infer_period_type, axis=1)

        df["covertype"] = (
            df["covertype"]
            .astype("string")
            .replace("<NA>", pd.NA)
            .fillna("All")
        )

        df["metric_category"] = df["metric_name"].apply(metric_category)

        df = df[~(df["metric_name"].isna() & df["value"].isna())].copy()

        core_cols = [
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
        ]

        debug_cols = [
            "measure",
            "variable",
            "year",
            "date",
            "yearh",
            "accidentquarter",
        ]

        if keep_debug_cols:
            final_cols = [c for c in core_cols + debug_cols if c in df.columns]
            other_cols = [c for c in df.columns if c not in final_cols]
            return df[final_cols + other_cols]

        final_cols = [c for c in core_cols if c in df.columns]
        return df[final_cols]


    def build_load_status(file_metadata_df, master_df, pd):
        """Build a compact status summary dataframe."""
        if file_metadata_df is None or file_metadata_df.empty:
            return pd.DataFrame(
                {
                    "status": ["No files loaded"],
                    "details": ["Upload one or more CSV files to begin."],
                }
            )

        total_rows = int(file_metadata_df["row_count"].sum()) if "row_count" in file_metadata_df.columns else 0
        total_files = len(file_metadata_df)

        summary_rows = [
            {"status": "Files loaded", "details": total_files},
            {"status": "Total rows loaded", "details": total_rows},
            {"status": "Master dataframe rows", "details": len(master_df) if master_df is not None else 0},
            {"status": "Master dataframe columns", "details": len(master_df.columns.tolist()) if master_df is not None else 0},
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
        source_files,
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

        if source_files and "source_file" in out.columns:
            out = out[out["source_file"].astype(str).isin(source_files)]

        if metric_names and "metric_name" in out.columns:
            out = out[out["metric_name"].astype(str).isin(metric_names)]

        return out


    def build_ratio_table(
        df,
        ratio_name,
        numerator_metrics,
        denominator_metrics,
        group_cols,
        decimal_places,
        pd,
        np,
    ):
        """Build a ratio table using sum(numerator) / sum(denominator)."""
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
                .sum()
                .reset_index(name="numerator_value")
            )
            denominator = (
                den_df.groupby(valid_group_cols, dropna=False)["value"]
                .sum()
                .reset_index(name="denominator_value")
            )
            ratio_df = numerator.merge(denominator, on=valid_group_cols, how="outer")
        else:
            ratio_df = pd.DataFrame(
                {
                    "numerator_value": [num_df["value"].sum()],
                    "denominator_value": [den_df["value"].sum()],
                }
            )

        ratio_df["numerator_value"] = pd.to_numeric(ratio_df["numerator_value"], errors="coerce")
        ratio_df["denominator_value"] = pd.to_numeric(ratio_df["denominator_value"], errors="coerce")

        ratio_df[ratio_name] = np.where(
            ratio_df["denominator_value"].fillna(0) == 0,
            np.nan,
            ratio_df["numerator_value"] / ratio_df["denominator_value"],
        )

        ratio_df[ratio_name] = pd.to_numeric(
            ratio_df[ratio_name], errors="coerce"
        ).round(decimal_places)

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
        numeric_sorted_unique,
        safe_read_csv_from_upload,
        safe_sorted_unique,
        standardise_columns,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 1. Upload and prepare your CSV files

    Use the upload box below to add **one or more CSV files**.

    After upload, the app will:
    - read each file
    - standardise column names
    - combine them into a single master analysis dataframe

    If a file cannot be read, it will be skipped and the error will be shown below.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    file_input = mo.ui.file(
        multiple=True,
        filetypes=[".csv"],
        label="Upload one or more CSV files",
    )

    mo.vstack([file_input])
    return (file_input,)


@app.cell(hide_code=True)
def _(
    align_schemas,
    build_load_status,
    build_master_analysis_df,
    file_input,
    io,
    np,
    pd,
    safe_read_csv_from_upload,
    standardise_columns,
):
    uploaded_files = list(file_input.value) if file_input.value else []

    loaded_dfs = []
    load_errors = []
    file_metadata = []

    if uploaded_files:
        for file_obj in uploaded_files:
            df, err = safe_read_csv_from_upload(file_obj, pd, io)

            if err:
                load_errors.append(err)
                continue

            df = standardise_columns(df)

            source_name = getattr(file_obj, "name", "uploaded_file.csv")
            df["source_file"] = source_name

            loaded_dfs.append(df)

            file_metadata.append(
                {
                    "source_file": source_name,
                    "row_count": len(df),
                    "column_count": len(df.columns),
                    "load_source": "upload",
                }
            )
    else:
        load_errors.append("No files uploaded.")

    if loaded_dfs:
        aligned_dfs = align_schemas(loaded_dfs, np)
        master_raw_df = pd.concat(aligned_dfs, ignore_index=True)
        master_analysis_df = build_master_analysis_df(master_raw_df, np, pd)
    else:
        master_raw_df = pd.DataFrame()
        master_analysis_df = pd.DataFrame()

    file_metadata_df = pd.DataFrame(file_metadata)
    load_status_df = build_load_status(file_metadata_df, master_analysis_df, pd)
    return (master_analysis_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 2. Filter the combined data

    Use these filters to narrow down the uploaded data before building ratios or charts.

    ### What each filter means
    - **Year range**: limits the data to a selected span of years
    - **Period type**: filters by the reporting format, such as annual, quarterly, or half-yearly
    - **Source file**: lets you isolate values from specific uploaded CSV files
    - **Metric name**: the individual metric label used for actual analysis and ratio building

    A common approach is to start broad, then narrow down by **metric name**.
    """)
    return


@app.cell(hide_code=True)
def _(master_analysis_df, mo, numeric_sorted_unique, safe_sorted_unique):
    if master_analysis_df is None or master_analysis_df.empty:
        years = []
        period_types = []
        source_files = []
    else:
        years = numeric_sorted_unique(master_analysis_df.get("year_clean"))
        period_types = safe_sorted_unique(master_analysis_df.get("period_type"))
        source_files = safe_sorted_unique(master_analysis_df.get("source_file"))

    if years:
        yr_min, yr_max = min(years), max(years)
        year_range = mo.ui.range_slider(
            start=yr_min,
            stop=yr_max,
            value=(yr_min, yr_max),
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

    source_file_filter = mo.ui.multiselect(
        options=source_files,
        value=source_files,
        label="Source file",
    )

    mo.vstack(
        [
            year_range,
            period_type_filter,
            source_file_filter,
        ]
    )
    return period_type_filter, source_file_filter, year_range


@app.cell(hide_code=True)
def _(master_analysis_df, mo, safe_sorted_unique, source_file_filter):
    if (
        master_analysis_df is None
        or master_analysis_df.empty
        or "metric_name" not in master_analysis_df.columns
    ):
        metric_names = []
    else:
        selected_sources = source_file_filter.value

        if selected_sources and "source_file" in master_analysis_df.columns:
            source_subset_df = master_analysis_df[
                master_analysis_df["source_file"].astype(str).isin(selected_sources)
            ]
        else:
            source_subset_df = master_analysis_df

        metric_names = safe_sorted_unique(source_subset_df.get("metric_name"))

    metric_name_filter = mo.ui.multiselect(
        options=metric_names,
        value=metric_names,
        label="Metric name",
    )

    metric_name_filter
    return (metric_name_filter,)


@app.cell(hide_code=True)
def _(
    apply_filters,
    master_analysis_df,
    metric_name_filter,
    period_type_filter,
    source_file_filter,
    year_range,
):
    _ = master_analysis_df  # dependency

    if master_analysis_df is None or master_analysis_df.empty:
        filtered_df = master_analysis_df.copy()
    else:
        yr_val = getattr(year_range, "value", None)
        if isinstance(yr_val, (tuple, list)) and len(yr_val) == 2:
            year_range_value = yr_val
        else:
            year_range_value = None

        filtered_df = apply_filters(
            master_analysis_df,
            year_range_value=year_range_value,
            period_types=period_type_filter.value,
            source_files=source_file_filter.value,
            metric_names=metric_name_filter.value,
        )
    return (filtered_df,)


@app.cell(hide_code=True)
def _(mo):
    preview_row_mode = mo.ui.dropdown(
        options=["First N rows", "All rows"],
        value="First N rows",
        label="Filtered table display",
    )

    preview_row_limit = mo.ui.number(
        start=10,
        stop=10000,
        step=10,
        value=100,
        label="Number of rows to show",
    )

    mo.vstack([
        preview_row_mode,
        preview_row_limit,
    ])
    return preview_row_limit, preview_row_mode


@app.cell(hide_code=True)
def _(filtered_df, mo, pd, preview_row_limit, preview_row_mode):
    filtered_preview_cols = [
        "year_clean",
        "quarter",
        "half_year",
        "period_type",
        "metric_name",
        "source_file",
        "value",
    ]

    if filtered_df is not None and not filtered_df.empty:
        filtered_display_df = filtered_df.copy()

        if "year_clean" in filtered_display_df.columns:
            filtered_display_df["year_clean"] = filtered_display_df["year_clean"].apply(
                lambda x: str(int(x)) if pd.notna(x) else None
            )

        filtered_cols_to_show = [
            c for c in filtered_preview_cols if c in filtered_display_df.columns
        ]

        row_limit = (
            int(preview_row_limit.value)
            if preview_row_limit.value is not None
            else 100
        )

        if preview_row_mode.value == "All rows":
            filtered_preview_df = filtered_display_df[filtered_cols_to_show]
        else:
            filtered_preview_df = filtered_display_df[filtered_cols_to_show].head(row_limit)

        shown_count = len(filtered_preview_df)
        total_count = len(filtered_df)

        filtered_row_text = (
            f"### Filtered data rows shown: **{shown_count:,}** of **{total_count:,}**"
        )
    else:
        filtered_preview_df = pd.DataFrame({"info": ["No filtered rows"]})
        filtered_row_text = "No filtered data"

    mo.vstack(
        [
            mo.md(filtered_row_text),
            filtered_preview_df,
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. Ratio builder

    This section lets you build a ratio from the **currently filtered data**.

    ### How it works
    - **Ratio name**: the label that will appear in the output table
    - **Numerator metric(s)**: the metric or metrics to add together for the top of the ratio
    - **Denominator metric(s)**: the metric or metrics to add together for the bottom of the ratio
    - **Calculation view**: controls whether the ratio is calculated overall or split by time period / source columns
    - **Decimal places**: select to how many decimal places the ratio calculations are displayed
    - **Years to include**: gives you a final year-level check before calculating the ratio

    The ratio is calculated as:

    **sum(selected numerator values) / sum(selected denominator values)**
    """)
    return


@app.cell(hide_code=True)
def _(filtered_df, mo, numeric_sorted_unique, safe_sorted_unique):
    if filtered_df is None or filtered_df.empty:
        ratio_metric_options = []
        ratio_year_options = []
        calculation_view_options = ["Overall"]
    else:
        ratio_metric_options = (
            safe_sorted_unique(filtered_df["metric_name"])
            if "metric_name" in filtered_df.columns else []
        )
        ratio_year_options = (
            numeric_sorted_unique(filtered_df["year_clean"])
            if "year_clean" in filtered_df.columns else []
        )

        calculation_view_options = ["Overall"]
        for option in [
            "year_clean", 
            "quarter",
            "half_year",
            "period_type",
            "source_file",
            "metric_source_table",
        ]:
            if option in filtered_df.columns:
                calculation_view_options.append(option)

    ratio_name_input = mo.ui.text(
        value="Custom Ratio",
        label="Ratio name",
        placeholder="Enter a ratio name",
    )

    ratio_decimal_places = mo.ui.number(
        start=0,
        stop=6,
        step=1,
        value=2,
        label="Decimal places",
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

    calculation_view = mo.ui.dropdown(
        options=calculation_view_options,
        value=calculation_view_options[0] if calculation_view_options else "Overall",
        label="Calculation view",
    )

    if ratio_year_options:
        ratio_year_min, ratio_year_max = min(ratio_year_options), max(ratio_year_options)
        ratio_year_range = mo.ui.range_slider(
            start=ratio_year_min,
            stop=ratio_year_max,
            value=(ratio_year_min, ratio_year_max),
            label="Years to include",
        )
    else:
        ratio_year_range = mo.ui.text(
            value="No valid years found",
            label="Years unavailable",
            disabled=True,
        )

    ratio_ui = mo.vstack(
        [
            ratio_name_input,
            numerator_metrics_widget,
            denominator_metrics_widget,
            calculation_view,
            ratio_decimal_places,
            ratio_year_range,
        ]
    )

    ratio_ui
    return (
        calculation_view,
        denominator_metrics_widget,
        numerator_metrics_widget,
        ratio_decimal_places,
        ratio_name_input,
        ratio_year_range,
    )


@app.cell(hide_code=True)
def _(
    calculation_view,
    denominator_metrics_widget,
    filtered_df,
    numerator_metrics_widget,
    pd,
    ratio_decimal_places,
    ratio_name_input,
    ratio_year_range,
):
    effective_decimal_places = max(0, int(ratio_decimal_places.value or 2))

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
    ):
        ratio_year_value = getattr(ratio_year_range, "value", None)

        if (
            isinstance(ratio_year_value, (tuple, list))
            and len(ratio_year_value) == 2
        ):
            ratio_year_lo, ratio_year_hi = ratio_year_value
            ratio_base_df = filtered_df[
                pd.to_numeric(filtered_df["year_clean"], errors="coerce").between(
                    ratio_year_lo, ratio_year_hi, inclusive="both"
                )
            ].copy()
        else:
            ratio_base_df = filtered_df.copy()
    else:
        ratio_base_df = filtered_df.copy()

    if calculation_view.value == "Overall":
        ratio_group_cols = []
    else:
        ratio_group_cols = [calculation_view.value]
    return (
        effective_decimal_places,
        effective_denominators,
        effective_numerators,
        effective_ratio_name,
        ratio_base_df,
        ratio_group_cols,
    )


@app.cell(hide_code=True)
def _(
    build_ratio_table,
    effective_decimal_places,
    effective_denominators,
    effective_numerators,
    effective_ratio_name,
    np,
    pd,
    ratio_base_df,
    ratio_group_cols,
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
            group_cols=ratio_group_cols,
            decimal_places=effective_decimal_places,
            pd=pd,
            np=np,
        )

    ratio_table_display_df = ratio_table_df.copy()

    if "year_clean" in ratio_table_display_df.columns:
        ratio_table_display_df["year_clean"] = ratio_table_display_df["year_clean"].apply(
            lambda x: str(int(x)) if pd.notna(x) else None
        )

    ratio_table_display_df
    return (ratio_table_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## 4. Visualisations

    Use this section to create a chart from either:
    - **Filtered data**: the dataset produced by selected filters
    - **Ratio table**: the table produced by the ratio builder

    ### What each chart option means
    - **Dataset to chart**: chooses which table the chart is built from
    - **X-axis**: the field shown along the bottom of the chart
    - **Y-axis**: the numeric field being plotted
    - **Colour / grouping**: optionally splits the chart by an additional category
    - **Chart type**: changes the visual style (line, bar, point, area)
    - **Aggregation for chart**: controls how numeric values are combined before plotting

    ### Altair Features
    - This chart is rendered using Altair, enabling interactive exploration of the data
    - Users can highlight specific data points or categories by dragging their mouse over an area of interest
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    chart_dataset_choice = mo.ui.dropdown(
        options=["Filtered data", "Ratio table"],
        value="Filtered data",
        label="Dataset to chart",
    )
    return (chart_dataset_choice,)


@app.cell(hide_code=True)
def _(chart_dataset_choice, filtered_df, mo, pd, ratio_table_df):
    if chart_dataset_choice.value == "Filtered data":
        chart_source_df = filtered_df.copy() if filtered_df is not None else pd.DataFrame()
    else:
        chart_source_df = ratio_table_df.copy() if ratio_table_df is not None else pd.DataFrame()

    if chart_source_df is None or chart_source_df.empty:
        chart_x_options = []
        chart_colour_options = ["None"]
        chart_numeric_columns = []
    else:
        if chart_dataset_choice.value == "Filtered data":
            preferred_x = [
                "year_clean",
                "quarter",
                "half_year",
                "period_type",
                "source_file",
                "metric_name",
            ]
            chart_x_options = [c for c in preferred_x if c in chart_source_df.columns]
            chart_colour_options = ["None"] + chart_x_options
            chart_numeric_columns = ["value"] if "value" in chart_source_df.columns else []
        else:
            all_columns = [c for c in chart_source_df.columns if c != "message"]
            chart_x_options = all_columns
            chart_colour_options = ["None"] + all_columns
            chart_numeric_columns = [
                c for c in chart_source_df.columns
                if pd.api.types.is_numeric_dtype(chart_source_df[c]) and c != "message"
            ]

    x_axis = mo.ui.dropdown(
        options=chart_x_options,
        value=chart_x_options[0] if chart_x_options else None,
        label="X-axis",
    )

    default_y_axis = "value" if "value" in chart_numeric_columns else (
        chart_numeric_columns[0] if chart_numeric_columns else None
    )

    y_axis = mo.ui.dropdown(
        options=chart_numeric_columns,
        value=default_y_axis,
        label="Y-axis",
    )

    default_colour_by = "metric_name" if "metric_name" in chart_colour_options else "None"

    colour_by = mo.ui.dropdown(
        options=chart_colour_options,
        value=default_colour_by,
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
    chart_dataset_choice,
    chart_source_df,
    colour_by,
    mo,
    safe_sorted_unique,
    x_axis,
):
    if chart_dataset_choice.value == "Filtered data":
        element_filter_col = colour_by.value if colour_by.value != "None" else x_axis.value
    else:
        element_filter_col = None

    if(
        element_filter_col
        and chart_source_df is not None
        and not chart_source_df.empty
        and element_filter_col in chart_source_df.columns
    ):
        element_filter_options = safe_sorted_unique(chart_source_df[element_filter_col])
    else:
        element_filter_options = []

    element_filter = mo.ui.multiselect(
        options = element_filter_options,
        value = element_filter_options,
        label=(
            f"Elements to display ({element_filter_col})"
            if element_filter_col
            else "Elements to display"
        ),
    )

    if chart_dataset_choice.value == "Filtered data" and element_filter_options:
        element_filter_ui = mo.vstack(
            [
                mo.md(
                    "### Filter which elements appear on the chart\n"
                    "Narrow down which of the currently filtered values are actually plotted."
                ),
                element_filter,
            ]
        )
    else:
        element_filter_ui = mo.md("")

    element_filter_ui
    return element_filter, element_filter_col


@app.cell(hide_code=True)
def _(
    aggregate_for_chart,
    alt,
    chart_aggregation,
    chart_dataset_choice,
    chart_source_df,
    chart_type,
    colour_by,
    element_filter,
    element_filter_col,
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

        chart_input_df = chart_source_df

        if(
            chart_dataset_choice.value == "Filtered data"
            and element_filter_col in chart_input_df.columns
        ):
            chart_input_df = chart_input_df[
                chart_input_df[element_filter_col].astype(str).isin(element_filter.value)
            ]

        chart_df = aggregate_for_chart(
            df=chart_input_df,
            x_col=x_axis.value,
            y_col=y_axis.value,
            color_col=color_col,
            aggfunc=chart_aggregation.value,
            pd=pd,
        )

        if chart_df is None or chart_df.empty:
            chart = None
        else:
            if x_axis.value in ["year_clean", "quarter", "half_year"]:
                x_encoding = alt.X(f"{x_axis.value}:O", title=x_axis.value)
            else:
                x_encoding = alt.X(f"{x_axis.value}:N", title=x_axis.value)

            brush = alt.selection_interval()

            base = (
                alt.Chart(chart_df)
                .encode(
                    x=x_encoding,
                    y=alt.Y(f"{y_axis.value}:Q", title=y_axis.value),
                    tooltip=list(chart_df.columns),
                )
                .add_params(brush)
            )

            if color_col and color_col in chart_df.columns:
                base = base.encode(color=alt.Color(f"{color_col}:N", title=color_col))

            if chart_type.value == "line":
                chart = base.mark_line(point=alt.OverlayMarkDef(size=100)).encode(
                    opacity=alt.condition(brush, alt.value(1), alt.value(0.2))
                )
            elif chart_type.value == "bar":
                chart = base.mark_bar().encode(
                    opacity=alt.condition(brush, alt.value(1), alt.value(0.4))
                )
            elif chart_type.value == "area":
                chart = base.mark_area(opacity=0.6).encode(
                    opacity=alt.condition(brush, alt.value(0.8), alt.value(0.2))
                )
            else:
                chart = base.mark_point(size=100).encode(
                    opacity=alt.condition(brush, alt.value(1), alt.value(0.2))
                )

            chart = chart.properties(width="container", height=400)
            chart = mo.ui.altair_chart(chart)

    chart_display_df = chart_df.copy()

    if "year_clean" in chart_display_df.columns:
        chart_display_df["year_clean"] = chart_display_df["year_clean"].apply(
            lambda x: str(int(x)) if pd.notna(x) else None
        )

    mo.vstack(
        [
            mo.md("### Chart"),
            chart if chart is not None else mo.md("No chart to display yet."),
            mo.md("### Chart data"),
            chart_display_df,
        ]
    )
    return (chart,)


@app.cell(hide_code=True)
def _(chart):
    if chart is not None and hasattr(chart, 'value'):
        selected_chart_data = chart.value
    else:
        selected_chart_data = None

    selected_chart_data
    return


if __name__ == "__main__":
    app.run()
