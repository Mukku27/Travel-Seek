import streamlit as st
import os
from dotenv import load_dotenv
from phi.agent import Agent
from phi.model.groq import Groq
from phi.tools.serpapi_tools import SerpApiTools
from phi.tools.duckduckgo import DuckDuckGo
from datetime import datetime

load_dotenv()

# Initialize page config
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# [Previous CSS styles remain the same]
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

class TravelAgent:
    def __init__(self):
        self.agent = Agent(
            name="Comprehensive Travel Assistant",
            model=Groq(id="deepseek-r1-distill-llama-70b"),
            tools=[SerpApiTools(), DuckDuckGo()],
            instructions=[
                "You are a comprehensive travel planning assistant with expertise in all aspects of travel.",
                "For every recommendation and data point, you MUST provide working source links.",
                "Your knowledge spans across:",
                "- Seasonal travel timing and weather patterns",
                "- Transportation options and booking",
                "- Accommodation recommendations",
                "- Day-by-day itinerary planning",
                "- Local cuisine and restaurant recommendations",
                "- Practical travel tips and cultural advice",
                "- Budget estimation and cost breakdown",
                "Format all responses in markdown with clear headings (##) and bullet points.",
                "Use [text](url) format for all hyperlinks.",
                "Verify all links are functional before including them.",
                "Organize information clearly with appropriate sections based on the query type."
            ],
            show_tool_calls=True,
            markdown=True,
            debug_mode=True
        )
    def generate_travel_plan(self, destination, present_location, start_date, end_date, budget, travel_style):
        prompt = f""" Act as a Personalized Travel Expert
You are a travel expert specializing in creating tailored, detailed travel plans. Design a comprehensive itinerary for a trip to {destination} spanning {duration} days, starting on {start_date} and ending on {end_date}.

Traveler Preferences:
Budget Level: {budget}
Travel Styles: {', '.join(travel_style)}
Your Task:
Provide a structured markdown response that includes the following elements:

🌞 Best Time to Visit:
 -Highlight seasonal considerations for visiting {destination}.
 -Day-by-day weather forecast from {start_date} to {end_date}
 -Alternative date suggestions if weather is unfavorable .Include source links for all weather data.
 -Offer clothing recommendations for each day based on weather forecasts of that particular day be accurate . For example:
    -Warm jackets and boots for cold, snowy days.
    -Light, breathable clothing for warm, sunny days.
    -Raincoats and umbrellas for rainy conditions.

🏨 Accommodation Recommendations:
 -Suggest accommodations within the {budget} range.
 -Include pros and cons, prices, amenities, and booking links.
 -Indicate the distance and travel time to major attractions. 
 -Format your response using markdown with clear headings (##) and bullet points. Use [text](url) format for hyperlinks. Verify all links are functional before including them.

🗺️ Day-by-Day Itinerary:
 -Create a detailed itinerary for each day, broken into specific time slots (e.g., "9:00 AM–12:00 PM: Visit [Attraction]").
 -Incorporate activities, attractions, and cultural experiences that align with the specified travel styles.
 -Include booking links, costs, and recommendations for optimizing time and enjoyment.
 -Include sites only if the sites exist 

🍽️ Culinary Highlights:
 -Recommend local cuisines, restaurants, and food experiences.
 -Provide suggestions based on the travel styles (e.g., street food, fine dining, or unique culinary tours).
 -Include price ranges, opening hours, and reservation links, where available.

💡 Practical Travel Tips:
 -List local and intercity transportation options (e.g., public transit, car rentals, taxis).
 -Provide advice on cultural etiquette, local customs, and safety tips.
 -Include a suggested daily budget breakdown for meals, transport, and activities.

💰 Estimated Total Trip Cost:
 -Provide an itemized expense breakdown by category:
 -Accommodation, transportation, meals, activities, and miscellaneous expenses.
 -Offer budget-saving tips specific to {budget} constraints.

🚂 Transportation Details:
 -Recommend transportation options from {present_location} to {destination}.
 -Include schedules, pricing, duration, and booking links for trains, buses, or flights.

Output Requirements:
 -Use clear, easy-to-read markdown with headings and bullet points for each section.
 -Provide source links, booking references, and maps wherever applicable.
 -Ensure all details are actionable and well-organized to facilitate ease of planning.

"""
        response = self.agent.run(prompt)
        try:
            if hasattr(response, 'content'):
                clean_response = response.content.replace('∣', '|').replace('\n\n\n', '\n\n')
                st.session_state.travel_plan = clean_response
                st.markdown(clean_response)
            else:
                st.session_state.travel_plan = str(response)
                st.markdown(str(response))
        except Exception as e:
            st.error(f"Error generating travel plan: {str(e)}")
            st.info("Please try again in a few moments.")

    def answer_question(self, question, travel_plan, destination):
        prompt = f"""Using the context of this travel plan for {destination}:

{travel_plan}

Please answer this specific question: {question}

Guidelines for your response:
1. Focus specifically on answering the question asked
2. Reference relevant parts of the travel plan when applicable
3. Provide new information if the travel plan doesn't cover the topic
4. Include verified source links for any new information
5. Keep the response concise but comprehensive
6. Use markdown formatting for clarity

Format your response with appropriate headings and verify all included links."""

        return self.agent.run(prompt)

# Sidebar configuration
with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/airplane-take-off.png")
    st.title("Trip Settings")
    
    destination = st.text_input("🌍 Where would you like to go?", "")
    present_location = st.text_input("📍 What's your current location?", "")
    
    start_date = st.date_input("📅 Start Date", min_value=datetime.today())
    end_date = st.date_input("📅 End Date", min_value=start_date)
    
    if start_date and end_date:
        duration = (end_date - start_date).days + 1
    else:
        duration = 5
    
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

# Initialize session state
if 'travel_plan' not in st.session_state:
    st.session_state.travel_plan = None
if 'qa_expanded' not in st.session_state:
    st.session_state.qa_expanded = False

try:
    # Set API keys
    os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
    os.environ["SERP_API_KEY"] = os.getenv("SERP_API_KEY")

    # Initialize single travel agent
    travel_agent = TravelAgent()

    # Main UI
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
                        travel_style
                    )
                    st.session_state.travel_plan = travel_plan
                    st.markdown(travel_plan)
            except Exception as e:
                st.error(f"Error generating travel plan: {str(e)}")
        else:
            st.warning("Please enter a destination")

    # Q&A Section
    st.divider()
    
    qa_expander = st.expander("🤔 Ask a specific question about your destination or travel plan", 
                             expanded=st.session_state.qa_expanded)
    
    with qa_expander:
        st.session_state.qa_expanded = True
        question = st.text_input("Your question:", placeholder="What would you like to know about your trip?")
        if st.button("Get Answer", key="qa_button"):
            if question and st.session_state.travel_plan:
                with st.spinner("🔍 Finding answer..."):
                    try:
                        # Combine the original travel plan with the new question for context
                        context_question = f"""
                        I have a travel plan for {destination}. Here's the existing plan:
                        {st.session_state.travel_plan}

                        Now, please answer this specific question: {question}
                        
                        Provide a focused, concise answer that relates to the existing travel plan if possible.
                        """
                        response = travel_agent.run(context_question)
                        if hasattr(response, 'content'):
                            st.markdown(response.content)
                        else:
                            st.markdown(str(response))
                    except Exception as e:
                        st.error(f"Error getting answer: {str(e)}")
            elif not st.session_state.travel_plan:
                st.warning("Please generate a travel plan first before asking questions.")
            else:
                st.warning("Please enter a question")
except Exception as e:
    st.error(f"Application Error: {str(e)}")