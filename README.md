# Chameleon AI Agent - Terminal Application

This is a terminal-based application for creating and interacting with AI agents. 
The application uses LangChain and OpenAI to create customizable AI agents with specific capabilities and personalities.

## Features

- Generate custom AI agents through conversation
- Chat with generated agents
- Simple terminal-based interface
- No web browser or frontend needed

## Requirements

- Python 3.8+
- OpenAI API Key
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```
git clone https://github.com/yourusername/chameleon-ai-agent.git
cd chameleon-ai-agent
```

2. Create a virtual environment (recommended):
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the application with:
```
./run.sh
```

Or manually:
```
python terminal_app.py
```

### Application Flow

1. **Generate Agent**: Create a custom AI agent by describing its purpose, personality, and capabilities.
2. **Chat with Agent**: Interact with your generated agent.

## Configuration

Agent configurations are stored in the `configs` directory.

## Development

This application replaces the previous web-based frontend and FastAPI backend with a simpler terminal interface, while maintaining all core functionality.

### Directory Structure

- `backend/app/services`: Core service logic for agent generation and interaction
- `backend/app/models`: Data models
- `agents_forge`: Agent implementation files
- `configs`: Stored agent configurations

## License

[MIT License]
