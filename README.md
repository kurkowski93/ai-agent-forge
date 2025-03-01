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
- **Extensibility**: Prepared for adding new node types and functionalities

## 🚀 Future Development Directions

- Meta-agent that interprets client needs and generates optimal agent specifications
- User interface for visually designing agents
- Library of ready-made, specialized agent components
- Ability to combine agents into more complex systems
- Self-improving agents that learn from interactions

## 🛠️ How to Use (Current PoC)

1. Define your agent in a JSON file according to the schema in `example_config.json`
2. Use the `create_agent_from_config()` function to generate the agent
3. Run the agent with selected input parameters

## ⚠️ Project Status

This project is currently in the Proof of Concept phase. The current code demonstrates the possibility of creating agents based on a JSON file, which forms the foundation for further development of the platform for building adaptive, specialized AI agents.

---

*Created as part of the [AI Craftsman](https://kurkowski.substack.com) Weekly Challenge series.* 
