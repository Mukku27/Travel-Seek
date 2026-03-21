# Travel-Seek

Travel-Seek is an AI-powered travel planning assistant that helps you create personalized travel itineraries and answer travel-related questions. The application leverages a coordinated multi-agent team (powered by Agno + Groq) and optionally enriches results with real Google Places & Directions data via a custom MCP server.

## Features

- **Multi-Agent Travel Planning**: Four specialized AI agents (Research, Itinerary, Budget, Local Expert) coordinate to produce comprehensive travel plans.
- **Google Places Integration**: Real ratings, reviews, hours, and directions via a custom MCP server backed by the Google Maps API.
- **Conversational Planning**: Chat naturally to build and refine your plan with session memory.
- **Graceful Fallback**: Works without a Google Maps key — falls back to DuckDuckGo search with a visible warning.
- **Standalone MCP Server**: The Places MCP server works independently with Claude Desktop or any MCP-compatible client.

## Installation

### 1. Clone the Repository
```sh
git clone https://github.com/Mukku27/Travel-Seek.git
cd Travel-Seek
```

### 2. Create and Activate a Virtual Environment
```sh
python3 -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:
```sh
GROQ_API_KEY='your_groq_api_key'
GOOGLE_MAPS_API_KEY='your_google_maps_api_key'   # Optional — enables Places & Directions
SERPI_API_KEY='your_serpi_api_key'

# Optional: enable Tavily search alongside SerpAPI/DuckDuckGo
USE_TAVILY='true'
TAVILY_API_KEY='your_tavily_api_key'
```

The `GOOGLE_MAPS_API_KEY` requires the following APIs enabled in your Google Cloud project:
- Places API
- Directions API
- Geocoding API

If the key is not set, the app works normally using DuckDuckGo for all research.
If `USE_TAVILY` is enabled and `TAVILY_API_KEY` is present, the research agent can use Tavily alongside DuckDuckGo.

## Usage

### Run the Streamlit Application
```sh
streamlit run app.py
```

Open your browser at `http://localhost:8501`, enter your trip details in the sidebar, and either generate a one-shot plan or chat interactively.

### Run Tests
```sh
pytest tests/ -v
```

## Project Structure

```
Travel-Seek/
├── agents/
│   ├── __init__.py
│   ├── travel_team.py        # Team orchestrator with MCP lifecycle
│   ├── research_agent.py     # DuckDuckGo + optional MCP tools
│   ├── itinerary_agent.py    # Day-by-day planner + optional Directions
│   ├── budget_agent.py       # Cost estimates via DuckDuckGo
│   └── local_expert_agent.py # Cultural tips via DuckDuckGo
├── mcp_servers/
│   ├── __init__.py
│   ├── config.py             # API key management & client factory
│   ├── places_tools.py       # Core Google Maps tool logic
│   └── places_server.py      # FastMCP server (3 tools)
├── tests/
│   ├── test_places_tools.py
│   ├── test_places_server.py
│   ├── test_mcp_config.py
│   ├── test_travel_team_fallback.py
│   ├── test_models.py
│   └── test_utils.py
├── app.py                    # Streamlit entry point
├── config.py                 # App configuration
├── models.py                 # Pydantic models
├── prompt.py                 # Prompt templates
├── utils.py                  # Response cleaning utilities
├── requirements.txt
└── README.md
```

## MCP Server

The `mcp_servers/` package exposes three Google Maps tools as a standalone MCP server:

| Tool | Description |
|------|-------------|
| `search_places` | Geocodes a location, then runs a Places Nearby Search. Returns top 5 results with name, rating, address, price level, etc. |
| `get_place_details` | Fetches rich details for a place: reviews, hours, phone, website, geometry. |
| `get_directions` | Computes directions between two locations with distance, duration, and step-by-step instructions. |

### Run Standalone (stdio)
```sh
python -m mcp_servers.places_server
```

### Run with SSE Transport
```sh
python -m mcp_servers.places_server --transport sse --port 8000
```

### Claude Desktop Configuration

Add this to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "travel-seek-places": {
      "command": "python",
      "args": ["-m", "mcp_servers.places_server"],
      "env": {
        "GOOGLE_MAPS_API_KEY": "your_key"
      }
    }
  }
}
```

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
