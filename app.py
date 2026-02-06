import streamlit as st
import pandas as pd
import re
import io

# Page settings
st.set_page_config(page_title="Bank Data Extractor | BOC Solution Manager", layout="wide")

st.title("📊 Performance Report Data Extractor")
st.info("Upload your raw CSV and the Product Mapping file to process.")

# --- SIDEBAR: Dynamic Filtering ---
st.sidebar.header("Filter Configuration")

# ✅ FIX 1: Use triple quotes for multi-line string
default_accs = """300016, 300015, 300037, 300057, 300033, 300035, 300058, 300021, 300024, 300040,
300048, 300051, 300056, 300060, 300038, 300047, 300054, 300034, 300036, 300045,
300046, 300052, 300053, 300018, 300020, 300032, 300017, 300019, 300027, 300039,
300041, 300049, 300055, 300029, 300023, 300026, 300059, 303007, 303008, 303009,
303010, 303015, 303022, 303025, 303028, 303029, 303030, 303027, 303020, 303031,
303032, 303033, 303035, 303036, 303037, 303038, 303039, 303040, 303041, 303042,
303043, 303044, 303045, 303046, 303047, 303048, 303049, 303050, 303051, 303052,
303001, 303002, 303003, 303004, 303005, 303011, 303012, 303016, 303017, 303021,
303023, 303024, 303026, 303543, 303545, 303546, 303547, 303548, 303541, 303536,
303537, 303538, 303539, 408122, 303529, 303534, 408132, 303535, 408145, 408142,
408135, 408133, 408131, 408130, 408129, 408125, 408122, 408120, 408118, 408117,
408114, 408113, 408112, 408111, 408109, 408108, 408107, 408105, 408104, 408103,
408098, 408096, 408095, 408093, 408092, 408090, 408086, 408083, 408080, 408078,
408077, 408076, 408070, 408069, 408068, 408065, 408062, 408061, 408057, 408056,
408055, 408050, 408049, 408047, 408046, 408044, 408043, 408042, 408040, 408039,
408038, 408035, 408034, 408030, 408028, 408027, 408025, 408024, 408023, 408022,
408021, 408020, 408019, 408018, 408015, 408014, 408013, 408012, 408010, 408009,
408007, 408005, 408004, 408003, 406033, 406030, 406029, 406028, 406027, 406025,
406023, 406022, 406017, 406015, 406014, 406011, 406005, 406003, 406002, 406001,
405010, 405008, 405007, 405001, 404002, 402007, 402006, 402003, 402002, 402001,
401030, 401029, 401028, 401026, 401025, 401024, 401020, 401014, 401013, 401012,
401011, 401008, 401007, 401006, 401005, 401004, 401003, 401002"""

account_input = st.sidebar.text_area("Target Account Numbers:", value=default_accs, height=250)

try:
    filter_list = [int(x.strip()) for x in account_input.replace('\n', ',').split(",") if x.strip().isdigit()]
except ValueError:
    st.sidebar.error("Check your account number list formatting.")
    filter_list = []

col1, col2 = st.columns(2)
with col1:
    main_file = st.file_uploader("1. Upload Raw Data CSV", type=['csv'])
with col2:
    mapping_file = st.file_uploader("2. Upload Product Code Mapping CSV", type=['csv'])

def process_logic(raw_df, map_df, target_accounts):
    column_names = [
        'Document_No', 'Posting_Date', 'External_Document_No', 'Account_Type',
        'Account_No', 'Debit_Amount', 'Credit_Amount', 'Branch_Code',
        'Product_Code', 'Contract_Asset_Code', 'Narration_1', 'Narration_2',
        'Narration_3', 'Finacle_GL_No', 'Document_Date'
    ]
    
    # Check if column counts match before assigning
    if len(raw_df.columns) == len(column_names):
        raw_df.columns = column_names
    else:
        st.error(f"Column mismatch! File has {len(raw_df.columns)} columns but expected {len(column_names)}.")
        return pd.DataFrame()

    # ✅ FIX 2: Removed raw_df.iloc[3:] from here because it's already done in read_csv

    acc_pattern = r'\b([1-6]\d{11})\b'
    op_pattern = r'\b(L\d{9})\b'
    
    raw_df['Account number'] = raw_df['Narration_1'].str.extract(acc_pattern, expand=False)
    raw_df['Operative account'] = raw_df['Narration_1'].str.extract(op_pattern, expand=False)

    raw_df['Finacle_GL_No'] = pd.to_numeric(raw_df['Finacle_GL_No'], errors='coerce')
    map_df['GL_Code'] = pd.to_numeric(map_df['GL_Code'], errors='coerce')
    
    merged_df = pd.merge(raw_df, map_df[['GL_Code', 'Product_Code']], 
                         left_on='Finacle_GL_No', right_on='GL_Code', how='left')
    
    raw_df['Update_Product_Code'] = merged_df['Product_Code_y']
    raw_df['Account_No'] = pd.to_numeric(raw_df['Account_No'], errors='coerce')
    
    return raw_df[raw_df['Account_No'].isin(target_accounts)].copy()

if main_file and mapping_file:
    try:
        with st.spinner('Processing...'):
            # Read CSV - Skiprows is correct here
            df_main = pd.read_csv(main_file, skiprows=3, header=None, low_memory=False)
            df_map = pd.read_csv(mapping_file, encoding='latin1')

            final_data = process_logic(df_main, df_map, filter_list)

            if not final_data.empty:
                st.success(f"✅ Processed {len(final_data)} records.")
                st.dataframe(final_data.head(50), use_container_width=True)
                
                output_csv = final_data.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Cleaned CSV", data=output_csv, file_name="BOC_Performance_Report.csv", mime="text/csv")
            else:
                st.warning("No data found matching the filters.")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("Please upload both files.")
