import streamlit as st
import pandas as pd
import re
import io

# Page settings for a professional look
st.set_page_config(page_title="Bank Data Extractor | BOC Solution Manager", layout="wide")

st.title("📊 Performance Report Data Extractor")
st.info("Upload your raw CSV and the Product Mapping file to process.")

# --- SIDEBAR: Dynamic Filtering ---
st.sidebar.header("Filter Configuration")
st.sidebar.write("Add or remove Account Numbers below (comma-separated).")

# Default account list provided in your requirements
default_accs = "300016, 300015, 300037, 300057, 300033, 303007, 303543, 408122, 401002"
account_input = st.sidebar.text_area("Target Account Numbers:", value=default_accs, height=250)

# Parsing the input into a list of integers
try:
    filter_list = [int(x.strip()) for x in account_input.split(",") if x.strip().isdigit()]
except ValueError:
    st.sidebar.error("Please ensure the list contains only numbers and commas.")
    filter_list = []

# --- MAIN SECTION: File Uploads ---
col1, col2 = st.columns(2)

with col1:
    main_file = st.file_uploader("1. Upload Raw Data CSV (Up to 500MB)", type=['csv'])
with col2:
    mapping_file = st.file_uploader("2. Upload Product Code Mapping CSV", type=['csv'])

def process_logic(raw_df, map_df, target_accounts):
    """
    Core logic to clean, extract, merge and filter bank data.
    """
    column_names = [
        'Document_No', 'Posting_Date', 'External_Document_No', 'Account_Type',
        'Account_No', 'Debit_Amount', 'Credit_Amount', 'Branch_Code',
        'Product_Code', 'Contract_Asset_Code', 'Narration_1', 'Narration_2',
        'Narration_3', 'Finacle_GL_No', 'Document_Date'
    ]
    
    # Cleaning the raw structure
    raw_df.columns = column_names
    raw_df = raw_df.iloc[3:].reset_index(drop=True)

    # Regex Extraction
    account_number_pattern = r'\b([1-6]\d{11})\b'
    operative_account_pattern = r'\b(L\d{9})\b'
    
    raw_df['Account number'] = raw_df['Narration_1'].str.extract(account_number_pattern, expand=False)
    raw_df['Operative account'] = raw_df['Narration_1'].str.extract(operative_account_pattern, expand=False)

    # Data Type Conversion for Merging
    raw_df['Finacle_GL_No'] = pd.to_numeric(raw_df['Finacle_GL_No'], errors='coerce')
    map_df['GL_Code'] = pd.to_numeric(map_df['GL_Code'], errors='coerce')
    
    # Merging Mapping File
    merged_df = pd.merge(raw_df, map_df[['GL_Code', 'Product_Code']], 
                         left_on='Finacle_GL_No', right_on='GL_Code', how='left')
    
    raw_df['Update_Product_Code'] = merged_df['Product_Code_y']

    # Final Filtering based on Account_No
    raw_df['Account_No'] = pd.to_numeric(raw_df['Account_No'], errors='coerce')
    filtered_output = raw_df[raw_df['Account_No'].isin(target_accounts)].copy()
    
    return filtered_output

# --- EXECUTION ---
if main_file and mapping_file:
    try:
        with st.spinner('Engineering is in progress... Processing heavy data...'):
            # Load data
            df_main = pd.read_csv(main_file, skiprows=3, header=None, low_memory=False)
            df_map = pd.read_csv(mapping_file, encoding='latin1')

            # Run the engine
            final_data = process_logic(df_main, df_map, filter_list)

            st.success(f"✅ Success! Processed {len(final_data)} records matching your filters.")
            
            # Data Preview
            st.subheader("Preview (First 50 Rows)")
            st.dataframe(final_data.head(50), use_container_width=True)

            # Download Option
            output_csv = final_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Cleaned CSV",
                data=output_csv,
                file_name="Automated_Bank_Export.csv",
                mime="text/csv",
            )
    except Exception as e:
        st.error(f"An error occurred during processing: {e}")
else:
    st.warning("Awaiting files. Please upload both CSVs to generate the report.")
