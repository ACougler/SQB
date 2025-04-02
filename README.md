# Search Query Generator (SQG)
## Overview
The Search Query Generator (SQG) is a Python-based tool designed to automate the creation of complex and reproducible search queries from structured CSV input.
It was originally developed to support research in Nexis Uni by generating large-scale search strings, but it has since been generalized to support any application that requires consistent, flexible, and logic-based query construction.

SQG allows users to define groups of search terms (such as platforms, phrases, or locations), configure how they should be quoted and logically connected (AND, OR, NOT), and produce search strings accordingly.
It supports both single combined queries and queries generated per category.

## Key Features

 - Read structured CSV input with multiple columns representing search term groups

 - Automatically detect CSV delimiters and encodings (e.g., utf-8, windows-1252)

 - Interactive CLI prompts for term quoting and logical operator settings

 * Generate:
   - A single, combined search query from all terms
   - One search query per unique value in a selected "main" column
 - Optional export of query metadata for reproducibility and tracking

# Input
Input is a wide-format CSV file, where each column represents a group of search terms.
These terms will be combined using the logical structure provided by the user.
# Output
```queries.txt```: List of queries, optionally labeled by group value. 

```metadata.csv```: (Optional) Summary of queries, useful for logging and reproducibility.

# How to use:
```python cli.py -i data/sample.csv -o output/queries.txt -m output/metadata.csv```