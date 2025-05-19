import streamlit as st
import fitz  # PyMuPDF
import ollama
import base64
import io
import pandas as pd
from markdown import markdown
import zipfile # For zipping multiple CSVs

st.title("PDF to Markdown Extractor")

# Helper function to extract tables and return them as CSV data strings
def extract_tables_from_markdown(markdown_content: str) -> list[tuple[str, str]]:
    """
    Extracts tables from a Markdown string and returns them as a list of (filename, csv_data) tuples.
    """
    extracted_tables_csv_data = []
    try:
        html_content = markdown(markdown_content, extensions=['fenced_code', 'tables'])
        
        # Use a try-except block for pandas.read_html as it can raise errors on malformed HTML
        try:
            tables_dfs = pd.read_html(io.StringIO(html_content), flavor='lxml')
        except ImportError:
            tables_dfs = pd.read_html(io.StringIO(html_content)) # Fallback if lxml is not available
        except ValueError: # Handles cases where no tables are found or HTML is unparseable for tables
            tables_dfs = []

        if not tables_dfs:
            return []

        for i, df in enumerate(tables_dfs):
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.map('_'.join).str.strip('_')
            else:
                df.columns = [str(col) if not str(col).startswith("Unnamed:") else f"column_{j}" for j, col in enumerate(df.columns)]
            
            df.dropna(how='all', inplace=True)
            df.dropna(axis=1, how='all', inplace=True)

            if df.empty:
                continue
            
            csv_filename = f"table_{i+1}.csv"
            csv_data = df.to_csv(index=False, encoding='utf-8')
            extracted_tables_csv_data.append((csv_filename, csv_data))
            
    except Exception as e:
        st.warning(f"An error occurred during table extraction: {e}")
        # Return whatever was extracted so far, or an empty list if error was early
        return extracted_tables_csv_data 
    return extracted_tables_csv_data

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    st.write("PDF uploaded successfully!")
    
    # Convert PDF to images
    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    images_base64 = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        images_base64.append(img_base64)
    
    if images_base64:
        st.write(f"Extracted {len(images_base64)} pages from the PDF.")
        
        all_markdown_text = ""
        with st.spinner("Extracting text with Ollama..."):
            for i, img_b64 in enumerate(images_base64):
                st.write(f"Processing page {i+1}/{len(images_base64)}...")
                try:
                    response = ollama.chat(
                        model='gemma3:12b',
                        messages=[
                            {
                                'role': 'user',
                                'content': 'Can you extract the income and expenditure information in markdown while maintaining the information exactly?',
                                'images': [img_b64]
                            }
                        ]
                    )
                    page_markdown = response['message']['content']
                    all_markdown_text += page_markdown + "\n\n---\n\n" # Add a separator between pages
                    st.image(io.BytesIO(base64.b64decode(img_b64)), caption=f"Page {i+1}")
                    st.markdown(f"**Extracted Markdown for Page {i+1}:**")
                    st.markdown(page_markdown)
                except Exception as e:
                    st.error(f"Error processing page {i+1} with Ollama: {e}")
                    # Optionally, you can add more detailed error handling or logging here
                    # For example, check if Ollama server is running or if the model is available.
                    st.error("Ensure Ollama is running and the 'llava' model is pulled (e.g., `ollama run llava` or `ollama pull llava`).")
                    break # Stop processing if an error occurs
            
        if all_markdown_text:
            st.markdown("## Combined Extracted Markdown")
            st.markdown(all_markdown_text)
            st.download_button(
                label="Download Markdown",
                data=all_markdown_text,
                file_name="extracted_content.md",
                mime="text/markdown",
            )

            st.markdown("--- ") # Separator
            st.markdown("### Table Extraction from Markdown")
            if st.button("Extract Tables to CSV"): 
                with st.spinner("Extracting tables..."):
                    csv_files_data = extract_tables_from_markdown(all_markdown_text)
                    
                    if not csv_files_data:
                        st.info("No tables found in the extracted Markdown or tables were empty after cleanup.")
                    else:
                        st.success(f"Found {len(csv_files_data)} table(s).")
                        
                        if len(csv_files_data) == 1:
                            file_name, csv_data = csv_files_data[0]
                            st.download_button(
                                label=f"Download {file_name}",
                                data=csv_data,
                                file_name=file_name,
                                mime="text/csv",
                            )
                        else:
                            # Create a zip file in memory for multiple CSVs
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                                for file_name, csv_data in csv_files_data:
                                    zip_file.writestr(file_name, csv_data)
                            
                            st.download_button(
                                label="Download All Tables as ZIP",
                                data=zip_buffer.getvalue(),
                                file_name="extracted_tables.zip",
                                mime="application/zip",
                            )
    else:
        st.error("Could not extract images from the PDF.")
