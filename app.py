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

    # Filter out columns named 'Score' (case-insensitive)
    differentiators = [
        d for d in all_potential_differentiators
        if d.strip().lower() not in ['score', 'total score'] # Exclude columns named Score or Total Score
    ]

    # *** Removed the st.info message about excluded columns ***

    if df_defaults.empty or df_defaults.shape[0] < 1:
        st.error("Error: Excel sheet has no data rows.")
        st.stop()
    opportunity_col_name = df_defaults.columns[0]
    business_opportunities = df_defaults[opportunity_col_name].dropna().unique().tolist()

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
# This section runs only once when the app starts or session state is cleared
if 'scores' not in st.session_state:
    st.session_state.scores = {}
    initialization_warnings = [] # To store notes about default loading
    # Loop through opportunities and the *filtered* differentiators
    for opportunity in business_opportunities:
        for differentiator in differentiators: # Uses filtered list
            slider_key = f"{opportunity}_{differentiator}"
            # Default value if lookup fails or data is invalid
            default_value_fallback = 3

            try:
                # Look up the value in the DataFrame using the opportunity and differentiator names
                if differentiator in df_defaults.columns: # Check column exists in loaded data
                    raw_value = df_defaults.loc[opportunity, differentiator]

                    # Validate the raw value from the Excel sheet
                    if pd.notna(raw_value) and isinstance(raw_value, (int, float, np.number)):
                        # It's a number, round it and clamp between 1 and 5
                        clamped_value = int(round(float(raw_value)))
                        # Apply clamping: max(1, min(5, value)) ensures it's within range
                        final_value = max(1, min(5, clamped_value))

                        # Store the successfully loaded and clamped value
                        st.session_state.scores[slider_key] = final_value

                        # Note if clamping occurred (value was outside 1-5)
                        if final_value != clamped_value:
                             initialization_warnings.append(f"Clamped value for '{opportunity}' / '{differentiator}' from {raw_value} to {final_value}.")

                    else:
                        # Value is present but not a number (e.g., text)
                        st.session_state.scores[slider_key] = default_value_fallback
                        if pd.notna(raw_value): # Avoid warning for actual blank cells
                             initialization_warnings.append(f"Non-numeric value '{raw_value}' found for '{opportunity}' / '{differentiator}'. Using default {default_value_fallback}.")
                        else: # Handle blank cells slightly differently if needed, or just use fallback
                             initialization_warnings.append(f"Missing value for '{opportunity}' / '{differentiator}'. Using default {default_value_fallback}.")

                else:
                     # Should not happen if differentiator list is derived correctly, but as safeguard
                     initialization_warnings.append(f"Differentiator column '{differentiator}' not found in data for defaults. Using default {default_value_fallback}.")
                     st.session_state.scores[slider_key] = default_value_fallback

            except KeyError:
                 # Opportunity name might be missing in the index
                 initialization_warnings.append(f"Could not find opportunity '{opportunity}' in index for defaults. Using default {default_value_fallback} for '{differentiator}'.")
                 st.session_state.scores[slider_key] = default_value_fallback
            except Exception as e:
                 # Catch any other unexpected error during lookup/processing
                 initialization_warnings.append(f"Error reading default for '{opportunity}' / '{differentiator}': {e}. Using default {default_value_fallback}.")
                 st.session_state.scores[slider_key] = default_value_fallback

    # Display warnings if any issues occurred during default value loading
    # *** Reinstated this section to help debug default value issues ***
    if initialization_warnings:
        with st.expander("Initialization Notes (Defaults)"):
            st.write("These notes indicate if default values from Excel could not be read correctly:")
            for warning in initialization_warnings:
                st.warning(warning)


# --- Live Score Calculation & Sidebar Display ---
live_results = {}
for opportunity in business_opportunities:
    total_score = 0
    for differentiator in differentiators:
        slider_key = f"{opportunity}_{differentiator}"
        # Read the current value from session_state, fallback to 3 if somehow missing post-init
        total_score += st.session_state.scores.get(slider_key, 3)
    live_results[opportunity] = total_score

live_results_df = pd.DataFrame(list(live_results.items()), columns=['Business Opportunity', 'Current Score'])
live_results_df = live_results_df.sort_values(by='Current Score', ascending=False).reset_index(drop=True)

st.sidebar.subheader("Live Calculated Scores")
st.sidebar.dataframe(
    live_results_df,
    use_container_width=True,
    hide_index=True
    )
st.sidebar.markdown("---")

# --- Main Area: Form for Rating ---
st.header("Rate Each Opportunity (1-5)")
st.write("Adjust sliders for relevant differentiators. Scores calculated live in sidebar.")

with st.form("rating_form"):
    for opportunity in business_opportunities:
        st.markdown(f"#### {opportunity}")
        # Use columns for layout - this should prevent excessive width
        cols = st.columns(len(differentiators))
        for i, differentiator in enumerate(differentiators):
            slider_key = f"{opportunity}_{differentiator}"
            with cols[i]:
                st.slider(
                    label=differentiator,
                    min_value=1,
                    max_value=5,
                    key=slider_key, # Links slider to st.session_state.scores[slider_key]
                )
        st.markdown("<br>", unsafe_allow_html=True) # Add space

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
