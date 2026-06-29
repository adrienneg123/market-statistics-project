# Market Statistics Data Pipeline and Analysis Toolkit

## Overview

This project is a Python-based workflow for extracting, tidying, analysing, and visualising market statistics data from Excel and CSV sources.

The repository was designed to support a structured market statistics workflow by:

- extracting tables from multi-sheet Excel workbooks,
- converting those tables into tidy analysis-ready CSV outputs,
- building a standardised master analysis dataset,
- enabling interactive filtering and summary analysis,
- calculating reusable ratios,
- and generating visualisations for exploratory analysis.

The overall aim of the project is to turn unstructured or inconsistently formatted market statistics files into a format that is easier to review, compare, and analyse using Python tools.

---

This repository contains two main components:

### Excel → CSV Processing Script

A robust Python pipeline that:

- Extracts Excel data from:
  - Webpages (automatically detects Excel links)
  - Local files
  - Folders of Excel files
- Outputs clean, analysis-ready CSV files

Each detected table is exported as a separate CSV inside:

tidy_outputs/

---

### Interactive Marimo Analysis App

An interactive notebook that enables:

- Uploading CSV files or selecting a folder of CSVs
- Interactive filtering
- Building custom ratios using selected metrics
- Creating interactive charts and tables

---

##  Workflow

Excel files → Processing script → Tidy CSVs → Marimo app → Interactive analysis

---

##  Installation

Install dependencies:

```
pip install pandas numpy requests beautifulsoup4 openpyxl marimo altair --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

---

##  Usage

### Step 1: Run the processing script

market_statistics_project_jupyter.ipynb

Choose one of the following:
1. Scrape Excel files from a webpage  
2. Use a local Excel file  
3. Use a folder of Excel files  

Processed outputs will be saved in:

tidy_outputs/

---

### Step 2: Launch the marimo app

```
marimo run market_statistics_project.py
```

---

### Step 3: Load data in the app


- Uploaded files → upload CSVs directly  


---

### Step 4: Analyse

Within the app you can:

- Filter the dataset  
- Build summary tables  
- Create custom ratios  
- Generate interactive visualisations  

---

## Project Structure
```
project/
├── market_statistics_project_jupyter.ipynb      # scrape & clean raw data
├── tidy_outputs/                                # processed CSVs for analysis
├── market_statistics_project.py                 # analysis + visualisation (marimo)
└── README.md                                    # project overview & instructions
```
---

