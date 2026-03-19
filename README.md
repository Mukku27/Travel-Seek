# Travel-Seek

Travel-Seek is an AI-powered travel planning assistant that helps you create personalized travel itineraries and answer travel-related questions. The application leverages advanced AI models to provide comprehensive travel plans, including accommodation recommendations, day-by-day itineraries, and practical travel tips.

## Features

- **Personalized Travel Plans**: Generate detailed travel itineraries based on your preferences, including budget, travel style, and duration.
- **Q&A Section**: Get instant and accurate answers to travel-related questions.
- **Interactive UI**: User-friendly interface built with Streamlit for seamless interaction and customization.

## Installation

### 1. Clone the Repository
```sh
git clone https://github.com/yourusername/travel-seek.git
cd travel-seek
```

### 2. Create and Activate a Virtual Environment
```sh
python3 -m venv travel-seek
source travel-seek/bin/activate  # On Windows use `travel-seek\Scripts\activate`
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
- Create a `.env` file in the root directory and add your API keys:
```sh
GROQ_API_KEY='your_groq_api_key'
SERPI_API_KEY='your_serpi_api_key'

# Optional: enable Tavily search (alongside SerpAPI/DuckDuckGo)
USE_TAVILY=true
TAVILY_API_KEY='your_tavily_api_key'
```

## Usage

### 1. Run the Streamlit Application
```sh
streamlit run app.py
```

### 2. Access the Application
- Open your web browser and go to `http://localhost:8501`.
- Enter your trip details in the sidebar, including destination, current location, start and end dates, budget, and travel style.
- Click the **"✨ Generate My Perfect Travel Plan"** button to create a personalized itinerary.
- Use the Q&A section for specific travel queries.

## Project Structure

```
travel-seek/
├── bin/
├── etc/
├── include/
├── lib/
├── share/
├── __pycache__/
├── agent.py         # Handles AI interactions for travel planning
├── app.py           # Main entry point, initializes Streamlit and UI
├── config.py        # Manages configuration settings and environment variables
├── LICENSE          # License file
├── prompt.py        # Generates AI prompts for itinerary creation
├── README.md        # Project documentation
├── requirements.txt # Dependencies list
├── utils.py         # Utility functions used in the application
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

---

Happy travels with Travel-Seek! 🌍✈️

