import pymupdf4llm
import pathlib
import argparse
import io # Added for StringIO
import pandas as pd # Added for table extraction
from markdown import markdown # Added for Markdown to HTML conversion

def _extract_and_save_tables(markdown_file_path: str):
    """
    Extracts tables from a Markdown file and saves them as CSV files.

    Args:
        markdown_file_path (str): Path to the input Markdown file.
    """
    md_path = pathlib.Path(markdown_file_path)
    output_dir = md_path.parent
    base_filename = md_path.stem

    print(f"Attempting to extract tables from '{markdown_file_path}'...")

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert Markdown to HTML
        # Using 'fenced_code' and 'tables' extensions for better compatibility
        html_content = markdown(md_content, extensions=['fenced_code', 'tables'])

        # Use pandas to read HTML tables
        # pd.read_html might require lxml or other parsers to be installed.
        # Explicitly specify lxml parser if available and robust.
        try:
            tables = pd.read_html(io.StringIO(html_content), flavor='lxml')
        except ImportError:
            # Fallback if lxml is not found, though it should be in requirements
            tables = pd.read_html(io.StringIO(html_content))


        if not tables:
            print("No tables found in the Markdown content.")
            return

        for i, df in enumerate(tables):
            # Clean up DataFrame:
            # Sometimes headers might be read as data or columns might be unnamed from malformed/simple tables
            # This is a basic cleanup, more sophisticated logic might be needed for complex cases
            if isinstance(df.columns, pd.MultiIndex):
                 df.columns = df.columns.map('_'.join).str.strip('_')
            else:
                 df.columns = [str(col) if not str(col).startswith("Unnamed:") else f"column_{j}" for j, col in enumerate(df.columns)]

            # Drop rows that are entirely NaN (often occurs with table structures)
            df.dropna(how='all', inplace=True)
            # Drop columns that are entirely NaN
            df.dropna(axis=1, how='all', inplace=True)


            if df.empty:
                print(f"Table {i+1} was empty after cleanup, skipping.")
                continue

            csv_filename = output_dir / f"{base_filename}_table_{i+1}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Successfully extracted and saved table {i+1} to '{csv_filename}'")

    except FileNotFoundError:
        print(f"Error: Markdown file not found at '{markdown_file_path}' for table extraction.")
    except Exception as e:
        print(f"An error occurred during table extraction: {e}")

def convert_pdf_to_markdown(input_pdf_path: str, output_md_path: str, write_images: bool = False, page_chunks: bool = False, extract_tables: bool = False):
    """
    Converts a PDF file to Markdown using pymupdf4llm and optionally extracts tables to CSV.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        output_md_path (str): Path to save the output Markdown file.
        write_images (bool): Whether to extract and write images from the PDF.
        page_chunks (bool): Whether to output page content in chunks (list of dicts).
        extract_tables (bool): Whether to extract tables from the Markdown to CSV files.
    """
    print(f"Starting conversion of '{input_pdf_path}'...")
    markdown_successfully_created = False

    try:
        if page_chunks:
            data = pymupdf4llm.to_markdown(input_pdf_path, write_images=write_images, page_chunks=True)
            full_markdown_text = ""
            for i, page_data in enumerate(data):
                full_markdown_text += f"## Page {i+1}\n\n"
                full_markdown_text += page_data.get("text", "")
                full_markdown_text += "\n\n---\n\n"
            pathlib.Path(output_md_path).write_bytes(full_markdown_text.encode())
            print(f"Page-chunked Markdown content successfully saved to '{output_md_path}'")
            markdown_successfully_created = True
        else:
            md_text = pymupdf4llm.to_markdown(input_pdf_path, write_images=write_images)
            pathlib.Path(output_md_path).write_bytes(md_text.encode())
            print(f"Markdown content successfully saved to '{output_md_path}'")
            markdown_successfully_created = True

        if write_images:
            print(f"Images (if any) were extracted to the folder containing '{pathlib.Path(input_pdf_path).parent}'.")
            # Corrected image path reference for clarity
            image_output_folder_note = f"They will be named like '{pathlib.Path(input_pdf_path).name}-p<page_num>-<image_index>.<ext>'"
            print(image_output_folder_note)
            
        if markdown_successfully_created and extract_tables:
            _extract_and_save_tables(output_md_path)

    except FileNotFoundError:
        print(f"Error: Input PDF file not found at '{input_pdf_path}'")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a PDF to Markdown using pymupdf4llm and optionally extract tables to CSV.")
    parser.add_argument("input_pdf", help="Path to the input PDF file.")
    parser.add_argument("-o", "--output_md", default="output_pymupdf4llm.md", help="Path to save the output Markdown file (default: output_pymupdf4llm.md).")
    parser.add_argument("--write_images", action="store_true", help="Extract and write images from the PDF.")
    parser.add_argument("--page_chunks", action="store_true", help="Output content as page chunks instead of a single Markdown string.")
    parser.add_argument("--extract_tables", action="store_true", help="Extract tables from the generated Markdown file to CSV files.")
    
    args = parser.parse_args()

    # For demonstration, you might want to create a dummy input.pdf
    # or ensure you have one in your project directory.
    # For example:
    # if not pathlib.Path(args.input_pdf).exists():
    #     print(f"Warning: Input file '{args.input_pdf}' does not exist. Please create it or specify a valid PDF.")
    # else:
    # convert_pdf_to_markdown(args.input_pdf, args.output_md, args.write_images, args.page_chunks)

    convert_pdf_to_markdown(args.input_pdf, args.output_md, args.write_images, args.page_chunks, args.extract_tables) 