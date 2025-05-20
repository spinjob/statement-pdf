# Financial CSV Transformer & Aggregator

This application is a Streamlit web app designed to process multiple CSV files from a specified directory. It applies a predefined set of financial calculations and transformations to each CSV and then aggregates the results into a single, consolidated CSV file.

## Core Logic

1.  **Input**: The application expects a directory containing one or more CSV files. Each input CSV should ideally be a two-column file where:
    *   Column 1: A descriptive key (e.g., "Total Operating Income", "Total Cash"). Key matching is case-insensitive.
    *   Column 2: A monetary value (e.g., "$1,234.56", "500.00"). Currency symbols and commas are stripped for calculation.

2.  **Formulas**: A predefined set of formulas (found in `FORMULAS_CONFIG` within `app.py`) dictates how new output columns are generated. These formulas can be:
    *   **Direct Mapping**: An input key directly maps to an output column (e.g., `[Net Income]` from input becomes `Net Income` in output).
    *   **Summation**: Values from multiple input keys are summed to produce an output column (e.g., `[Total Cash] + [Total Other Current Assets] = Total Current Assets`).
    *   **Subtraction**: One input key's value is subtracted from another's (e.g. `[Total Liabilities] - [Total SECURITY DEPOSITS] = Total Current Liabilites`)

3.  **Processing**: For each CSV file found in the input directory:
    *   The application reads the key-value pairs.
    *   It applies the defined formulas to calculate the required output values.
    *   If an expected key is missing in an input CSV, its value is treated as `0.0` for calculation purposes.

4.  **Output**: The application generates a single CSV file containing the transformed data from all processed input files.
    *   Each row in the output CSV corresponds to one processed input CSV file.
    *   The **first column** in the output CSV is always `Filename`, indicating the source CSV file for that row.
    *   Subsequent columns are the results of the applied formulas.
    *   Monetary values in the output are formatted with a '$' symbol and two decimal places (e.g., "$150.00").

## Prerequisites

*   Python 3.7 or higher.
*   `pip` (Python package installer).

## Setup & Installation

1.  **Clone the repository or download the `app.py` file.**

2.  **Navigate to the project directory** in your terminal:
    ```bash
    cd path/to/your/project_directory
    ```

3.  **Create a virtual environment (recommended)**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install the required Python packages**:
    ```bash
    pip install streamlit pandas
    ```

## Running the Application

1.  Once the setup is complete, run the Streamlit application from your terminal:
    ```bash
    streamlit run app.py
    ```
2.  This command will start the Streamlit development server, and your default web browser should automatically open to the application's URL (usually `http://localhost:8501`).

## Using the Application

1.  **Input Directory**: In the sidebar of the web application, enter the full path to the directory that contains your input CSV files.
2.  **Output CSV Filename**: Specify the desired name for the generated consolidated CSV file (e.g., `consolidated_report.csv`). It defaults to `consolidated_output.csv`.
3.  **Process**: Click the "🚀 Process CSVs" button.
    *   The application will show a spinner and status messages indicating which files are being processed.
    *   Any warnings or errors during processing (e.g., file not found, malformed CSV rows) will be displayed.
4.  **Preview**: If processing is successful, a preview of the first 5 rows of the generated data will be displayed in the main area.
5.  **Download**: A download button will appear, allowing you to save the consolidated CSV file to your computer.
6.  **Formulas Applied**: The sidebar also lists the financial formulas that were applied during the transformation for your reference.

## Example Input CSV structure (e.g., `file1.csv`)

```csv
Total Operating Income,$3000.00
Total Operating Expenses,$2000.00
NOI - Net Operating Income,$1000.00
Total Cash,$10000.00
Total Other Current Assets,$5000.00
Net Income,$500.00
# ... and so on for other relevant keys
```

This `file1.csv` would then become a single row in the output CSV, starting with `file1.csv` in the 'Filename' column, followed by the calculated values based on `FORMULAS_CONFIG`.
