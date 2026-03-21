"""Main Streamlit entry point with itinerary exports."""

import uuid
from datetime import datetime
import streamlit as st

import config
from agents import TravelTeam
from export_utils import build_calendar_export, build_markdown_export, build_pdf_export
from models import UserPreferences

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    :root {
        --primary-color: #2E86C1;
        --accent-color: #FF6B6B;
        --background-light: #F8F9FA;
        --text-color: #2C3E50;
        --hover-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .main { padding: 2rem; max-width: 1200px; margin: 0 auto; }
    .stButton > button { width: 100%; border-radius: 8px; height: 3em; background-color: var(--accent-color) !important; color: white !important; font-weight: bold; font-size: 1rem; }
    .travel-summary { background-color: #262730; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "preferences" not in st.session_state:
    st.session_state.preferences = UserPreferences()
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "travel_plan" not in st.session_state:
    st.session_state.travel_plan = None

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.title("Trip Settings")

    destination = st.text_input("🌍 Where would you like to go?", "")
    present_location = st.text_input("📍 What's your current location?", "")
    start_date = st.date_input("📅 Start Date", min_value=datetime.today())
    end_date = st.date_input("📅 End Date", min_value=start_date)
    duration = (end_date - start_date).days + 1 if start_date and end_date else config.DEFAULT_DURATION
    budget = st.select_slider("💰 What's your budget level?", options=["Budget", "Moderate", "Luxury"], value="Moderate")
    all_styles = ["Culture", "Nature", "Adventure", "Relaxation", "Food", "Shopping", "Entertainment"]
    selected_styles = st.multiselect("🎯 Travel Style", ["All"] + all_styles, key="style_selector")
    travel_style = all_styles if "All" in selected_styles else selected_styles

    st.divider()
    st.subheader("Extracted Preferences")
    st.text(st.session_state.preferences.summary())

    if st.button("Reset Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.preferences = UserPreferences()
        st.session_state.chat_messages = []
        st.session_state.travel_plan = None
        st.rerun()

try:
    travel_agent = TravelTeam(session_id=st.session_state.session_id)

    if not travel_agent.mcp_available:
        st.warning(f"{travel_agent.mcp_status_reason or 'Google Places API unavailable.'} Using DuckDuckGo fallback — results may be less precise.")
    if not travel_agent.weather_available:
        st.info(f"{travel_agent.weather_status_reason or 'OpenWeather API unavailable.'} Weather guidance will fall back to general web research.")

    st.title("🌎 AI Travel Planner")
    tab_plan, tab_chat = st.tabs(["Generate Plan", "Chat with Planner"])

    with tab_plan:
        st.markdown(f"""
            <div class="travel-summary">
                <h4>Generate a complete travel plan</h4>
                <p><strong>Destination:</strong> {destination}</p>
                <p><strong>Duration:</strong> {duration} days</p>
                <p><strong>Budget:</strong> {budget}</p>
                <p><strong>Travel Styles:</strong> {', '.join(travel_style)}</p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("✨ Generate My Perfect Travel Plan", type="primary"):
            if destination:
                with st.spinner("🔍 Researching and planning your trip..."):
                    travel_plan = travel_agent.generate_travel_plan(
                        destination, present_location, start_date, end_date, budget, travel_style, duration,
                    )
                    st.session_state.travel_plan = travel_plan
                    st.markdown(travel_plan)
            else:
                st.warning("Please enter a destination")

        if st.session_state.travel_plan:
            export_col1, export_col2, export_col3 = st.columns(3)
            with export_col1:
                st.download_button(
                    "📄 Download PDF",
                    data=build_pdf_export(destination, st.session_state.travel_plan, start_date, end_date, budget, travel_style),
                    file_name=f"{destination or 'trip'}-itinerary.pdf",
                    mime="application/pdf",
                )
            with export_col2:
                st.download_button(
                    "📅 Add to Calendar",
                    data=build_calendar_export(destination, st.session_state.travel_plan, start_date),
                    file_name=f"{destination or 'trip'}-calendar.ics",
                    mime="text/calendar",
                )
            with export_col3:
                st.download_button(
                    "📝 Copy as Markdown",
                    data=build_markdown_export(st.session_state.travel_plan),
                    file_name=f"{destination or 'trip'}-itinerary.md",
                    mime="text/markdown",
                )

            with st.expander("🤔 Ask about your plan"):
                question = st.text_input("Your question:", key="plan_question")
                if st.button("Get Answer", key="qa_button"):
                    if question:
                        with st.spinner("🔍 Finding answer..."):
                            answer = travel_agent.answer_question(question, st.session_state.travel_plan, destination)
                            if answer:
                                st.markdown(answer)
                    else:
                        st.warning("Please enter a question")

    with tab_chat:
        st.markdown("""
            <div class="travel-summary">
                <h4>Conversational Travel Planner</h4>
                <p>Chat naturally to build and refine your travel plan step by step.</p>
            </div>
        """, unsafe_allow_html=True)

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if user_input := st.chat_input("Tell me about your trip plans..."):
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Planning..."):
                    response = travel_agent.chat(user_input, st.session_state.preferences)
                    st.markdown(response)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.session_state.travel_plan = response
            st.rerun()

except Exception as e:
    st.error(f"Application Error: {str(e)}")
