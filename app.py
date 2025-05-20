#!/usr/bin/env python3
import csv
import re
import os
import streamlit as st # Added Streamlit
from io import StringIO # To handle CSV data in memory for download

# Configuration for the transformations based on user's formulas
# Each dictionary defines an output column:
# 'output_header': The name of the column in the output CSV.
# 'type': The type of operation ('direct', 'sum', 'subtract').
# 'input_keys_from_csv': A list of keys (lowercase) to find in the input CSV.
#                        For 'subtract', the order is [minuend_key, subtrahend_key].
FORMULAS_CONFIG = [
    {'output_header': 'Total Operating Income', 'type': 'direct', 'input_keys_from_csv': ['total operating income']},
    {'output_header': 'Total Operating Expense', 'type': 'direct', 'input_keys_from_csv': ['total operating expense']},
    {'output_header': 'Net Operating Income', 'type': 'direct', 'input_keys_from_csv': ['noi - net operating income']},
    {'output_header': 'Net Income', 'type': 'direct', 'input_keys_from_csv': ['net income']},
    {'output_header': 'Total Current Assets', 'type': 'sum', 'input_keys_from_csv': ['total cash', 'total other current assets']},
    {'output_header': 'Interest Expense', 'type': 'direct', 'input_keys_from_csv': ['mortgage interest']},
    {'output_header': 'Total Assets', 'type': 'direct', 'input_keys_from_csv': ['total assets']},
    {'output_header': 'Total Current Liabilites', 'type': 'subtract', 'input_keys_from_csv': ['total liabilities', 'total security deposits']},
    {'output_header': 'Total Long-Term Liabilites', 'type': 'direct', 'input_keys_from_csv': ['total security deposits']},
    {'output_header': 'Capital Contributions', 'type': 'sum', 'input_keys_from_csv': ['owner contribution', 'owner contribution - owner 1', 'owner contribution - owner 2']},
    {'output_header': 'Capital Distributions', 'type': 'sum', 'input_keys_from_csv': ['owner distribution - owner 1', 'owner distribution - owner 2']},
    {'output_header': 'Retained Earnings', 'type': 'direct', 'input_keys_from_csv': ['calculated retained earnings']},
    {'output_header': "Total Owners' Equity", 'type': 'direct', 'input_keys_from_csv': ['total capital']},
]

def parse_monetary_value(value_str):
    """Converts a string monetary value (e.g., "$1,234.56") to a float."""
    if isinstance(value_str, (int, float)):
        return float(value_str)
    if not isinstance(value_str, str):
        return 0.0
    
    # Remove currency symbols (like $), commas, and whitespace
    cleaned_value = re.sub(r'[$\s,]', '', value_str)
    try:
        return float(cleaned_value)
    except ValueError:
        # If conversion fails, return 0.0 or you could raise an error/log
        return 0.0

def load_input_data(input_csv_path, status_messages_area):
    """Reads the input CSV and stores its data in a dictionary.
    Keys are made lowercase for case-insensitive matching.
    Values are parsed as floats.
    """
    data = {}
    try:
        with open(input_csv_path, mode='r', encoding='utf-8-sig') as infile: # utf-8-sig handles BOM
            reader = csv.reader(infile)
            for row_number, row in enumerate(reader, 1):
                if len(row) >= 2:
                    key = row[0].strip().lower()
                    value_str = row[1].strip()
                    data[key] = parse_monetary_value(value_str)
                elif row: # Non-empty row but not enough columns
                    status_messages_area.warning(f"Skipping row {row_number} in '{os.path.basename(input_csv_path)}' (insufficient columns): {row}")
    except FileNotFoundError:
        status_messages_area.error(f"Input file '{os.path.basename(input_csv_path)}' not found.")
        return None
    except Exception as e:
        status_messages_area.error(f"Error reading/parsing '{os.path.basename(input_csv_path)}': {e}")
        return None
    return data

def calculate_output_values(input_filename, input_data, formulas):
    """Calculates the output values based on the defined formulas and input data."""
    output_headers = ['Filename'] # Add Filename as the first header
    calculated_values = [input_filename] # Add the actual filename as the first value

    if input_data is None:
        # Still return headers even if data is None, so output CSV has consistent columns
        for formula_item in formulas:
            output_headers.append(formula_item['output_header'])
            calculated_values.append(0.0) # Or some placeholder like 'N/A' if preferred
        return output_headers, calculated_values

    for formula_item in formulas:
        output_headers.append(formula_item['output_header'])
        val = 0.0
        
        # Ensure all lookup keys from the formula config are lowercase
        # (though they are already defined as such in FORMULAS_CONFIG)
        current_input_keys = [key.lower() for key in formula_item['input_keys_from_csv']]

        if formula_item['type'] == 'direct':
            # For 'direct', we expect one input key.
            # .get(key, 0.0) safely handles missing keys, defaulting to 0.0
            val = input_data.get(current_input_keys[0], 0.0)
        
        elif formula_item['type'] == 'sum':
            current_sum = 0.0
            for key in current_input_keys:
                current_sum += input_data.get(key, 0.0)
            val = current_sum
        
        elif formula_item['type'] == 'subtract':
            # Expects two keys: minuend, subtrahend
            if len(current_input_keys) == 2:
                minuend = input_data.get(current_input_keys[0], 0.0)
                subtrahend = input_data.get(current_input_keys[1], 0.0)
                val = minuend - subtrahend
            else:
                # This kind of warning can also be displayed in Streamlit if needed
                print(f"Warning: Subtract formula for '{formula_item['output_header']}' incorrect keys.")
        
        calculated_values.append(val)
    
    return output_headers, calculated_values

def process_directory_and_generate_csv_data(input_dir_path, formulas_config, status_messages_area):
    """
    Processes all CSV files in the input directory and returns the consolidated data
    as a string in CSV format.
    """
    if not input_dir_path or not os.path.isdir(input_dir_path):
        status_messages_area.error(f"Input directory '{input_dir_path}' not found or is not a directory.")
        return None, None

    all_rows_data = []
    all_output_headers = []
    processed_file_count = 0

    for filename in os.listdir(input_dir_path):
        if filename.lower().endswith('.csv'):
            input_csv_path = os.path.join(input_dir_path, filename)
            status_messages_area.info(f"Processing file: {filename}...")
            
            input_data = load_input_data(input_csv_path, status_messages_area)
            
            current_headers, current_values = calculate_output_values(filename, input_data, formulas_config)

            if not all_output_headers:
                all_output_headers = current_headers
            
            if current_values:
                 # Ensure consistent row length, especially if input_data was None
                if len(current_values) != len(all_output_headers) and input_data is None:
                     temp_values = [filename] + [0.0] * (len(all_output_headers) -1)
                     all_rows_data.append(temp_values)
                else:
                    all_rows_data.append(current_values)
                processed_file_count += 1
            else:
                status_messages_area.warning(f"Processing '{filename}' resulted in no output data. Skipping.")
        # else:
        #     status_messages_area.info(f"Skipping non-CSV file: {filename}") # Optional: too verbose?

    if not processed_file_count:
        status_messages_area.warning(f"No CSV files found or processed in directory '{input_dir_path}'.")
        return None, None

    # Generate CSV string
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(all_output_headers)
    for data_row in all_rows_data:
        formatted_row = [data_row[0]] + [f"${value:.2f}" if isinstance(value, (int, float)) else str(value) for value in data_row[1:]]
        writer.writerow(formatted_row)
    
    status_messages_area.success(f"Successfully processed {processed_file_count} CSV file(s).")
    return output.getvalue(), all_output_headers


def streamlit_main():
    st.set_page_config(layout="wide")
    st.title("📁 CSV Aggregator & Transformer")

    st.markdown("""
    This application processes all CSV files within a specified directory.
    For each CSV, it applies predefined financial formulas and aggregates the results
    into a single downloadable CSV file. Each row in the output corresponds to an
    input CSV file, with the first column indicating the source filename.
    """)

    # Session state to store output data for download
    if 'csv_output_data' not in st.session_state:
        st.session_state.csv_output_data = None
    if 'csv_output_filename' not in st.session_state:
        st.session_state.csv_output_filename = "transformed_data.csv"
    if 'last_processed_headers' not in st.session_state:
        st.session_state.last_processed_headers = []


    st.sidebar.header("⚙️ Configuration")
    input_dir = st.sidebar.text_input("Enter path to Input Directory with CSVs", 
                                      help="Provide the full path to the folder containing your CSV files.",
                                      value=st.session_state.get("last_input_dir", ""))
    
    output_filename_default = "consolidated_output.csv"
    output_filename = st.sidebar.text_input("Enter desired Output CSV Filename", value=output_filename_default)

    status_messages_area = st.empty() # Placeholder for status messages

    if st.sidebar.button("🚀 Process CSVs", type="primary"):
        st.session_state.csv_output_data = None # Clear previous results
        st.session_state.last_processed_headers = []
        
        if input_dir:
            st.session_state.last_input_dir = input_dir # Remember last input dir
            with st.spinner(f"Processing files in '{input_dir}'..."):
                csv_data_str, headers = process_directory_and_generate_csv_data(input_dir, FORMULAS_CONFIG, status_messages_area)
                if csv_data_str:
                    st.session_state.csv_output_data = csv_data_str
                    st.session_state.csv_output_filename = output_filename if output_filename.endswith(".csv") else f"{output_filename}.csv"
                    st.session_state.last_processed_headers = headers
                    status_messages_area.success(f"All CSV files processed! Ready to download '{st.session_state.csv_output_filename}'.")
                else:
                    status_messages_area.error("Processing failed or no data was generated.")
        else:
            status_messages_area.warning("Please enter an input directory path.")

    if st.session_state.csv_output_data:
        st.header("📊 Processed Data Preview (First 5 rows)")
        
        # Create a preview dataframe
        preview_data = StringIO(st.session_state.csv_output_data)
        df_preview_list = list(csv.reader(preview_data))
        
        if st.session_state.last_processed_headers and len(df_preview_list) > 1:
            import pandas as pd # Import pandas locally for preview
            # Use headers from session state, actual data rows start from index 1
            df = pd.DataFrame(df_preview_list[1:], columns=st.session_state.last_processed_headers)
            st.dataframe(df.head())
        elif len(df_preview_list) > 0 : # Only headers or no data
             st.text("Preview of generated CSV content (headers only or limited data):")
             st.code("".join(df_preview_list[:6])) # Show first few lines as text
        else:
            st.text("No data to preview.")


        st.download_button(
            label=f"📥 Download {st.session_state.csv_output_filename}",
            data=st.session_state.csv_output_data,
            file_name=st.session_state.csv_output_filename,
            mime='text/csv',
        )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Formulas Applied:")
    # Display formulas in a more readable way
    for i, formula in enumerate(FORMULAS_CONFIG):
        source_keys = ' + '.join(formula['input_keys_from_csv']) if formula['type'] == 'sum' else \
                      ' - '.join(formula['input_keys_from_csv']) if formula['type'] == 'subtract' else \
                      formula['input_keys_from_csv'][0]
        st.sidebar.caption(f"{i+1}. **{formula['output_header']}**  ⬅️  `{source_keys.title()}` ({formula['type']})")


if __name__ == "__main__":
    streamlit_main()
