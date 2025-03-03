# AgentForge

An AI meta-agent system designed to autonomously create and optimize specialized AI agents based on user requirements and collected information.

## 🌟 Overview

AgentForge is an ambitious project that aims to create a meta-agent capable of:

1. Understanding user needs and requirements for specialized AI agents
2. Designing optimal agent architectures based on gathered information
3. Automatically generating custom agents with appropriate behaviors
4. Continuously refining and improving agent performance

The current implementation represents an initial proof of concept, demonstrating the foundational technology that will enable agent generation using a JSON-based configuration system. This serves as the core mechanism that the meta-agent will leverage to craft specialized agents.

## ✨ Current Features (PoC)

- **JSON-based Agent Generation**: Create full-fledged LangGraph agents from configuration files
- **Modular Architecture**: Easily define nodes of various types (LLM, web search, etc.)
- **Configurable Graph**: Flexible workflow definition by connecting nodes with edges
- **Web Interface**: React-based UI for interacting with agents
- **FastAPI Backend**: Robust API for agent communication
- **Extensibility**: Prepared for adding new node types and functionalities

## 🚀 Getting Started

### Prerequisites

- Python 3.10+ 
- Node.js 18+
- An OpenAI API key (set in `.env` file)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd chameleon-ai-agent
   ```

2. Set up the environment variables:
   ```bash
   cp example.env .env
   # Edit .env to add your OpenAI API key
   ```

3. Run the application:
   ```bash
   ./run.sh
   ```

   This will:
   - Activate the Python virtual environment (if it exists)
   - Install required dependencies
   - Start the FastAPI backend server
   - Start the React frontend development server

4. Open your browser and navigate to:
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

## 🛠️ How to Use

1. **Chat with Core Agent**: Start by chatting with the core agent to describe what kind of agent you want to create
2. **Generate Agent**: Once the agent configuration is ready (indicated in the Agent State panel), click the "Generate Agent" button
3. **Interact with Generated Agent**: After generation, you can interact with your new agent in the right panel

## 🚀 Future Development Directions

- Meta-agent that interprets client needs and generates optimal agent specifications
- User interface for visually designing agents
- Library of ready-made, specialized agent components
- Ability to combine agents into more complex systems
- Self-improving agents that learn from interactions

## ⚠️ Project Status

This project is currently in the Proof of Concept phase. The current code demonstrates the possibility of creating agents based on a JSON file, which forms the foundation for further development of the platform for building adaptive, specialized AI agents.

---

*Created as part of the [AI Craftsman](https://kurkowski.substack.com) Weekly Challenge series.* 
