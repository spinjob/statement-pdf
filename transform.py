#!/usr/bin/env python3
import csv
import argparse
import re

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
    {'output_header': 'Total Owners\' Equity', 'type': 'direct', 'input_keys_from_csv': ['total capital']},
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

def load_input_data(input_csv_path):
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
                    print(f"Warning: Skipping row {row_number} in '{input_csv_path}' due to insufficient columns: {row}")
    except FileNotFoundError:
        print(f"Error: Input file '{input_csv_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading or parsing '{input_csv_path}': {e}")
        return None
    return data

def calculate_output_values(input_data, formulas):
    """Calculates the output values based on the defined formulas and input data."""
    output_headers = []
    calculated_values = []

    if input_data is None:
        return [], []

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
                print(f"Warning: Subtract formula for '{formula_item['output_header']}' has an incorrect number of input keys: {formula_item['input_keys_from_csv']}. Expected 2.")
                # val remains 0.0 as initialized
        
        calculated_values.append(val)
    
    return output_headers, calculated_values

def write_output_csv(output_csv_path, headers, values_row):
    """Writes the headers and the calculated values to the output CSV file.
    Values are formatted as currency strings (e.g., "$150.00").
    """
    if not headers or not values_row:
        print("Warning: No data to write to output CSV.")
        return

    try:
        with open(output_csv_path, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(headers)
            # Format numerical values back into currency strings for the output
            formatted_values = [f"${value:.2f}" for value in values_row]
            writer.writerow(formatted_values)
        print(f"Successfully transformed data and saved to '{output_csv_path}'")
    except IOError as e:
        print(f"Error writing to output file '{output_csv_path}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV writing: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Transforms a two-column CSV (key, monetary value) into a new CSV "
                    "with columns derived from predefined formulas."
    )
    parser.add_argument("input_csv", help="Path to the input CSV file (e.g., input.csv)")
    parser.add_argument("output_csv", help="Path for the output CSV file (e.g., output.csv)")
    args = parser.parse_args()

    input_data = load_input_data(args.input_csv)
    
    if input_data is not None:
        output_headers, output_values_calculated = calculate_output_values(input_data, FORMULAS_CONFIG)
        if output_headers and output_values_calculated:
            write_output_csv(args.output_csv, output_headers, output_values_calculated)
        else:
            print("Processing resulted in no output data. Output file not written.")
    else:
        print("Failed to load input data. Transformation aborted.")

if __name__ == "__main__":
    main()
