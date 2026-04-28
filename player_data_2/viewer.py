import streamlit as st
import pandas as pd
import glob
import os

# ── Page Config ──
st.set_page_config(page_title="LILA BLACK — Parquet Explorer", page_icon="📂", layout="wide")

# ── Custom CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600&display=swap');

.stApp { background-color: #0b0f19; color: #f8fafc; }
.hdr { font-family: 'Rajdhani', sans-serif; font-size:2.2rem; font-weight:700; background:linear-gradient(90deg,#4FC3F7,#CE93D8);
       -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.5rem; }
.sub { font-family: 'Inter', sans-serif; color:#64748b; font-size:1rem; margin-top:0; }

/* Customizing Dataframe appearance */
[data-testid="stDataFrame"] {
    background-color: rgba(18, 24, 38, 0.6);
    border: 1px solid rgba(48, 54, 61, 0.6);
    border-radius: 8px;
    padding: 5px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="hdr">📂 Parquet Data Explorer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub">Raw Data Table Viewer for .nakama-0 files</p>', unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("### 🔍 Search Settings")
    base_path = os.path.join(".", "data", "raw")
    
    # Find all folders that might contain data
    all_items = os.listdir(base_path)
    folders = [d for d in all_items if os.path.isdir(os.path.join(base_path, d)) and not d.startswith(".")]
    folders.sort()
    
    selected_folder = st.selectbox("Select Data Folder", folders if folders else ["."])
    
    # Scan for .nakama-0 files in selected folder
    if selected_folder:
        search_path = os.path.join(base_path, selected_folder, "*.nakama-0")
        files = glob.glob(search_path)
        files.sort()
        
        if not files:
            st.warning(f"No .nakama-0 files found in '{selected_folder}'")
            selected_file = None
        else:
            st.markdown(f"**Found {len(files)} files**")
            selected_file = st.selectbox("Select File to Visualize", files, format_func=lambda x: os.path.basename(x))
    else:
        selected_file = None

# ── Main Area ──
if selected_file:
    try:
        # Load the data
        with st.spinner(f"Reading {os.path.basename(selected_file)}..."):
            df = pd.read_parquet(selected_file)
        
        # Header Info
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("Columns", f"{len(df.columns)}")
        c3.metric("Size", f"{os.path.getsize(selected_file) / 1024:.1f} KB")
        c4.metric("Format", "Parquet")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Table View", "📋 Schema Info", "📈 Summary Stats"])
        
        with tab1:
            st.markdown("### Data Preview")
            st.dataframe(df, use_container_width=True, height=600)
            
            # Download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"{os.path.basename(selected_file)}.csv",
                mime='text/csv',
            )
            
        with tab2:
            st.markdown("### Column Definitions")
            schema_df = pd.DataFrame({
                "Column": df.columns,
                "Type": [str(t) for t in df.dtypes],
                "Non-Null Count": df.count().values,
                "Unique Values": [df[col].nunique() for col in df.columns]
            })
            st.table(schema_df)
            
        with tab3:
            st.markdown("### Numerical Summary")
            st.write(df.describe())
            
    except Exception as e:
        st.error(f"❌ Error reading Parquet file: {e}")
        st.info("Ensure the file is a valid Parquet format and that 'pyarrow' or 'fastparquet' is installed.")
else:
    st.info("👈 Please select a data folder and file from the sidebar to begin.")
    
    # Quick help
    st.markdown("""
    ### How to use:
    1. Select a folder from `data/raw/` (for example, `February_10`) in the sidebar.
    2. Choose a specific `.nakama-0` file.
    3. The data will be displayed in an interactive table.
    
    **Note:** Files with the `.nakama-0` extension are internally stored as Apache Parquet files.
    """)
