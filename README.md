 # Travel-Seek

Travel-Seek is an AI-powered travel planning assistant that helps you create personalized travel itineraries and answer travel-related questions. The application leverages advanced AI models to provide comprehensive travel plans, including accommodation recommendations, day-by-day itineraries, and practical travel tips.

## Features

- **Personalized Travel Plans**: Generate detailed travel itineraries based on your preferences, including budget, travel style, and duration.
- **Q&A Section**: Ask specific questions about your travel plan or destination and get accurate answers.
- **Interactive UI**: User-friendly interface built with Streamlit for easy interaction and customization.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/travel-seek.git
    cd travel-seek
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv travel-seek
    source travel-seek/bin/activate  # On Windows use `travel-seek\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up environment variables:
    - Create a 

.env

 file in the root directory and add your API keys:
        ```
        GROQ_API_KEY='your_groq_api_key'
        SERPI_API_KEY='your_serpi_api_key'
        ```

## Usage

1. Run the Streamlit application:
    ```sh
    streamlit run 

app.py


    ```

2. Open your web browser and navigate to `http://localhost:8501` to access the Travel-Seek application.

3. Enter your trip details in the sidebar, including destination, current location, start and end dates, budget, and travel style.

4. Click the "✨ Generate My Perfect Travel Plan" button to create a personalized travel itinerary.

5. Use the Q&A section to ask specific questions about your travel plan or destination.

## Project Structure

```
travel-seek/
├── bin/
├── etc/
├── include/
├── lib/
├── share/
├── __pycache__/
├── 

agent.py


├── 

app.py


├── 

config.py


├── LICENSE
├── 

prompt.py

├── 

README.md


├── 

requirements.txt


├── 

utils.py


```

- `agent.py`: Contains the `TravelAgent` class that interacts with the AI model to generate travel plans and answer questions.
- `app.py`: The main entry point of the application, initializes Streamlit, handles user inputs, and displays the UI.
- `config.py`: Manages configuration settings and environment variables.
- `prompt.py`: Contains functions to generate prompt templates for creating travel plans and answering questions.
- `utils.py`: Includes helper functions used across the application.
- `requirements.txt`: Lists the dependencies required for the project.
- `.env`: Stores environment variables such as API keys (not included in the repository).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [Groq](https://groq.com/)
- [DuckDuckGo Search](https://duckduckgo.com/)
- [Google Search Results](https://serpapi.com/)

---

Happy travels with Travel-Seek! 🌍✈️- `agent.py`: Contains the `TravelAgent` class that interacts with the AI model to generate travel plans and answer questions.
- `app.py`: The main entry point of the application, initializes Streamlit, handles user inputs, and displays the UI.
- `config.py`: Manages configuration settings and environment variables.
- `prompt.py`: Contains functions to generate prompt templates for creating travel plans and answering questions.
- `utils.py`: Includes helper functions used across the application.
- `requirements.txt`: Lists the dependencies required for the project.
- `.env`: Stores environment variables such as API keys (not included in the repository).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [Groq](https://groq.com/)
- [DuckDuckGo Search](https://duckduckgo.com/)
- [Google Search Results](https://serpapi.com/)

---

Happy travels with Travel-Seek! 🌍✈️