# app.py
"""
Streamlit UI for LLMS File Builder
"""
import streamlit as st
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from backend import LLMSProcessor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="LLMS File Builder",
    page_icon="🧠",
    layout="wide"
)

# Initialize session state
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'result' not in st.session_state:
    st.session_state.result = None

# Header
st.title("🧠 LLMS File Builder")
st.markdown("Convert your Screaming Frog SEO crawl into an AI-optimized LLMS.txt file")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # AI Enhancement is now mandatory - just check for API key
    st.info("✨ AI optimization is enabled for all LLMS.txt files")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.warning("⚠️ OpenAI API key not found in .env file")
        api_key = st.text_input("Enter OpenAI API Key:", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
    else:
        st.success("✅ OpenAI API key loaded")
    
    st.divider()
    
    # Export settings
    st.subheader("📁 Export Options")
    custom_filename = st.text_input(
        "Custom filename (optional):",
        placeholder="LLMS",
        help="Leave blank to use default 'LLMS' filename"
    )
    
    include_stats = st.checkbox(
        "Include statistics in output",
        value=True,
        help="Add generation date and page count to LLMS.txt"
    )

# Main content area
col1, col2 = st.columns([3, 2])

with col1:
    st.header("📤 Upload CSV File")
    
    # Instructions
    with st.expander("📋 How to export from Screaming Frog", expanded=False):
        st.markdown("""
        1. In Screaming Frog, click the **'Internal'** tab
        2. Click the Filter dropdown → Select **'HTML'**
        3. File → Export → Save as CSV
        
        This ensures you export only actual web pages, not images or scripts!
        """)
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose your Screaming Frog CSV export",
        type=['csv'],
        help="Select the CSV file exported from Screaming Frog"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Preview the CSV
        try:
            df_preview = pd.read_csv(tmp_path, nrows=5)
            st.subheader("📊 CSV Preview")
            st.dataframe(df_preview)
            
            # Validate button
            if st.button("🔍 Validate & Process", type="primary"):
                with st.spinner("Validating CSV..."):
                    processor = LLMSProcessor(api_key=os.getenv("OPENAI_API_KEY"))  # AI enhancement is always on
                    validation = processor.validate_csv(tmp_path)
                    
                    if validation['valid']:
                        st.success(f"✅ CSV validated! {validation['total_rows']} rows found")
                        
                        # Show quality analysis
                        if 'analysis' in validation:
                            analysis = validation['analysis']
                            quality_score = analysis['quality_score']
                            
                            # Quality score indicator
                            if quality_score >= 80:
                                st.success(f"Quality Score: {quality_score}/100 - Excellent!")
                            elif quality_score >= 60:
                                st.warning(f"Quality Score: {quality_score}/100 - Good")
                            else:
                                st.error(f"Quality Score: {quality_score}/100 - Needs improvement")
                            
                            if analysis['issues']:
                                with st.expander("⚠️ Quality Issues Found"):
                                    for issue in analysis['issues']:
                                        st.write(f"• {issue}")
                        
                        # Process the file
                        with st.spinner("Processing pages and enhancing with AI..."):
                            result = processor.process_file(
                                tmp_path,
                                custom_filename=custom_filename or "LLMS"
                            )
                            
                            if result['success']:
                                st.session_state.processing_complete = True
                                st.session_state.result = result
                                st.balloons()
                            else:
                                st.error(f"❌ Processing failed: {result['error']}")
                    else:
                        st.error(f"❌ Validation failed: {validation['error']}")
                        if 'available_columns' in validation:
                            with st.expander("Available columns"):
                                st.write(validation['available_columns'])
        
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
        
        finally:
            # Cleanup temp file
            if 'tmp_path' in locals():
                Path(tmp_path).unlink(missing_ok=True)

with col2:
    if st.session_state.processing_complete and st.session_state.result:
        result = st.session_state.result
        
        st.header("✅ Processing Complete!")
        
        # Statistics
        st.subheader("📈 Statistics")
        stats = result['stats']
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("Total Rows", stats['total_rows'])
            st.metric("Indexable Pages", stats['indexable_pages'])
        with col_stat2:
            st.metric("Unique Pages", stats['unique_pages'])
            total_categorized = sum(result['categories'].values())
            st.metric("Categorized", total_categorized)
        
        # Categories breakdown
        st.subheader("📁 Categories")
        categories_df = pd.DataFrame(
            list(result['categories'].items()),
            columns=['Category', 'Count']
        ).sort_values('Count', ascending=False)
        st.dataframe(categories_df, hide_index=True)
        
        # Download buttons
        st.subheader("💾 Download Files")
        
        # Read the generated file
        txt_path = result['files']['txt_path']
        
        with open(txt_path, 'r') as f:
            txt_content = f.read()
        
        # Single download button for LLMS.txt only
        st.download_button(
            label="📄 Download LLMS.txt",
            data=txt_content,
            file_name=f"{custom_filename or 'LLMS'}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
        # Preview
        with st.expander("👁️ Preview LLMS.txt", expanded=False):
            st.text(txt_content[:2000] + "\n..." if len(txt_content) > 2000 else txt_content)
        
        # Reset button
        if st.button("🔄 Process Another File"):
            st.session_state.processing_complete = False
            st.session_state.result = None
            st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #888;'>
    LLMS File Builder | Made for AI Search Optimization
</div>
""", unsafe_allow_html=True)