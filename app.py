
# Import necessary libraries
import streamlit as st
import pandas as pd
import os # Import os module to check file existence

# --- Configuration ---
st.set_page_config(page_title="Business Opportunity Evaluator", layout="wide")
st.title("Evaluate Business Opportunities Against Differentiators")

# --- File Path ---
# Define the expected Excel file name
file_name = 'Defining the business.xlsx' # Expecting .xlsx file

# Check if the file exists in the current directory
if not os.path.exists(file_name):
    st.error(f"Error: The file '{file_name}' was not found in the application's root directory.")
    st.warning(f"Please ensure you have added the Excel file '{file_name}' to the repository/directory.")
    st.stop() # Stop execution if file is not found

# --- Data Loading ---
try:
    # Read the FIRST SHEET of the Excel file.
    # Requires openpyxl: pip install openpyxl
    df = pd.read_excel(file_name, sheet_name=0) # Read the first sheet (index 0)

    # --- Data Extraction ---
    if df.shape[1] < 2:
        st.error("Error: The Excel sheet seems to have less than two columns. Cannot identify differentiators.")
        st.stop()
    differentiators = df.columns[1:].tolist()
    if not differentiators:
        st.error("Could not find differentiator names in the first row (starting from the second column). Please check the Excel file format.")
        st.stop()

    if df.empty or df.shape[0] < 1:
         st.error("Error: The Excel sheet appears to be empty or has no data rows.")
         st.stop()
    opportunity_col_name = df.columns[0]
    business_opportunities = df[opportunity_col_name].dropna().unique().tolist()
    if not business_opportunities:
        st.error(f"Could not find any business opportunities in the first column ('{opportunity_col_name}'). Please check the Excel file.")
        st.stop()

    # --- Sidebar Info ---
    st.sidebar.success(f"Successfully loaded '{file_name}'.")
    st.sidebar.write(f"Reading data from the first sheet.")
    st.sidebar.write(f"Found {len(business_opportunities)} opportunities and {len(differentiators)} differentiators.")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Opportunities Found:")
    st.sidebar.dataframe(pd.DataFrame(business_opportunities, columns=['Opportunity Name']), hide_index=True)
    st.sidebar.markdown("---")
    st.sidebar.subheader("Differentiators Found:")
    st.sidebar.dataframe(pd.DataFrame(differentiators, columns=['Differentiator Name']), hide_index=True)

    # --- Form for Rating ---
    st.header("Rate Each Opportunity (1-5)")
    st.write("Use the sliders to rate how relevant each differentiator is to the business opportunity (1 = Low Relevance, 5 = High Relevance).")

    if 'scores' not in st.session_state:
        st.session_state.scores = {}
        # Initialize scores with a default value (e.g., 3)
        for opportunity in business_opportunities:
            for differentiator in differentiators:
                 slider_key = f"{opportunity}_{differentiator}"
                 st.session_state.scores[slider_key] = 3

    with st.form("rating_form"):
        for opportunity in business_opportunities:
            st.markdown(f"#### {opportunity}")
            cols = st.columns(len(differentiators))
            for i, differentiator in enumerate(differentiators):
                slider_key = f"{opportunity}_{differentiator}"
                with cols[i]:
                   current_value = st.session_state.scores.get(slider_key, 3)
                   st.session_state.scores[slider_key] = st.slider(
                       label=differentiator,
                       min_value=1,
                       max_value=5,
                       value=current_value,
                       key=slider_key
                   )
            st.markdown("---") # Separator

        submitted = st.form_submit_button("Calculate Total Scores")

    # --- Display Results ---
    if submitted:
        st.header("Results: Total Scores per Business Opportunity")
        results = {}
        for opportunity in business_opportunities:
            total_score = 0
            for differentiator in differentiators:
                slider_key = f"{opportunity}_{differentiator}"
                total_score += st.session_state.scores.get(slider_key, 0) # Use get with default 0
            results[opportunity] = total_score

        results_df = pd.DataFrame(list(results.items()), columns=['Business Opportunity', 'Total Score'])
        results_df = results_df.sort_values(by='Total Score', ascending=False).reset_index(drop=True)

        st.dataframe(results_df, use_container_width=True)

        if not results_df.empty:
            st.subheader("Score Comparison Chart")
            chart_df = results_df.set_index('Business Opportunity')
            st.bar_chart(chart_df)
        else:
            st.warning("No results to display in the chart.")

except FileNotFoundError:
    st.error(f"Error: The file '{file_name}' was not found in the application's root directory.")
    st.warning(f"Please ensure you have added the Excel file '{file_name}' to the repository/directory.")
    st.stop()
except ImportError:
    st.error("Error: Missing library required to read Excel files.")
    st.warning("Could not import the 'openpyxl' library. Please add it to your requirements.txt and ensure it's installed.")
    st.code("pip install openpyxl", language="bash")
    st.stop()
except Exception as e:
    st.error(f"An error occurred while processing the Excel file: {e}")
    st.warning(f"Please ensure the Excel file '{file_name}' (first sheet) is formatted correctly:\n"
               f"- Differentiators in the first row (starting column B).\n"
               f"- Opportunities in the first column (starting row 2).")

