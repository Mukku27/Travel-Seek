"""
app.py

The main entry point of the application. It initializes Streamlit, handles user inputs via the sidebar, 
and uses the TravelAgent from agent.py to generate travel plans or answer questions. This module also 
applies UI styling and layout configurations.
"""

import os
from datetime import datetime
import streamlit as st

# Import configuration to load API keys and settings
import config
# Import the TravelAgent class to handle AI interactions
from agent import TravelAgent

# Set page configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
    <style>
    :root {
        --primary-color: #2E86C1;
        --accent-color: #FF6B6B;
        --background-light: #F8F9FA;
        --text-color: #2C3E50;
        --hover-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .main {
        padding: 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: var(--accent-color) !important;
        color: white !important;
        font-weight: bold;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: var(--hover-shadow);
        background-color: #FF4A4A !important;
    }
    .sidebar .element-container {
        background-color: var(--background-light);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stExpander {
        background-color: #262730;
        border-radius: 10px;
        padding: 1rem;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .travel-summary {
        background-color: #262730;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    .travel-summary h4 {
        color: var(--primary-color);
        margin-bottom: 0.5rem;
    }
    .spinner-text {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--primary-color);
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar configuration for user inputs
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.title("Trip Settings")
    
    destination = st.text_input("🌍 Where would you like to go?", "")
    present_location = st.text_input("📍 What's your current location?", "")
    
    start_date = st.date_input("📅 Start Date", min_value=datetime.today())
    end_date = st.date_input("📅 End Date", min_value=start_date)
    
    # Calculate duration based on selected dates
    if start_date and end_date:
        duration = (end_date - start_date).days + 1
    else:
        duration = config.DEFAULT_DURATION
    
    budget = st.select_slider(
        "💰 What's your budget level?",
        options=["Budget", "Moderate", "Luxury"],
        value="Moderate"
    )
    
    all_styles = ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping", "Entertainment"]
    selected_styles = st.multiselect(
        "🎯 Travel Style",
        ["All"] + all_styles,
        key="style_selector"
    )
    
    travel_style = all_styles if "All" in selected_styles else selected_styles

# Initialize session state for travel plan and Q&A
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'qa_expanded' not in st.session_state:
    st.session_state.qa_expanded = False

try:
    # Initialize the travel agent
    travel_agent = TravelAgent()

    # Main UI Header
    st.title("🌎 AI Travel Planner")
    
    st.markdown(f"""
        <div class="travel-summary">
            <h4>Welcome to your personal AI Travel Assistant! 🌟</h4>
            <p>Let me help you create your perfect travel itinerary based on your preferences.</p>
            <p><strong>Destination:</strong> {destination}</p>
            <p><strong>Duration:</strong> {duration} days</p>
            <p><strong>Budget:</strong> {budget}</p>
            <p><strong>Travel Styles:</strong> {', '.join(travel_style)}</p>
        </div>
    """, unsafe_allow_html=True)

    # Button to generate the travel plan
    if st.button("✨ Generate My Perfect Travel Plan", type="primary"):
        if destination:
            try:
                with st.spinner("🔍 Researching and planning your trip..."):
                    travel_plan = travel_agent.generate_travel_plan(
                        destination,
                        present_location,
                        start_date,
                        end_date,
                        budget,
                        travel_style,
                        duration
                    )
                    st.session_state.travel_plan = travel_plan
                    st.markdown(travel_plan)
            except Exception as e:
                st.error(f"Error generating travel plan: {str(e)}")
        else:
            st.warning("Please enter a destination")

    # Q&A Section for asking specific questions about the travel plan
    st.divider()
    
    qa_expander = st.expander("🤔 Ask a specific question about your destination or travel plan", 
                              expanded=st.session_state.qa_expanded)
    
    with qa_expander:
        st.session_state.qa_expanded = True
        question = st.text_input("Your question:", placeholder="What would you like to know about your trip?")
        if st.button("Get Answer", key="qa_button"):
            if question and st.session_state.travel_plan:
                with st.spinner("🔍 Finding answer..."):
                    answer = travel_agent.answer_question(question, st.session_state.travel_plan, destination)
                    if answer:
                        st.markdown(answer)
            elif not st.session_state.travel_plan:
                st.warning("Please generate a travel plan first before asking questions.")
            else:
                st.warning("Please enter a question")
except Exception as e:
    st.error(f"Application Error: {str(e)}")
