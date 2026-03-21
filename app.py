"""Main Streamlit frontend with split chat/map itinerary experience."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import uuid

import streamlit as st
from streamlit_folium import st_folium

import config
from agents import TravelTeam
from models import UserPreferences
from ui.itinerary_parser import DayPlan, parse_itinerary_markdown
from ui.map_view import build_itinerary_map

TRAVEL_STYLE_OPTIONS = ["Adventure", "Cultural", "Foodie", "Relaxation"]
SPECIAL_REQUIREMENTS_OPTIONS = ["Vegetarian", "Wheelchair accessible", "Family-friendly"]
MODEL_PROVIDER_OPTIONS = ["Groq (active)", "OpenAI (coming soon)", "Anthropic (coming soon)"]
AGENT_STAGE_MESSAGES = [
    "Research Agent is gathering destination intel...",
    "Itinerary Planner is sequencing your days...",
    "Budget Agent is estimating spend by stop...",
    "Local Expert is adding cultural context...",
]

st.set_page_config(
    page_title="Travel-Seek Planner",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --surface: #f7f7f4;
        --ink: #1e1f24;
        --accent: #0f766e;
        --accent-2: #f59e0b;
        --panel: rgba(255, 255, 255, 0.82);
    }
    .stApp {
        background:
            radial-gradient(circle at 15% 20%, #fef3c7 0%, rgba(254,243,199,0) 35%),
            radial-gradient(circle at 82% 12%, #ccfbf1 0%, rgba(204,251,241,0) 40%),
            linear-gradient(160deg, #f8fafc 0%, #ecfeff 100%);
        color: var(--ink);
    }
    .planner-hero {
        border: 1px solid rgba(15,118,110,0.25);
        border-radius: 16px;
        background: var(--panel);
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 22px rgba(0,0,0,0.08);
    }
    .planner-hero h3 {
        margin: 0 0 0.45rem 0;
        color: #115e59;
    }
    .stop-note {
        border-left: 4px solid #14b8a6;
        padding-left: 0.8rem;
        color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _initialize_session_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "preferences" not in st.session_state:
        st.session_state.preferences = UserPreferences()
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "travel_plan" not in st.session_state:
        st.session_state.travel_plan = None
    if "activity_feed" not in st.session_state:
        st.session_state.activity_feed = []
    if "geocode_cache" not in st.session_state:
        st.session_state.geocode_cache = {}
    if "model_provider" not in st.session_state:
        st.session_state.model_provider = MODEL_PROVIDER_OPTIONS[0]


def _add_activity(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.activity_feed.insert(0, f"{timestamp} | {message}")
    st.session_state.activity_feed = st.session_state.activity_feed[:24]


def _reset_session() -> None:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.preferences = UserPreferences()
    st.session_state.chat_messages = []
    st.session_state.travel_plan = None
    st.session_state.activity_feed = []
    st.session_state.geocode_cache = {}


def _parse_date_range(date_value) -> tuple[date, date, int]:
    today = date.today()
    default_start = today + timedelta(days=7)
    default_end = default_start + timedelta(days=max(config.DEFAULT_DURATION - 1, 1))
    if isinstance(date_value, tuple) and len(date_value) == 2:
        start_date, end_date = date_value
    elif isinstance(date_value, list) and len(date_value) == 2:
        start_date, end_date = date_value[0], date_value[1]
    elif isinstance(date_value, date):
        start_date, end_date = date_value, date_value
    else:
        start_date, end_date = default_start, default_end
    if end_date < start_date:
        end_date = start_date
    duration = (end_date - start_date).days + 1
    return start_date, end_date, duration


def _render_day_cards(day_plans: list[DayPlan]) -> None:
    if not day_plans:
        st.info("No day sections detected yet. Ask the planner for a day-by-day itinerary format.")
        return
    tabs = st.tabs([day.label for day in day_plans])
    for day_plan, day_tab in zip(day_plans, tabs):
        with day_tab:
            if not day_plan.stops:
                st.warning("No stop-level bullets were detected for this day.")
                continue
            for stop in day_plan.stops:
                header = f"{stop.time} | {stop.name}"
                with st.expander(header, expanded=False):
                    col_1, col_2, col_3 = st.columns(3)
                    col_1.metric("Duration", stop.duration)
                    col_2.metric("Rating", stop.rating)
                    col_3.metric("Cost Estimate", stop.cost_estimate)
                    st.caption(f"Distance to next: {stop.distance_to_next}")
                    st.markdown(f"<div class='stop-note'>{stop.notes}</div>", unsafe_allow_html=True)


def _run_with_activity(status_label: str, run_fn):
    with st.status(status_label, expanded=True) as status:
        for stage in AGENT_STAGE_MESSAGES:
            status.write(stage)
            _add_activity(stage)
        result = run_fn()
        status.update(label="Delegation complete", state="complete")
    return result


_initialize_session_state()

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.title("Trip Configuration")

    prefs = st.session_state.preferences
    destination = st.text_input("Destination", value=prefs.destination or "")
    present_location = st.text_input("Current location", "")
    date_range = st.date_input(
        "Date range",
        value=(date.today() + timedelta(days=7), date.today() + timedelta(days=11)),
        min_value=date.today(),
    )
    start_date, end_date, duration = _parse_date_range(date_range)

    travelers = st.number_input(
        "Number of travelers",
        min_value=1,
        max_value=20,
        value=prefs.group_size or 2,
        step=1,
    )
    budget_tier = st.select_slider(
        "Budget tier",
        options=["Budget", "Mid-range", "Luxury"],
        value=prefs.budget_tier if prefs.budget_tier in ["Budget", "Mid-range", "Luxury"] else "Mid-range",
    )
    travel_style = st.multiselect(
        "Travel style",
        options=TRAVEL_STYLE_OPTIONS,
        default=prefs.travel_style if prefs.travel_style else ["Cultural", "Foodie"],
    )
    special_requirements = st.multiselect(
        "Special requirements",
        options=SPECIAL_REQUIREMENTS_OPTIONS,
        default=prefs.special_requirements,
    )
    model_provider = st.selectbox(
        "Model provider",
        options=MODEL_PROVIDER_OPTIONS,
        index=MODEL_PROVIDER_OPTIONS.index(st.session_state.model_provider),
    )
    st.session_state.model_provider = model_provider

    if model_provider != MODEL_PROVIDER_OPTIONS[0]:
        st.info("Only Groq is wired in backend right now. Selection is captured for future providers.")

    prefs.destination = destination or prefs.destination
    prefs.num_days = duration
    prefs.budget_tier = budget_tier
    prefs.travel_style = travel_style
    prefs.group_size = int(travelers)
    prefs.special_requirements = special_requirements

    st.divider()
    st.subheader("Extracted Preferences")
    st.text(prefs.summary())

    st.divider()
    st.subheader("Live Agent Activity")
    if st.session_state.activity_feed:
        for line in st.session_state.activity_feed[:8]:
            st.caption(line)
    else:
        st.caption("No activity yet. Generate a plan or chat to see delegation steps.")

    if st.button("Reset Session"):
        _reset_session()
        st.rerun()

try:
    travel_agent = TravelTeam(session_id=st.session_state.session_id)

    if not travel_agent.mcp_available:
        st.warning(
            f"{travel_agent.mcp_status_reason or 'Google Places API unavailable.'} "
            "Using DuckDuckGo fallback. Venue precision may be lower."
        )
    if not travel_agent.weather_available:
        st.info(
            f"{travel_agent.weather_status_reason or 'OpenWeather API unavailable.'} "
            "Weather guidance may rely on non-forecast research."
        )

    st.title("Travel-Seek Planning Desk")
    st.caption("Left side for conversation. Right side for map, cards, and full itinerary context.")

    col_chat, col_itinerary = st.columns([2, 3], gap="large")

    with col_chat:
        st.subheader("Chat Planner")
        if not st.session_state.chat_messages:
            st.info("Start by generating a plan or asking for trip ideas in the chat box below.")

        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask to modify your itinerary, budget, pace, or themes...")
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            _add_activity("User sent a chat update request.")
            with st.chat_message("assistant"):
                response = _run_with_activity(
                    "Delegating your request across the travel team...",
                    lambda: travel_agent.chat(user_input, st.session_state.preferences),
                )
                st.markdown(response)

            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.session_state.travel_plan = response
            _add_activity("Chat response delivered.")
            st.rerun()

    with col_itinerary:
        st.markdown(
            f"""
            <div class="planner-hero">
                <h3>Trip Snapshot</h3>
                <p><strong>Destination:</strong> {destination or "Not set yet"}</p>
                <p><strong>Dates:</strong> {start_date.isoformat()} to {end_date.isoformat()} ({duration} days)</p>
                <p><strong>Travelers:</strong> {travelers} | <strong>Budget:</strong> {budget_tier}</p>
                <p><strong>Style:</strong> {", ".join(travel_style) if travel_style else "No style selected"}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Generate Full Itinerary", type="primary", use_container_width=True):
            if not destination:
                st.warning("Please add a destination in the sidebar before generating.")
            else:
                _add_activity("One-shot itinerary generation started.")
                generated_plan = _run_with_activity(
                    "Running full-team itinerary generation...",
                    lambda: travel_agent.generate_travel_plan(
                        destination,
                        present_location,
                        start_date,
                        end_date,
                        budget_tier,
                        travel_style,
                        duration,
                    ),
                )
                if generated_plan:
                    st.session_state.travel_plan = generated_plan
                    st.session_state.chat_messages.append({"role": "assistant", "content": generated_plan})
                    _add_activity("Itinerary generation complete.")
                    st.success("Plan generated. Map and day cards updated.")

        if st.session_state.travel_plan:
            day_plans = parse_itinerary_markdown(st.session_state.travel_plan)
            itinerary_map = build_itinerary_map(
                day_plans=day_plans,
                destination=destination,
                geocode_cache=st.session_state.geocode_cache,
            )
            st.subheader("Interactive Map")
            if itinerary_map:
                st_folium(itinerary_map, height=430, use_container_width=True, key="itinerary_map")
            else:
                st.info(
                    "Map markers appear when day stops include recognizable place names or coordinates."
                )

            st.subheader("Day-by-Day Cards")
            _render_day_cards(day_plans)

            with st.expander("Open raw itinerary markdown"):
                st.markdown(st.session_state.travel_plan)
        else:
            st.info("No itinerary yet. Click 'Generate Full Itinerary' to populate map and day cards.")

except Exception as exc:
    st.error(f"Application Error: {str(exc)}")
