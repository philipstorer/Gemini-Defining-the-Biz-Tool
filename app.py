# Import necessary libraries
import streamlit as st
import pandas as pd
import os
import numpy as np # Import numpy for checking numeric types

# --- Configuration ---
st.set_page_config(page_title="Business Opportunity Evaluator", layout="wide")
st.title("Evaluate Business Opportunities Against Differentiators")

# --- File Path ---
file_name = 'Defining the business.xlsx'

# Check if the file exists
if not os.path.exists(file_name):
    st.error(f"Error: The file '{file_name}' was not found.")
    st.warning(f"Please ensure '{file_name}' is in the same directory as app.py.")
    st.stop()

# --- Data Loading and Preparation ---
try:
    # Read the first sheet
    df_defaults = pd.read_excel(file_name, sheet_name=0)

    # --- Data Extraction ---
    if df_defaults.shape[1] < 2:
        st.error("Error: Excel sheet needs at least two columns (Opportunity | Differentiator1 | ...).")
        st.stop()

    # Get all column names after the first one
    all_potential_differentiators = df_defaults.columns[1:].tolist()

    # *** NEW: Filter out columns named 'Score' (case-insensitive) ***
    differentiators = [
        d for d in all_potential_differentiators
        if d.strip().lower() not in ['score', 'total score'] # Exclude columns named Score or Total Score
    ]

    # Inform user if a score column was excluded from sliders
    if len(differentiators) < len(all_potential_differentiators):
        excluded_cols = [d for d in all_potential_differentiators if d not in differentiators]
        st.info(f"Note: Found column(s) named like 'Score' ({', '.join(excluded_cols)}) in the input. These columns will not have input sliders.")

    if df_defaults.empty or df_defaults.shape[0] < 1:
        st.error("Error: Excel sheet has no data rows.")
        st.stop()
    opportunity_col_name = df_defaults.columns[0]
    business_opportunities = df_defaults[opportunity_col_name].dropna().unique().tolist()

    # Now 'differentiators' list only contains columns that should have sliders
    if not differentiators or not business_opportunities:
        st.error("Error: Could not extract opportunities or valid differentiators (after excluding 'Score' columns). Check Excel format.")
        st.stop()

    # Set the opportunity column as the index for easy lookup of defaults
    df_defaults.set_index(opportunity_col_name, inplace=True)

except FileNotFoundError:
    st.error(f"Error: File '{file_name}' not found.")
    st.stop()
except ImportError:
    st.error("Error: Missing 'openpyxl'. Run: pip install openpyxl")
    st.stop()
except Exception as e:
    st.error(f"Error loading or processing Excel file: {e}")
    st.stop()


# --- Initialize Session State for Scores using Defaults from Excel ---
# Uses the filtered 'differentiators' list
if 'scores' not in st.session_state:
    st.session_state.scores = {}
    initialization_warnings = []
    # Only loop through the *filtered* list of differentiators for sliders
    for opportunity in business_opportunities:
        for differentiator in differentiators: # Uses filtered list
            slider_key = f"{opportunity}_{differentiator}"
            default_value = 3 # Default fallback value

            try:
                # Look up the value in the DataFrame using the differentiator name
                # Check if differentiator column exists in the original df before accessing
                if differentiator in df_defaults.columns:
                    raw_value = df_defaults.loc[opportunity, differentiator]
                    # Check if the value is numeric and not NaN
                    if pd.notna(raw_value) and isinstance(raw_value, (int, float, np.number)):
                        clamped_value = int(round(float(raw_value)))
                        default_value = max(1, min(5, clamped_value))
                        if default_value != clamped_value:
                             initialization_warnings.append(f"Clamped value for '{opportunity}' / '{differentiator}' from {raw_value} to {default_value}.")
                    elif pd.notna(raw_value): # Value exists but is not numeric
                        initialization_warnings.append(f"Non-numeric value '{raw_value}' found for '{opportunity}' / '{differentiator}'. Using default 3.")
                else:
                     initialization_warnings.append(f"Differentiator column '{differentiator}' not found for defaults. Using default 3.")

            except KeyError:
                 initialization_warnings.append(f"Could not find entry for '{opportunity}' / '{differentiator}'. Using default 3.")
            except Exception as e:
                 initialization_warnings.append(f"Error reading default for '{opportunity}' / '{differentiator}': {e}. Using default 3.")

            st.session_state.scores[slider_key] = default_value

    # Display warnings if any issues occurred during default value loading
    if initialization_warnings:
        with st.expander("Initialization Notes (Defaults)"):
            for warning in initialization_warnings:
                st.warning(warning)


# --- Live Score Calculation & Sidebar Display ---
# Uses the filtered 'differentiators' list
live_results = {}
for opportunity in business_opportunities:
    total_score = 0
    # Calculate score based ONLY on the filtered differentiators (those with sliders)
    for differentiator in differentiators: # Uses filtered list
        slider_key = f"{opportunity}_{differentiator}"
        total_score += st.session_state.scores.get(slider_key, 3)
    live_results[opportunity] = total_score

live_results_df = pd.DataFrame(list(live_results.items()), columns=['Business Opportunity', 'Current Score'])
live_results_df = live_results_df.sort_values(by='Current Score', ascending=False).reset_index(drop=True)

st.sidebar.subheader("Live Calculated Scores") # Renamed for clarity
st.sidebar.dataframe(
    live_results_df,
    use_container_width=True,
    hide_index=True
    )
st.sidebar.markdown("---")

# --- Main Area: Form for Rating ---
# Uses the filtered 'differentiators' list
st.header("Rate Each Opportunity (1-5)")
st.write("Adjust sliders for relevant differentiators. Scores calculated live in sidebar.")

with st.form("rating_form"):
    for opportunity in business_opportunities:
        st.markdown(f"#### {opportunity}")
        # Create columns ONLY for the filtered differentiators
        cols = st.columns(len(differentiators)) # Uses filtered list count
        for i, differentiator in enumerate(differentiators): # Uses filtered list
            slider_key = f"{opportunity}_{differentiator}"
            with cols[i]:
                st.slider(
                    label=differentiator, # Display the actual differentiator name
                    min_value=1,
                    max_value=5,
                    key=slider_key,
                )
        st.markdown("<br>", unsafe_allow_html=True)

    submitted = st.form_submit_button("Confirm Ratings")

# --- Display Final Results After Submission (Optional) ---
if submitted:
    st.header("Confirmed Scores")
    st.success("Ratings confirmed!")
    st.dataframe(
        live_results_df,
        use_container_width=True,
        hide_index=True
        )
    st.subheader("Confirmed Score Comparison Chart")
    chart_df = live_results_df.set_index('Business Opportunity')
    st.bar_chart(chart_df)
