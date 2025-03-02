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
        {state.agent_bleuprint}
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
        Current blueprint: 
        {state.agent_bleuprint}
        
        Messages:
        {state.messages}
        
        Please update the blueprint with new informations.
    """

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    response = await llm.ainvoke(system_prompt)
    
    return{ "agent_config": response.content}

async def ask_followup(state: AgentCreatorState) -> AgentCreatorState:
    """
    Ask followup question to user to clarify some details.
    """
    system_prompt = f"""
        You're expert agent creator. Your current task it to ask followup question to user to clarify some details about the agent you're going to create.
        
        Here is the current blueprint:
        {state.agent_bleuprint}
        
        Here is the messages history:
        {state.messages}
        
        Please ask followup question to user to clarify some details.
    """
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    response = await llm.ainvoke(system_prompt)
    
    return { "messages": [AIMessage(content=response.content)]}

async def generate_agent(state: AgentCreatorState) -> AgentCreatorState:
    return { "agent_config": state.agent_config}