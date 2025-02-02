"""
prompt.py

This module contains all prompt-related logic. It provides functions that generate prompt templates 
for creating a travel plan and for answering questions based on an existing travel plan.
"""

def get_travel_plan_prompt(destination, present_location, start_date, end_date, budget, travel_style, duration):
    """
    Generate the prompt for creating a comprehensive travel plan.

    Parameters:
        destination (str): The travel destination.
        present_location (str): The traveler's current location.
        start_date (str): The trip start date.
        end_date (str): The trip end date.
        budget (str): The budget level (e.g., Budget, Moderate, Luxury).
        travel_style (list): A list of travel styles (e.g., Culture, Nature).
        duration (int): Number of days for the trip.
    
    Returns:
        str: The formatted prompt string.
    """
    travel_style_str = ', '.join(travel_style)
    prompt = f"""Act as a Personalized Travel Expert.
You are a travel expert specializing in creating tailored, detailed travel plans. Design a comprehensive itinerary for a trip to {destination} spanning {duration} days, starting on {start_date} and ending on {end_date}.

Traveler Preferences:
Budget Level: {budget}
Travel Styles: {travel_style_str}
Your Task:
Provide a structured markdown response that includes the following elements:

🌞 Best Time to Visit:
 - Highlight seasonal considerations for visiting {destination}.
 - Day-by-day weather forecast from {start_date} to {end_date}.
 - Alternative date suggestions if weather is unfavorable. Include source links for all weather data.
 - Offer clothing recommendations for each day based on weather forecasts (e.g., warm jackets for cold days, light clothing for sunny days).

🏨 Accommodation Recommendations:
 - Suggest accommodations within the {budget} range.
 - Include pros and cons, prices, amenities, and booking links.
 - Indicate distance and travel time to major attractions.
 - Format your response using markdown with clear headings (##) and bullet points. Use [text](url) format for hyperlinks.
 - Verify all links are functional before including them.

🗺️ Day-by-Day Itinerary:
 - Create a detailed itinerary for each day with specific time slots (e.g., "9:00 AM–12:00 PM: Visit [Attraction]").
 - Incorporate activities, attractions, and cultural experiences that align with the specified travel styles.
 - Include booking links, costs, and recommendations for optimizing time.
 - Include only sites that exist.

🍽️ Culinary Highlights:
 - Recommend local cuisines, restaurants, and food experiences.
 - Provide suggestions based on travel styles (e.g., street food, fine dining).
 - Include price ranges, opening hours, and reservation links, where available.

💡 Practical Travel Tips:
 - List local and intercity transportation options (e.g., public transit, car rentals, taxis).
 - Provide advice on cultural etiquette, local customs, and safety.
 - Include a suggested daily budget breakdown for meals, transport, and activities.

💰 Estimated Total Trip Cost:
 - Provide an itemized expense breakdown (accommodation, transportation, meals, activities, and miscellaneous).
 - Offer budget-saving tips specific to {budget} constraints.

🚂 Transportation Details:
 - Recommend transportation options from {present_location} to {destination}.
 - Include schedules, pricing, duration, and booking links for trains, buses, or flights.

Output Requirements:
 - Use clear, easy-to-read markdown with headings and bullet points.
 - Provide source links, booking references, and maps wherever applicable.
 - Ensure all details are actionable and well-organized.
"""
    return prompt


def get_answer_question_prompt(destination, travel_plan, question):
    """
    Generate the prompt for answering a specific question based on an existing travel plan.

    Parameters:
        destination (str): The travel destination.
        travel_plan (str): The existing travel plan context.
        question (str): The specific question to answer.
    
    Returns:
        str: The formatted prompt string.
    """
    prompt = f"""Using the context of this travel plan for {destination}:

{travel_plan}

Please answer this specific question: {question}

Guidelines for your response:
1. Focus specifically on answering the question asked.
2. Reference relevant parts of the travel plan when applicable.
3. Provide new information if the travel plan doesn't cover the topic.
4. Include verified source links for any new information.
5. Keep the response concise but comprehensive.
6. Use markdown formatting for clarity.

Format your response with appropriate headings and verify all included links."""
    return prompt
