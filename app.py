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
# Wrap in function to potentially cache later if needed, but primarily for structure
@st.cache_data # Cache the data loading based on file content
def load_data(file):
    try:
        df = pd.read_excel(file, sheet_name=0)
        if df.shape[1] < 2:
            st.error("Error: Excel sheet needs at least two columns (Opportunity | Differentiator1 | ...).")
            return None, None, None, None
        all_potential_differentiators = df.columns[1:].tolist()
        differentiators = [
            d for d in all_potential_differentiators
            if d.strip().lower() not in ['score', 'total score']
        ]
        if df.empty or df.shape[0] < 1:
            st.error("Error: Excel sheet has no data rows.")
            return None, None, None, None
        opportunity_col_name = df.columns[0]
        business_opportunities = df[opportunity_col_name].dropna().unique().tolist()
        if not differentiators or not business_opportunities:
            st.error("Error: Could not extract opportunities or valid differentiators. Check Excel format.")
            return None, None, None, None
        # Set index after validation
        df.set_index(opportunity_col_name, inplace=True)
        return df, differentiators, business_opportunities, opportunity_col_name
    except ImportError:
        st.error("Error: Missing 'openpyxl'. Run: pip install openpyxl")
        st.stop()
    except Exception as e:
        st.error(f"Error loading or processing Excel file: {e}")
        st.stop()

df_defaults, differentiators, business_opportunities, opportunity_col_name = load_data(file_name)

# Stop if data loading failed
if df_defaults is None:
    st.stop()

# --- Initialize Session State for Scores using Defaults from Excel ---
if 'scores' not in st.session_state:
    st.session_state.scores = {}
    initialization_warnings = []
    for opportunity in business_opportunities:
        for differentiator in differentiators: # Use filtered list
            # *** Ensure key generation is consistent ***
            slider_key = f"{opportunity}_{differentiator}"
            default_value_fallback = 3
            try:
                if differentiator in df_defaults.columns:
                    raw_value = df_defaults.loc[opportunity, differentiator]
                    if pd.notna(raw_value) and isinstance(raw_value, (int, float, np.number)):
                        clamped_value = int(round(float(raw_value)))
                        final_value = max(1, min(5, clamped_value))
                        st.session_state.scores[slider_key] = final_value # Assign to state
                        if final_value != clamped_value:
                            initialization_warnings.append(f"Clamped value for '{opportunity}' / '{differentiator}' from {raw_value} to {final_value}.")
                    else:
                        st.session_state.scores[slider_key] = default_value_fallback # Assign fallback
                        if pd.notna(raw_value):
                            initialization_warnings.append(f"Non-numeric value '{raw_value}' found for '{opportunity}' / '{differentiator}'. Using default {default_value_fallback}.")
                        else:
                            initialization_warnings.append(f"Missing value for '{opportunity}' / '{differentiator}'. Using default {default_value_fallback}.")
                else:
                    initialization_warnings.append(f"Differentiator column '{differentiator}' not found for defaults. Using default {default_value_fallback}.")
                    st.session_state.scores[slider_key] = default_value_fallback # Assign fallback
            except KeyError:
                initialization_warnings.append(f"Could not find opportunity '{opportunity}' in index for defaults. Using default {default_value_fallback} for '{differentiator}'.")
                st.session_state.scores[slider_key] = default_value_fallback # Assign fallback
            except Exception as e:
                initialization_warnings.append(f"Error reading default for '{opportunity}' / '{differentiator}': {e}. Using default {default_value_fallback}.")
                st.session_state.scores[slider_key] = default_value_fallback # Assign fallback

    # Store warnings in session state too, so they persist if needed
    st.session_state.initialization_warnings = initialization_warnings


# --- Live Score Calculation & Sidebar Display ---
live_results = {}
# Ensure session state 'scores' exists before trying to calculate from it
if 'scores' in st.session_state:
    for opportunity in business_opportunities:
        total_score = 0
        for differentiator in differentiators: # Use filtered list
             # *** Ensure key generation is consistent ***
            slider_key = f"{opportunity}_{differentiator}"
            # Read from session state, fallback to 3 if key is somehow missing
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

# *** NEW: Debug Section to view raw session state scores ***
st.sidebar.subheader("Debug: Session State Scores")
# Display the scores dictionary. It should update when sliders move.
if 'scores' in st.session_state:
    st.sidebar.json(st.session_state.scores, expanded=False)
else:
    st.sidebar.warning("Session state 'scores' not initialized yet.")
st.sidebar.markdown("---")
# *** End of New Debug Section ***


# --- Main Area: Form for Rating ---
col_spacer1, col_main, col_spacer2 = st.columns([1, 3, 1])

with col_main:
    st.header("Rate Each Opportunity (1-5)")
    st.write("Adjust sliders for relevant differentiators. Scores calculated live in sidebar.")

    # Display initialization notes if they exist in session state
    if 'initialization_warnings' in st.session_state and st.session_state.initialization_warnings:
         with st.expander("Initialization Notes (Defaults)"):
             st.write("These notes indicate if default values from Excel could not be read correctly:")
             for warning in st.session_state.initialization_warnings:
                 st.warning(warning)

    with st.form("rating_form"):
        for opportunity in business_opportunities:
            st.markdown(f"#### {opportunity}")
            cols = st.columns(len(differentiators))
            for i, differentiator in enumerate(differentiators): # Use filtered list
                # *** Ensure key generation is consistent ***
                slider_key = f"{opportunity}_{differentiator}"
                with cols[i]:
                    # *** Ensure slider uses the same key ***
                    st.slider(
                        label=differentiator,
                        min_value=1,
                        max_value=5,
                        key=slider_key, # Links slider to st.session_state.scores[slider_key]
                    )
            st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Confirm Ratings")

    if submitted:
        st.header("Confirmed Scores")
        st.success("Ratings confirmed!")
        st.dataframe(
            live_results_df,
            use_container_width=True,
            hide_index=True
            )
        st.subheader("Confirmed Score Comparison Chart")
        # Ensure chart_df is created correctly if live_results_df is not empty
        if not live_results_df.empty:
             chart_df = live_results_df.set_index('Business Opportunity')
             st.bar_chart(chart_df)
        else:
             st.warning("No confirmed scores to display in chart.")
