# PaperImpact: A Comprehensive System for Analyzing the Impact of Scientific Publications

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

This project provides a robust and comprehensive system for analyzing the impact of scientific publications, primarily focusing on journal quality, citation metrics, recency, and international collaboration.  It leverages data from the SCImago Journal Rank (SJR) database and individual paper metadata (typically sourced from Scopus or similar databases) to calculate a normalized impact score for each paper.  The analyzer then aggregates these scores to provide insights at the country and journal levels, including comparative analyses and visualizations.  The goal is to provide a nuanced, multi-faceted view of research impact that goes beyond simple citation counts.

## Quick Start

1.  **Install dependencies:** `pip install -r requirements.txt`
2.  **Place SCImago data (e.g., `scimagojr 2023.csv`) in the `data` directory.**
3.  **Place paper data files (e.g., `australia_papers.csv`) in the `data/papers` directory.**
4.  **Run the analysis:** `python src/run_analysis.py`
5.  **Find results in the `results` directory.**

## Table of Contents

1.  [Features](#features)
2.  [Project Structure](#project-structure)
3.  [Installation and Setup](#installation-and-setup)
4.  [Input Data](#input-data)
    *   [SCImago Data](#scimago-data)
    *   [Papers Data](#papers-data)
5.  [Data Availability](#data-availability)
6.  [Methodology](#methodology)
    *   [Journal Impact](#journal-impact)
    *   [Citation Impact](#citation-impact)
    *   [Recency](#recency)
    *   [International Collaboration](#international-collaboration)
    *   [Normalization](#normalization)
    *   [Impact Tiers](#impact-tiers)
7.  [Usage](#usage)
    *   [Command-Line Arguments](#command-line-arguments)
    *   [Running the Analysis](#running-the-analysis)
8.  [Configuration](#configuration)
9.  [Output](#output)
    *   [Detailed Results (CSV)](#detailed-results-csv)
    *   [Analysis Report](#analysis-report)
    *   [Visualizations](#visualizations)
10. [Logging](#logging)
11. [Extensibility and Customization](#extensibility-and-customization)
12. [Troubleshooting](#troubleshooting)
13. [Future Enhancements](#future-enhancements)
14. [License](#license)
15. [Contributing](#contributing)
16. [Code of Conduct](#code-of-conduct)
17. [Security](#security)
18. [Acknowledgements](#acknowledgements)
19. [Citation](#citation)

## Features

*   **Comprehensive Impact Score:** Calculates a normalized impact score for each paper, considering multiple factors.
*   **Journal Matching:** Accurately matches paper data to SCImago journal entries using title and ISSN, with robust handling of variations and inconsistencies.
*   **Country-Level Analysis:** Aggregates results to provide insights into research performance by country.
*   **Comparative Analysis:** Generates reports and visualizations comparing research impact across multiple countries.
*   **Journal-Level Analysis:** Provides statistics on the distribution of publications across different journal quality tiers (SCImago quartiles).
*   **Detailed Reporting:** Produces comprehensive reports with key metrics, including average impact scores, publication volume, collaboration rates, and journal quality distributions.
*   **Visualizations:** Creates informative charts (using Matplotlib) to visualize impact score distributions, publication volume, collaboration rates, and journal quality.
*   **Global Reference Points:** Identifies the globally most cited paper and the highest-ranked journal across all input data.
*   **Extensible Design:**  The codebase is structured for easy modification and extension, allowing for the incorporation of new metrics or data sources.
*   **Robust Error Handling:** Includes extensive error handling and validation to ensure data integrity and prevent crashes.
*   **Detailed Logging:** Uses a custom logger (`PrettyLogger`) to provide clear and informative output during processing, including progress updates, warnings, and error messages.

## Project Structure

```
├── .gitignore                  # Specifies intentionally untracked files
├── LICENSE                     # MIT License file
├── README.md                   # This file
├── requirements.txt            # Project dependencies
├── data/                       # (Should contain) Input data files
│   └── scimagojr 2023.csv      # SCImago journal data (example filename)
│   └── papers/                 # (Should contain) Directory for paper CSV files
│       └── *_papers.csv        # Paper data files for each country
├── results/                    # (Will contain) Output directory
│   ├── comparative_analysis_*.csv  # Comparative analysis reports
│   ├── australia/              # (Example) Country-specific results
│   │   └── impact_scores.csv   # Detailed impact scores for Australia
│   ├── ...                     # Other country directories
│   ├── impact_scores.png       # Visualization of impact scores
│   ├── publication_volume.png  # Visualization of publication volume
│   ├── international_collab.png # Visualization of international collaboration
│   ├── average_citations.png   # Visualization of average citations
    └── journal_quality.png     # Visualization of journal quality distribution
└── src/
    ├── __init__.py             # Empty file to make 'src' a package
    ├── logger.py               # Custom logging class (PrettyLogger)
    └── impact_scorer.py        # (Unused) older scoring class.
└── run_analysis.py             # Main script for analysis
```

## Installation and Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/alpha912/PaperImpact
    cd PaperImpact
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Input Data

The analyzer requires two main types of input data:

### SCImago Data

*   **File:** `scimagojr 2023.csv` (or similar, specified via the `--scimago` argument)
*   **Source:**  SCImago Journal & Country Rank ([https://www.scimagojr.com/](https://www.scimagojr.com/))
*   **Format:** CSV file.  The script automatically detects the separator, but it should ideally be a standard CSV format.
*   **Required Columns:**
    *   `Title`: Journal title.
    *   `SJR`: SCImago Journal Rank indicator (as a string, may contain commas).
    *   `H index`: H-index of the journal.
    *   `Issn`:  Journal ISSN (can be used for more precise matching).
    *   `SJR Best Quartile`: Journal quartile (Q1, Q2, Q3, Q4).
    *   `Rank`: Numerical rank of the journal.

*   **Preprocessing:** The script handles the following preprocessing steps:
    *   Converts the `SJR` column to numeric, handling commas as decimal separators and filling missing values with 0.
    *   Converts the `H index` column to numeric, filling missing values with 0.
    *   Creates a `clean_title` column by converting journal titles to lowercase and stripping whitespace. This is used for more robust matching.

### Papers Data

*   **Files:**  One or more CSV files located in the `data/papers` directory (or specified via the `--papers_dir` argument).  Each file should represent data for a specific country and be named `[country]_papers.csv` (e.g., `australia_papers.csv`).
*   **Source:**  Typically Scopus, Web of Science, or a similar bibliographic database.
*   **Format:** CSV file (UTF-8 encoding).
*   **Required Columns:** The script attempts to map the following columns, handling variations in naming:
    *   `Source title` or `journal_title`:  The title of the journal where the paper was published.
    *   `ISSN`:  The ISSN of the journal (optional, but recommended for accurate matching).
    *   `Year` or `year`:  The year of publication.
    *   `Cited by` or `citation_count`: The number of citations the paper has received.
    *   `Affiliations`:  A string containing affiliation information, typically semicolon-separated.  Used to determine international collaboration.
    *   `Title`: The title of the paper.
    *   `DOI`: The DOI of the paper.
    *   `Authors`: The authors of the paper.
    *   `Publisher`: The publisher of the journal.
    *   `Open Access`: Information about the open access status of the paper.
    *   `Document Type`: The type of document (e.g., article, review).

*   **Preprocessing:**
    *   Renames columns to a standardized set (`journal_title`, `year`, `citation_count`, `affiliations`, etc.).
    *   Converts `year` to numeric, coercing errors and removing rows with invalid years (outside the range 1900-current year).
    *   Converts `citation_count` to numeric, filling missing values with 0.
    *   Calculates `international_collab` based on the `affiliations` column.  A paper is considered an international collaboration if the affiliations represent multiple countries.

## Data Availability

*   **SCImago Data:**  Download the CSV data directly from the SCImago Journal & Country Rank website ([https://www.scimagojr.com/](https://www.scimagojr.com/)).  You will need to select the desired year and download the data as a CSV file.
*   **Papers Data:** This data must be obtained from a bibliographic database such as Scopus ([https://www.scopus.com/](https://www.scopus.com/)) or Web of Science ([https://www.webofscience.com/](https://www.webofscience.com/)).  These databases typically require a subscription.  You will need to perform a search based on your criteria (e.g., country, research area, publication years) and export the results in CSV format.  Ensure that the exported data includes the required columns listed above.  *It is crucial to export the data in a consistent format for each country.*

    *   **Simulating Data (for testing):** If you do not have access to Scopus or Web of Science, you can create simulated data for testing purposes.  Create CSV files with the required columns and populate them with realistic data.  For example, you can generate random citation counts, publication years, and affiliation strings.  However, keep in mind that simulated data will not provide accurate results.

## Methodology

The impact score calculation is based on four key factors:

### Journal Impact (30% of total score)

This component reflects the prestige and influence of the journal in which the paper is published. It is calculated using the SCImago Journal Rank (SJR) and the H-index.

*   **SJR Score (20%):**  The SJR is a measure of a journal's influence, considering both the number of citations received and the importance of the citing journals.  The raw SJR value is normalized by dividing it by the maximum SJR value in the SCImago dataset and then multiplied by 20.
*   **H-index (10%):** The H-index is a measure of a journal's productivity and impact.  It represents the number of papers (h) that have been cited at least h times. The raw H-index is normalized by dividing it by the maximum H-index in the SCImago dataset and then multiplied by 10.

The formula for journal impact is:

```latex
Journal\ Impact = \left(\frac{SJR}{max(SJR)} \times 20\right) + \left(\frac{H-index}{max(H-index)} \times 10\right)
```

### Citation Impact (30% of total score)

This component reflects the impact of the individual paper, based on the number of times it has been cited.  A logarithmic transformation is applied to the citation count to reduce the influence of extremely highly cited papers.

*   **Formula:**

    ```latex
    Citation\ Impact = \left(\frac{log1p(citation\_count)}{log1p(global\_max\_citations)}\right) \times 30
    ```

    where `global_max_citations` is the highest citation count across *all* papers in the dataset (determined during the `find_global_reference_points` step).  `log1p(x)` calculates `log(1 + x)`, which handles zero values gracefully.

### Recency (15% of total score)

This component gives higher scores to more recent publications, reflecting the idea that recent research is often more relevant.  An exponential decay function is used to model the decreasing importance of older papers.

*   **Formula:**

    ```latex
    Recency = exp(-0.1 \times years\_diff) \times 15
    ```

    where `years_diff` is the difference between the current year and the paper's publication year.  The constant `0.1` controls the rate of decay.

### International Collaboration (10% of total score)

This component rewards papers that result from international collaborations, as these are often associated with higher impact.

*   **Calculation:** The script analyzes the `Affiliations` field of each paper. If the affiliations represent institutions from multiple countries, the paper is considered an international collaboration and receives a score of 10. Otherwise, it receives a score of 0.  The country is extracted by splitting the affiliation string by commas and taking the last element.

### Normalization

After calculating the individual components, the total impact score is calculated as the sum of the weighted components:

```latex
Total\ Impact\ Score = (Journal\ Impact \times 0.30) + (Citation\ Impact \times 0.30) + (Recency \times 0.15) + (Collaboration \times 0.10)
```

The total impact scores are then normalized to a 0-100 scale:

```latex
Normalized\ Impact\ Score = \left(\frac{Total\ Impact\ Score}{max(Total\ Impact\ Score)}\right) \times 100
```

This normalization ensures that scores are comparable across different datasets and that the highest-scoring paper always receives a score of 100.

### Impact Tiers

Papers are assigned to impact tiers based on their normalized impact scores:

*   **Very Low:** 0-20
*   **Low:** 20-40
*   **Medium:** 40-60
*   **High:** 60-80
*   **Very High:** 80-100

## Usage

### Command-Line Arguments

The script is run from the command line using `run_analysis.py`. It accepts the following arguments:

*   `--papers_dir`:  Path to the directory containing the paper CSV files.  Defaults to `data/papers`.
*   `--scimago`: Path to the SCImago journal rankings CSV file. Defaults to `data/scimagojr 2023.csv`.
*   `--output`:  Path to the output directory where results will be saved. Defaults to `results`.
*   `--countries`:  Optional.  A list of specific countries to process.  If not provided, all files ending in `_papers.csv` in the `--papers_dir` will be processed.

### Running the Analysis

1.  **Place your SCImago data file (e.g., `scimagojr 2023.csv`) in the `data` directory.**
2.  **Place your paper data files (e.g., `australia_papers.csv`, `canada_papers.csv`) in the `data/papers` directory.**
3.  **Run the script from the command line:**

    *   **To process all countries:**

        ```bash
        python src/run_analysis.py
        ```

    *   **To process specific countries (e.g., Australia and Canada):**

        ```bash
        python src/run_analysis.py --countries australia canada
        ```

    *   **To specify custom input and output directories:**

        ```bash
        python src/run_analysis.py --papers_dir my_data/papers --scimago my_data/scimago.csv --output my_results
        ```

## Configuration

*   **Weights:** The weights assigned to each component of the impact score can be adjusted in the `weights` dictionary within the `JournalImpactAnalyzer` class in `src/run_analysis.py`.  The default weights are:

    *   `journal_impact`: 0.30
    *   `citation_impact`: 0.30
    *   `recency`: 0.15
    *   `collaboration`: 0.10

    Modify these values to customize the relative importance of each factor.

## Output

The script generates the following output:

### Detailed Results (CSV)

For each country, a CSV file named `impact_scores.csv` is created in the `results/[country]` directory. This file contains the original paper data, along with the calculated impact scores:

| Column                    | Description                                                                  |
| ------------------------- | ---------------------------------------------------------------------------- |
| ... (original columns)   | Columns from the input paper data file.                                      |
| journal\_impact          | The calculated journal impact score (0-30).                                 |
| citation\_impact         | The calculated citation impact score (0-30).                                |
| recency                   | The calculated recency score (0-15).                                        |
| collaboration             | The calculated collaboration score (0 or 10).                               |
| total\_impact\_score     | The sum of the weighted impact components.                                  |
| normalized\_impact\_score | The total impact score normalized to a 0-100 scale.                        |
| impact\_tier              | The impact tier assigned to the paper ("Very Low", "Low", "Medium", "High", "Very High"). |

### Analysis Report

A comprehensive report is generated for each country and printed to the console. This report includes:

*   **Overall Statistics:**
    *   Total papers analyzed.
    *   Average impact score.
    *   Average citations per paper.
*   **Impact Distribution:**
    *   Number and percentage of papers in each impact tier (Very Low, Low, Medium, High, Very High).
*   **Journal Quality Distribution:**
    *   Percentage of publications in each SCImago quartile (Q1, Q2, Q3, Q4, and Unranked).
*   **Highest/Lowest Impact Papers:**
    *   Journal, title, and DOI of the highest and lowest scoring papers.
*   **Top Journals:**
    *   A list of the top journals (by publication count) along with their SCImago rank (if available).
*   **Publication Years:**
    *   A distribution of publication years.
* **International Collaboration:**
    * Percentage of papers that are international collaborations.

For comparative analyses (when processing multiple countries), a `comparative_analysis_[timestamp].csv` file is created in the `results` directory. This file contains a summary of key metrics for each country:

| Column                    | Description                                      |
| ------------------------- | ------------------------------------------------ |
| name                      | The name of the country.                         |
| total\_papers             | The total number of papers analyzed.             |
| avg\_impact\_score        | The average impact score for the country.        |
| international\_collab\_pct | The percentage of international collaborations. |

### Visualizations

The script generates several visualizations (saved as PNG files in the `results` directory):

*   `impact_scores.png`: A bar chart showing the average impact score for each country.
*   `publication_volume.png`: A bar chart showing the total number of papers for each country.
*   `international_collab.png`: A bar chart showing the percentage of international collaborations for each country.
*   `average_citations.png`: A bar chart showing the average number of citations per paper for each country.
*   `journal_quality.png`: A stacked bar chart showing the distribution of publications across SCImago quartiles for each country.

## Logging

The `PrettyLogger` class (in `src/logger.py`) provides detailed logging throughout the analysis process. It uses color-coded output to distinguish between different types of messages:

*   **Headers:**  Cyan, used for major sections of the analysis.
*   **Sub-headers:** Yellow, used for sub-sections within a country's analysis.
*   **Sections:** Blue, used for smaller sections within the analysis.
*   **Progress:** Green, used for indicating the progress of long-running tasks.
*   **Success:** Green, used for indicating successful completion of tasks.
*   **Info:** Blue, used for informational messages.
*   **Warning:** Yellow, used for warnings about potential issues.
*   **Error:** Red, used for error messages.
*   **Validation Steps:** Cyan, used for indicating the start of a validation step.
*   **Validation Results:** Magenta, used for reporting the results of a validation step.
*   **Validation Summary:** Cyan, used for summarizing the overall validation results.

The logger also supports writing log messages to a file (though this is not currently implemented in the main script).

## Extensibility and Customization

The codebase is designed to be easily extensible:

*   **Adding New Metrics:** You can easily add new metrics to the impact score calculation by modifying the `process_papers` method in the `JournalImpactAnalyzer` class.
*   **Using Different Data Sources:** The `_load_scimago_data` and `process_papers` methods can be adapted to handle data from different sources or in different formats.
*   **Customizing Weights:** The weights assigned to each component of the impact score can be adjusted in the `weights` dictionary within the `JournalImpactAnalyzer` class.
*   **Adding New Visualizations:** You can add new visualizations by modifying the `generate_visualizations` method.
*   **Improving Journal Matching:** The `match_journal` method could be further enhanced by incorporating more sophisticated fuzzy matching techniques or by using external APIs for journal data.

## Troubleshooting

*   **Missing Data:** Ensure that both the SCImago data file and the paper data files are correctly placed in the specified directories.  Check that the required columns are present in the input files.
*   **File Not Found Errors:** Double-check the file paths provided to the script, especially if you are using custom input or output directories.
*   **Incorrect Results:** If the results seem incorrect, verify that the input data is in the expected format and that the column mapping in `run_analysis.py` is accurate.  Review the log messages for any warnings or errors.
*   **Memory Errors:** If you encounter memory errors when processing very large datasets, try processing the data in smaller batches or using a more memory-efficient data structure.

## Future Enhancements

*   **Web Interface:** Develop a web interface for easier interaction and visualization.
*   **Database Integration:** Store data and results in a database for improved performance and scalability.
*   **Automated Data Retrieval:** Implement automated retrieval of SCImago and paper data from online sources.
*   **Advanced Journal Matching:** Incorporate more sophisticated fuzzy matching techniques and external APIs for journal data.
*   **Additional Metrics:** Include additional metrics such as Altmetrics, field-normalized citation impact, and open access status.
*   **User Authentication and Authorization:** Add user accounts and permissions for secure access and data management.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  See also our [SECURITY.md](SECURITY.md) policy.

## Contributing

Contributions are welcome! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) guidelines.

We maintain a [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) to ensure a welcoming and inclusive environment for all contributors.

## Code of Conduct

Please be respectful and constructive in all interactions.

## Acknowledgements

*   SCImago Journal & Country Rank ([https://www.scimagojr.com/](https://www.scimagojr.com/)) for providing the journal ranking data.
*   The developers of the Python libraries used in this project (pandas, numpy, matplotlib, colorama, tqdm).

## Citation

If you use this project in your research, please cite it as follows:

```bibtex
@misc{  ,
  author = {Tom, Alphin and {0000-0003-3787-8370}},
  title = {PaperImpact: A Comprehensive System for Analyzing the Impact of Scientific Publications},
  year = {2025},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/alpha912/PaperImpact}},

  note = {Email: alphin\@researchark.eu}

}
```
