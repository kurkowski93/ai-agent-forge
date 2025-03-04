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
You're expert agent creator. Based on current state of agent blueprint decide what is best next step to do:
1) UPDATE_BLUEPRINT - when you need to update the blueprint based on user feedback
2) ASK_FOLLOWUP - when you need more information from user to create a good agent
3) GENERATE_AGENT - when you have enough information to generate a custom agent

Blueprint: {state.agent_blueprint if state.agent_blueprint else "No blueprint yet"}

Current user message: {state.messages}

Respond with the next step.
""")
    
    class PlannerResponse(BaseModel):
        next_step: NextStep = Field(description="Next step to do")
        
    logger.info("Querying LLM for step planning")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).with_structured_output(PlannerResponse)
    
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

Current blueprint: {state.agent_blueprint if state.agent_blueprint else "No blueprint yet"}
""")]
    
    # Limit messages to last MAX_MESSAGES
    limited_messages = state.messages
    
    logger.info("Querying LLM for blueprint update")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    response = llm.invoke(system_prompt + limited_messages)
    logger.info("LLM responded with updated blueprint")
    
    return { "agent_blueprint": response.content, "messages": [AIMessage(content="Updated blueprint: " + response.content)] }

def ask_followup(state: AgentCreatorState) -> AgentCreatorState:
    """Ask a followup question to gather more information from the user."""
    logger.info("Executing ask_followup")
    
    system_prompt = [SystemMessage(content=f"""
You're an expert agent creator assistant. You need to ask the user follow-up questions to gather more information to build a high-quality agent.

Current blueprint: {state.agent_blueprint if state.agent_blueprint else "No blueprint yet"}

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
    
    system_prompt = SystemMessage(content=f"""
You are an expert agent designer. Your task is to create a complete agent configuration based on the blueprint provided.

A good agent configuration should:
- Define a clear purpose and goal for the agent
- Specify the agent's capabilities through a collection of nodes
- Design for reliability by making each step's purpose and output clear
- Include appropriate safeguards and error handling

The agent configuration must follow this structure:
- agent_name: A descriptive name for the agent
- description: A detailed description of what the agent does
- nodes: A list of processing nodes that make up the agent's workflow
   - Each node must have an id, type, objective, model_name, and temperature
   - Use nodes to break complex tasks into manageable steps
- edges: A list of edges connecting the nodes, each with source and target node IDs

Blueprint:
{state.agent_blueprint}

Return a complete, valid agent configuration in JSON format.
""")
    
    # LLM with structured output using the AgentConfig schema
    logger.info("Querying LLM for agent generation")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).with_structured_output(AgentConfig)
    
    config = llm.invoke([system_prompt])
    logger.info(f"LLM responded with agent configuration: {config.agent_name}")
    
    return { "agent_config": config , "messages": [AIMessage(content="Generated agent configuration: " + config.agent_name)]}