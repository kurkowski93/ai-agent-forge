from agents_forge.core_agent.utils.state import AgentCreatorState
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage
from enum import Enum
from agents_forge.core_agent.utils.helper_models import NextStep
from agents_forge.agents_generation.config_schema import AgentConfig
import logging

# Configure logger
logger = logging.getLogger(__name__)



def step_planner(state: AgentCreatorState) -> AgentCreatorState:
    """Plan the next step in agent creation based on user input and current state."""
    logger.info(f"Executing step_planner with blueprint: {state.agent_blueprint}")
    
    system_prompt = SystemMessage(content=f"""
You're expert agent creator. Based on current state decide what is best next step to do:
1) UPDATE_BLUEPRINT - when you know more from mesages thats already in blueprint -> always do this and keep blueprint updated
2) ASK_FOLLOWUP - when you need more information from user to create a good agent
3) GENERATE_AGENT - when you have enough information to generate a custom agent, and your blueprint is fully updated

Blueprint: {state.agent_blueprint if state.agent_blueprint else "No blueprint yet"}
Message: {state.messages}

Respond with the next step:
""")
    
    class PlannerResponse(BaseModel):
        next_step: NextStep = Field(description="Next step to do")
        
    logger.info("Querying LLM for step planning")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).with_structured_output(PlannerResponse, method="json_schema")
    
    # Create a combined message list with system prompt
    response = llm.invoke([system_prompt])
    logger.info(f"LLM responded with next step: {response.next_step}")
    
    return { "planned_step": response.next_step, "messages": [AIMessage(content="Next step: " + response.next_step)] }

def route_to_step(state: AgentCreatorState) -> AgentCreatorState:
    logger.info(f"Routing to step: {state.planned_step}")
    return state.planned_step
    
def update_blueprint(state: AgentCreatorState) -> AgentCreatorState:
    """Update the agent blueprint based on user feedback."""
    logger.info("Executing update_blueprint")
    
    system_prompt = [SystemMessage(content=f"""
You're an AI agent blueprint designer. Your task is to create or update a blueprint for an AI agent based on user requirements.

A good agent blueprint should:
- Be specific about the agent's purpose, capabilities, and limitations
- Define clear boundaries for what the agent can and cannot do
- Outline the agent's personality, tone, and communication style
- Specify required knowledge domains and key skills
- Accomplish one particular step in the overall workflow

AVAILABLE NODE TYPES:
1. "llm" - Language model interaction nodes for processing information, generating content, or making decisions
2. "web_search" - Internet search nodes for retrieving real-time information from the web

AGENT DESIGN PRINCIPLES:
- Break complex tasks into 3-7 focused nodes for optimal performance
- Each node should be atomic with a clear input and output
- Design for reliability with clear step purposes
- Consider parallel paths for concurrent operations when appropriate

Current blueprint: {state.agent_blueprint if state.agent_blueprint else "No blueprint yet"}
Messages: {state.messages}
""")]
    
    
    
    logger.info("Querying LLM for blueprint update")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    response = llm.invoke(system_prompt)
    logger.info("LLM responded with updated blueprint")
    
    return { "agent_blueprint": response.content, "messages": [AIMessage(content="Updated blueprint: " + response.content)] }

def ask_followup(state: AgentCreatorState) -> AgentCreatorState:
    """Ask a followup question to gather more information from the user."""
    logger.info("Executing ask_followup")
    
    system_prompt = [SystemMessage(content=f"""
You're an expert agent creator assistant. You need to ask the user follow-up questions to gather more information to build a high-quality agent.

Current blueprint: {state.agent_blueprint if state.agent_blueprint else "No blueprint yet"}

AVAILABLE NODE TYPES:
1. "llm" - Language model interaction nodes for processing information, generating content, or making decisions
2. "web_search" - Internet search nodes for retrieving real-time information from the web

AGENT DESIGN CONSTRAINTS:
- Agents must have 3-7 focused nodes for optimal performance
- Each node must be atomic with a clear input and output
- Every path must start from a "START" node and end at an "END" node
- Parallel paths are allowed but no recursive paths or loops
- Every node must have at least one incoming and one outgoing edge (except START/END)

Your task is to ask insightful, specific questions that will help you understand:
- The precise purpose of the agent
- Required capabilities and features
- Knowledge domains the agent should have expertise in
- How the agent should communicate and interact
- Any constraints or limitations
- The goal is to break down complex reasoning into a series of smaller, manageable steps that together
solve the overall problem

Ask only the most important questions needed right now. Be concise but friendly.
""")]
    

    
    logger.info("Querying LLM for followup question")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    response = llm.invoke(system_prompt + state.messages)
    logger.info("LLM responded with followup question")
    
    return { "messages": [AIMessage(content="Followup question: " + response.content)] }

def generate_agent(state: AgentCreatorState) -> AgentCreatorState:
    """Generate an agent configuration based on the blueprint."""
    logger.info(f"Executing generate_agent with blueprint: {state.agent_blueprint}")
    
    system_prompt = f"""
        You're an expert agent creator. Your task is to generate a JSON configuration for an agent based on the blueprint.
        
        UNDERSTANDING AGENTS:
        An agent is a sequence of atomic actions (nodes) that AI will execute in a specific order. Each node in the 
        sequence must:
        - Be focused on a single, specific task (atomic)
        - Have a clear input and output
        - Accomplish one particular step in the overall workflow
        
        The goal is to break down complex reasoning into a series of smaller, manageable steps that together 
        form a coherent workflow. This maximizes reliability and makes it easier to debug the agent's behavior.
        
        AVAILABLE NODE TYPES:
        1. "llm" - Language model interaction nodes:
           - Purpose: Process information, generate content, or make decisions
           - Configuration: Requires model_name, temperature, and a clear objective
           - Best for: Analysis, summarization, content generation, decision-making
        
        2. "web_search" - Internet search nodes:
           - Purpose: Retrieve real-time information from the web
           - Configuration: Requires model_name, temperature, and search objective
           - Best for: Gathering current data, researching topics, finding specific information
        
        NODE CONFIGURATION REQUIREMENTS:
        - id: A unique, descriptive identifier (e.g., "search_news", "summarize_findings")
        - type: Either "llm" or "web_search"
        - objective: Clear instructions for what the node should accomplish
        - model_name: Recommend using "gpt-4o-mini" for optimal performance
        - temperature: 0.0-0.3 for factual/precise tasks, 0.4-0.7 for creative tasks
        
        EDGE CONFIGURATION:
        Edges define the flow between nodes, with these guidelines:
        1. Every path must start from a "START" node and end at an "END" node
        2. PARALLEL PATHS are allowed and encouraged when appropriate:
           - One node can have multiple outgoing edges (e.g., node_A -> node_B, node_A -> node_C)
           - Multiple nodes can connect to a single node (e.g., node_B -> node_D, node_C -> node_D)
           - This creates parallel execution paths that can merge later
        3. NO RECURSIVE PATHS or loops are allowed - edges must only move forward in the workflow
        4. Every node must have at least one incoming and one outgoing edge (except if connected to START or END)
        
        Example of valid parallel path configuration:
        ```json
        [
          "source": "START", "target": "initial_node"
          "source": "initial_node", "target": "path1_node"
          "source": "initial_node", "target": "path2_node"
          "source": "path1_node", "target": "merge_node"
          "source": "path2_node", "target": "merge_node"
          "source": "merge_node", "target": "END"
        ]
        ```
        
        AGENT DESIGN PRINCIPLES:
        - Break complex tasks into 3-7 focused nodes for optimal performance
        - Use web_search nodes to gather information before processing with llm nodes
        - Make each node's objective specific and actionable
        - Ensure the complete workflow addresses all requirements in the blueprint
        - Design for reliability by making each step's purpose and output clear
        - Use parallel paths when different operations can happen concurrently, then merge results
        
        EXAMPLE STRUCTURE:
        For a research agent:
        1. web_search node to gather initial information
        2. The workflow splits into two parallel paths:
           - One path analyzes technical aspects
           - Another path analyzes market implications
        3. The paths merge at a synthesis node that combines both analyses
        4. Final llm node prepares the complete report
        
        Based on the blueprint below, create a complete agent configuration with appropriate nodes and edges:
        
        {state.agent_blueprint}
        {state.messages}
    """
    
    # LLM with structured output using the AgentConfig schema
    logger.info("Querying LLM for agent generation")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).with_structured_output(AgentConfig, method="json_schema")
    
    config = llm.invoke([system_prompt])
    logger.info(f"LLM responded with agent configuration: {config.agent_name}")
    
    return { "agent_config": config , "messages": [AIMessage(content="Generated agent configuration: " + config.agent_name)]}