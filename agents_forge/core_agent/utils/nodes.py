from agents_forge.core_agent.utils.state import AgentCreatorState
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Literal
from langchain_core.messages import AIMessage
from enum import Enum
from agents_forge.core_agent.utils.helper_models import NextStep

async def step_planner(state: AgentCreatorState) -> AgentCreatorState:
    """
    Gather information from the user about the agent they want to create.
    """

    system_prompt = f"""
        You're expert agent creator. Based on current state of agent blueprint decide what is best next step to do: 
        - update the blueprint with new informations
        - ask followup question to user to clarify some details
        - generate agent based on current blueprint (available only if blueprint is not empty)
        
        Messages:
        {state.messages}
        
        Agent blueprint:
        {state.agent_blueprint}
    """
    
    class PlannerResponse(BaseModel):
        next_step: NextStep = Field(description="Next step to do")
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).with_structured_output(PlannerResponse)
       
    response = await llm.ainvoke(system_prompt)
    
    return { "planned_step": response.next_step}

def route_to_step(state: AgentCreatorState) -> AgentCreatorState:
    return state.planned_step
    
async def update_blueprint(state: AgentCreatorState) -> AgentCreatorState:
    """
    Update the blueprint with new informations.
    """
    system_prompt = f"""
        You're expert agent creator. Your current task it to update the agent blueprint based on the knowledge from messages. 
        
        UNDERSTANDING AGENTS:
        An agent is a sequence of atomic actions (nodes) that AI will execute in a specific order. Each node should:
        - Be focused on a single, specific task (atomic)
        - Have a clear input and output
        - Accomplish one particular step in the overall workflow
        
        The goal is to break down complex reasoning into simple, sequential steps. This makes the agent more 
        reliable, easier to debug, and more transparent in its decision-making.
        
        IMPORTANT CONSTRAINTS:
        - The agent can only use two types of nodes: "llm" (for language model interactions) and "web_search" (for internet searches)
        - Each node must have an atomic, specific task (no complex multi-step processes in a single node)
        - The agent must work sequentially without loops
        - If a node needs to be used more than once, it must be added multiple times in the sequence
        
        DESIGN APPROACH:
        - You should proactively design the agent's workflow without requiring excessive user guidance
        - Make intelligent assumptions about the agent's implementation based on the task description
        - Apply best practices in agent design based on your expertise
        - Be decisive and comprehensive in your design decisions
        
        Current blueprint: 
        {state.agent_blueprint}
        
        Messages:
        {state.messages}
        
        Create a CONCISE blueprint with:
        1. Agent name and short description of its purpose
        2. Brief sequence of operations (node by node) in a simple list
        3. For each node: id, type, brief objective

        Keep it brief and focused on the flow, avoid unnecessary details.
    """

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    response = await llm.ainvoke(system_prompt)
    
    return { "agent_blueprint": response.content}

async def ask_followup(state: AgentCreatorState) -> AgentCreatorState:
    """
    Ask followup question to user to clarify some details.
    """
    system_prompt = f"""
        You're expert agent creator. Your current task it to ask followup question to user to clarify some details about the agent you're going to create.
        
        UNDERSTANDING AGENTS:
        An agent is essentially a sequence of atomic actions that AI will execute in a specific order. Each action (node) 
        in this sequence should:
        - Be focused on a single, specific task (atomic)
        - Have a clear input and output
        - Accomplish one particular step in the overall workflow
        
        The goal is to break down complex reasoning into a series of smaller, manageable steps that together 
        form a coherent workflow. This makes the agent more reliable, easier to debug, and more transparent 
        in its decision-making process.
        
        IMPORTANT GUIDANCE:
        - Only ask questions when absolutely necessary for critical information
        - Make reasonable assumptions and design decisions on your own wherever possible
        - Focus on asking only 1-2 most critical questions rather than seeking validation for every detail
        - The goal is to design the agent proactively with minimal user input
        - If you already have enough information to proceed, consider recommending moving directly to agent creation
        
        Here is the current blueprint:
        {state.agent_blueprint}
        
        Here is the messages history:
        {state.messages}
        
        If you genuinely need crucial information, ask a focused followup question. Otherwise, indicate that you have 
        sufficient information to proceed with the agent creation based on your expert judgment.
    """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    response = await llm.ainvoke(system_prompt)
    
    return { "messages": [AIMessage(content=response.content)]}

async def generate_agent(state: AgentCreatorState) -> AgentCreatorState:
    """
    Generate agent configuration from the blueprint.
    Produces a valid JSON configuration that can be used to instantiate an agent.
    """
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
        Edges must create a linear path from START to END:
        ```json
        [
          ..."source": "START", "target": "first_node"...
          ..."source": "first_node", "target": "second_node"..,
          ...
          "source": "last_node", "target": "END"
        ]
        ```
        
        AGENT DESIGN PRINCIPLES:
        - Break complex tasks into 3-7 focused nodes for optimal performance
        - Use web_search nodes to gather information before processing with llm nodes
        - Make each node's objective specific and actionable
        - Ensure the complete workflow addresses all requirements in the blueprint
        - Design for reliability by making each step's purpose and output clear
        
        EXAMPLE STRUCTURE:
        For a research agent:
        1. web_search node to gather initial information
        2. llm node to analyze and identify key points
        3. web_search node to find supporting evidence
        4. llm node to synthesize findings into a final output
        
        Based on the blueprint below, create a complete agent configuration with appropriate nodes and edges:
        
        {state.agent_blueprint}
    """
    
    from agents_forge.agents_generation.config_schema import AgentConfig, NodeConfig, EdgeConfig
    from pydantic import Field
    
    # LLM with structured output using the AgentConfig schema
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1).with_structured_output(AgentConfig)
    # Get structured response directly
    config = await llm.ainvoke(system_prompt)
    return {"agent_config": config}