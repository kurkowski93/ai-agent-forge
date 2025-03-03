from langgraph.graph import StateGraph, END, START
from agents_forge.core_agent.utils.state import AgentCreatorState
from agents_forge.core_agent.utils.nodes import step_planner, update_blueprint, ask_followup, generate_agent, NextStep, route_to_step
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

async def generate_core_agent():
    
    builder = StateGraph(AgentCreatorState)
    
    builder.add_node("step_planner", step_planner)
    builder.add_node(NextStep.UPDATE_BLUEPRINT, update_blueprint)
    builder.add_node(NextStep.ASK_FOLLOWUP, ask_followup)
    builder.add_node(NextStep.GENERATE_AGENT, generate_agent)
    
    
    builder.add_edge(
        START,
        "step_planner"
    )
    
    builder.add_conditional_edges( 
        "step_planner",
        route_to_step,
        {
            NextStep.UPDATE_BLUEPRINT,
            NextStep.ASK_FOLLOWUP,
            NextStep.GENERATE_AGENT
        }
    )
    
    
    builder.add_edge(NextStep.UPDATE_BLUEPRINT, "step_planner")
    builder.add_edge(NextStep.ASK_FOLLOWUP, END)
    builder.add_edge(NextStep.GENERATE_AGENT, END)
    
    return builder.compile(checkpointer=memory)


    