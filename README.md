# Local-AI-Assistant
This is a local desktop AI assistant built with Python and Tkinter and that combines local LLM capabilities from Ollama with web search and weather information.

# AI Personal Assistant

This is a desktop AI assistant built with Python and Tkinter that combines local LLM capabilities with web search and weather information. It features a modern UI with dark/light theme support and persistent conversation memory.

## Features

- 💬 Local LLM-powered chat using Ollama
- 🔍 Web search integration using Google Custom Search
- ⛅ Weather information using Tomorrow.io API
- 🌓 Dark/Light theme support
- 💾 Conversation memory with importance tracking
- ⌨️ Global hotkey support (Ctrl+/ to toggle)

## Prerequisites

- Python 3.x
- Ollama running locally (for LLM capabilities)
- API keys for external services

## Installation

1. Clone this repository
2. Install required packages:
```powershell
pip install tkinter requests keyboard
```
3. Configure your API keys (see Configuration section)
4. Run the assistant:
```powershell
python personalassistant.py
```

## Configuration

Before running the assistant, you need to set up the following API keys:

### 1. Tomorrow.io Weather API
1. Sign up for a free account at [Tomorrow.io](https://www.tomorrow.io/)
2. Get your API key from the dashboard
3. Configure your local settings in `personalassistant.py`:
```python
TOMORROW_API_KEY = "your_api_key_here"  # Add your Tomorrow.io API key here
DEFAULT_LOCATION = {"lat": 0, "lon": 0}  # Set your coordinates (e.g., {"lat": 51.5074, "lon": -0.1278} for London)
DEFAULT_CITY = "Your City"  # Set your city name (e.g., "London, UK")
```

To find your coordinates:
1. Go to [Google Maps](https://www.google.com/maps)
2. Right-click on your location
3. Copy the coordinates (they will be in "latitude, longitude" format)
4. Update the `DEFAULT_LOCATION` values accordingly

### 2. Google Custom Search API
1. Create a project in the [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Custom Search API
3. Create API credentials (API key)
4. Create a [Custom Search Engine](https://programmablesearchengine.google.com/about/)
5. Get your Search Engine ID
6. Replace the placeholders in `personalassistant.py`:
```python
GOOGLE_SEARCH_API_KEY = "your_api_key_here"  # Add your Google API key here
GOOGLE_SEARCH_ENGINE_ID = "your_search_engine_id_here"  # Add your Search Engine ID here
```

## Usage

### Basic Controls
- Press `Ctrl+/` to toggle the assistant window
- Use arrow keys with Ctrl to move the window:
  - `Ctrl+↑`: Move up
  - `Ctrl+↓`: Move down
  - `Ctrl+←`: Move left
  - `Ctrl+→`: Move right
- Click the theme button (🌙/☀️) to switch between dark and light themes
- Click the 'LLM/Web' button to switch between local LLM and web search modes

### Weather Command
After configuring your location in the settings:
- Type `!weather` to get weather information for your configured location
- The weather report includes:
  - Temperature in Celsius
  - "Feels like" temperature
  - Humidity percentage
  - Current weather conditions
  - Wind speed in meters per second
- Use memory commands:
  - `!remember this`: Mark conversation as important
  - `!forget this`: Remove importance flag
  - `!wipe memory`: Clear all saved conversations

## Local LLM Setup

1. Install [Ollama](https://ollama.ai/)
2. Start the Ollama service
3. The assistant will connect to Ollama at `http://localhost:11434`

## Contributing

Feel free to submit issues and pull requests.

## License

[MIT License](LICENSE)

