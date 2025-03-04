# Agent CLI 🤖

A powerful terminal-based application for creating, testing, and managing AI agents.

## Features

- 💬 Chat with core agent to design custom agents
- 🛠️ Generate agents based on your specifications
- 💾 Save and load agent configurations
- 📊 Visualize agent graphs
- 🎨 Beautiful terminal UI with emojis and colors
- 🔄 Real-time streaming of agent responses token by token
- 🐛 Detailed debug mode to see agent operations

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chameleon-ai-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure you have the required environment variables set (you can use a `.env` file):
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Starting a Conversation with the Core Agent

This is where you'll describe what you want your agent to do, and the core agent will help you design it.

```bash
python agent_cli.py chat
```

When chatting with the core agent:
- Type your messages to interact with the agent
- Type `exit` to end the conversation
- Type `generate` to generate a custom agent based on the conversation

### Testing a Saved Agent

Once you've generated and saved an agent, you can test it:

```bash
python agent_cli.py test
```

This will show you a list of saved agents to choose from.

### Listing Saved Agents

To see all your saved agent configurations:

```bash
python agent_cli.py list
```

### Debugging Agent Execution

To run an agent with detailed debugging information:

```bash
python agent_cli.py debug [AGENT_NAME]
```

If `AGENT_NAME` is not provided, the core agent will be used. This mode shows:
- Step-by-step execution details
- Node operations and state changes
- Token-by-token LLM outputs
- Ability to save debug traces

### Toggle Debug Mode

```bash
python agent_cli.py toggle-debug
```

This toggles the global debug mode flag, which can provide more detailed information in other commands.

## Streaming Features

Agent CLI provides real-time streaming of agent responses with multiple modes:

- **Token Streaming**: See agent responses as they are generated, token by token
- **Debug Streaming**: View detailed information about agent execution, including node operations
- **State Updates**: Track changes to the agent's state during execution

## Agent Configuration

Agent configurations are stored as JSON files in the `agent_configs` directory. Each configuration includes:

- Agent name and description
- Node definitions (processing steps)
- Edge definitions (connections between nodes)

## Example Workflow

1. Start a conversation: `python agent_cli.py chat`
2. Describe the agent you want to create
3. When ready, type `generate` to create the agent
4. Optionally save the agent with a custom name
5. Test your new agent

## Terminal Image Support

The application attempts to display agent graphs directly in your terminal:

- Automatic detection of image-capable terminals (iTerm2, Kitty)
- Fallback to system image viewer if terminal doesn't support images

## Requirements

- Python 3.8+
- Required Python packages (see `requirements.txt`)
- OpenAI API key
