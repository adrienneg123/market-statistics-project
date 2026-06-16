# Market Statistics Project
(WIP to be removed m_s_jupyter is most up to date script and should split problem tabs like ult data.)
## Description

This project builds an end-to-end data pipeline for collecting, cleaning, and analysing insurance market statistics data.

It combines:
- A **Jupyter Notebook** for data extraction and transformation  
- A **Marimo application** for interactive analysis and ratio calculation  

The aim is to convert raw Excel data into a clean, consistent **tidy data format** and use it to perform actuarial-style analysis.

## Key Features
- Scrapes Excel files from webpage URLs  
- Accepts local Excel file paths as input  
- Converts raw data into tidy (long) format  
- Stores cleaned outputs in a structured folder  
- Combines multiple datasets into one master dataset  
- Interactive filtering using a year range slider  
- Calculates key actuarial ratios
