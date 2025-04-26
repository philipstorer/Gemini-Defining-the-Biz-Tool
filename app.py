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
    df_defaults = pd.read_excel(file_name, sheet_name=0)
    if df_defaults.shape[1] < 2:
        st.error("Error: Excel sheet needs at least two columns (Opportunity | Differentiator1 | ...).")
        st.stop()
    all_potential_differentiators = df_defaults.columns[1:].tolist()
    differentiators = [
        d for d in all_potential_differentiators
        if d.strip().lower() not in ['score', 'total score']
    ]
    if df_defaults.empty or df_defaults.shape[0] < 1:
        st.error("Error: Excel sheet has no data rows.")
        st.stop()
    opportunity_col_name = df_defaults.columns[0]
    business_opportunities = df_defaults[opportunity_col_name].dropna().unique().tolist()
    if not differentiators or not business_opportunities:
        st.error("Error: Could not extract opportunities or valid differentiators. Check Excel format.")
        st.stop()
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
if 'scores' not in st.session_state:
    st.session_state.scores = {}
    initialization_warnings = []
    for opportunity in business_opportunities:
        for differentiator in differentiators:
            slider_key = f"{opportunity}_{differentiator}"
            default_value_fallback = 3
            try:
                if differentiator in df_defaults.columns:
                    raw_value = df_defaults.loc[opportunity, differentiator]
                    if pd.notna(raw_value) and isinstance(raw_value, (int, float, np.number)):
                        clamped_value = int(round(float(raw_value)))
                        final_value = max(1, min(5, clamped_value)) # Clamp 1-5
                        st.session_state.scores[slider_key] = final_value
                        if final_value != clamped_value:
                            initialization_warnings.append(f"Clamped value for '{opportunity}' / '{differentiator}' from {raw_value} to {final_value}.")
                    else:
                        st.session_state.scores[slider_key] = default_value_fallback
                        if pd.notna(raw_value):
                            initialization_warnings.append(f"Non-numeric value '{raw_value}' found for '{opportunity}' / '{differentiator}'. Using default {default_value_fallback}.")
                        else:
                            initialization_warnings.append(f"Missing value for '{opportunity}' / '{differentiator}'. Using default {default_value_fallback}.")
                else:
                    initialization_warnings.append(f"Differentiator column '{differentiator}' not found for defaults. Using default {default_value_fallback}.")
                    st.session_state.scores[slider_key] = default_value_fallback
            except KeyError:
                initialization_warnings.append(f"Could not find opportunity '{opportunity}' in index for defaults. Using default {default_value_fallback} for '{differentiator}'.")
                st.session_state.scores[slider_key] = default_value_fallback
            except Exception as e:
                initialization_warnings.append(f"Error reading default for '{opportunity}' / '{differentiator}': {e}. Using default {default_value_fallback}.")
                st.session_state.scores[slider_key] = default_value_fallback

    # Display initialization notes (useful for debugging defaults)
    if initialization_warnings:
        # Putting warnings inside the main central column now
        pass # Warnings will be displayed below, inside the main column


# --- Live Score Calculation & Sidebar Display ---
live_results = {}
for opportunity in business_opportunities:
    total_score = 0
    for differentiator in differentiators:
        slider_key = f"{opportunity}_{differentiator}"
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
# *** NEW: Using columns to constrain the main form area width ***
col_spacer1, col_main, col_spacer2 = st.columns([1, 3, 1]) # Adjust ratios (e.g., [1,4,1]) if needed

with col_main: # Put the form and related elements in the central column
    st.header("Rate Each Opportunity (1-5)")
    st.write("Adjust sliders for relevant differentiators. Scores calculated live in sidebar.")

    # Display initialization notes inside the main central column now
    if 'initialization_warnings' in locals() and initialization_warnings:
         with st.expander("Initialization Notes (Defaults)"):
             st.write("These notes indicate if default values from Excel could not be read correctly:")
             for warning in initialization_warnings:
                 st.warning(warning)

    # Form remains inside the central column
    with st.form("rating_form"):
        for opportunity in business_opportunities:
            st.markdown(f"#### {opportunity}")
            # Use columns for layout *within* the form/central column
            cols = st.columns(len(differentiators))
            for i, differentiator in enumerate(differentiators):
                slider_key = f"{opportunity}_{differentiator}"
                with cols[i]:
                    st.slider(
                        label=differentiator,
                        min_value=1,
                        max_value=5,
                        key=slider_key,
                    )
            st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Confirm Ratings")

    # --- Display Final Results After Submission (Optional) ---
    # Keep results display within the central column as well
    if submitted:
        st.header("Confirmed Scores")
        st.success("Ratings confirmed!")
        st.dataframe(
            live_results_df,
            use_container_width=True, # Use width of the central column
            hide_index=True
            )
        st.subheader("Confirmed Score Comparison Chart")
        chart_df = live_results_df.set_index('Business Opportunity')
        st.bar_chart(chart_df)
