# Market Statistics Data Pipeline and Analysis Toolkit

## Overview

This project is a Python-based workflow for extracting, tidying, analysing, and visualising market statistics data from Excel and CSV sources.

The repository was designed to support a structured market statistics workflow by:

- extracting tables from messy multi-sheet Excel workbooks,
- converting those tables into tidy analysis-ready CSV outputs,
- harmonising schemas across multiple files,
- building a standardised master analysis dataset,
- enabling interactive filtering and summary analysis,
- calculating reusable ratios,
- and generating visualisations for exploratory analysis.

The overall aim of the project is to turn unstructured or inconsistently formatted market statistics files into a format that is easier to review, compare, and analyse using Python tools.

---

## Key Features

### 1. Excel extraction and tidying
The Jupyter-based script processes Excel files from multiple sources:
- a webpage containing Excel links,
- a single local Excel file,
- or a local folder of Excel files.

It includes logic to:
- detect headers in messy worksheets,
- identify year/date/period structures,
- recognise already-long versus wide-form tables,
- remove title/footer noise,
- split sheets into separate tables,
- and export tidy CSV outputs.

A fallback workflow is also included for more difficult sheet layouts, such as:
- multiple tables on one sheet,
- blank-row/blank-column separated blocks,
- horizontally merged tables,
- embedded section headings,
- and irregular header structures.

### 2. Tidy output generation
Processed outputs are saved into a `tidy_outputs/` folder as CSV files.  
A processing log is also created so that each sheet or detected table can be tracked by:
- source file,
- sheet name,
- table index,
- processing method,
- and save/skipped status.

### 3. Master analysis dataset
The main Marimo application loads one or more tidy CSV files and builds a standardised **master analysis dataframe**.

This includes:
- schema harmonisation across files,
- standardised column naming,
- derived time fields,
- metric naming logic,
- metric categorisation,
- source lineage fields,
- and a simplified analysis-ready structure.

### 4. Interactive filtering and table building
The Marimo app provides a reactive interface for:
- filtering by year range,
- period type,
- cover type,
- source file,
- metric category,
- and metric name.

Users can then generate custom summary tables using flexible row, column, value, and aggregation selections.

### 5. Generic ratio engine
The analysis workflow includes a reusable ratio builder that allows the user to:
- choose numerator metric(s),
- choose denominator metric(s),
- define grouping columns,
- and calculate ratios using a selected aggregation method.

This makes it easier to explore metrics without hardcoding one-off calculations throughout the notebook.

### 6. Interactive visualisation
Two visualisation layers are included:

- **Altair-based charting** in the main Marimo app for charting filtered, summary, or ratio datasets
- **Plotly-based quick charting** in a lightweight Marimo app for fast CSV exploration

The plotting tools support:
- configurable x/y axes,
- optional grouping/colour dimensions,
- automatic aggregation when duplicate groups exist,
- and faceting behaviour for measures with different scales.

---

## Repository Structure

```text
project-root/
│
├── market_statistics_project.ipynb
│   Jupyter workflow for extracting tables from raw Excel files and exporting tidy CSVs.
│
├── marimo_market_statistics_project.py
│   Main interactive Marimo app for loading tidy CSVs, building a master analysis
│   dataframe, filtering data, creating summary tables, calculating ratios, and charting.
│
├── market_statistics_project_plotly.py
│   Lightweight Marimo app for quick visual exploration of a single CSV file using Plotly.
│
└── tidy_outputs/
    Output folder containing generated tidy CSV files and processing_log.csv.
