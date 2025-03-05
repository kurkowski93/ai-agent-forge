from enum import Enum
from typing import Dict, Any, Callable, List, Optional
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from agents_forge.agents_generation.state import AgentsGenerationState
from agents_forge.agents_generation.config_schema import NodeConfig
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
import json
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Limit messages to last N
MAX_MESSAGES = 4

class NodeType(str, Enum):
    """Predefined node types for the AgentForge system."""
    LLM = "llm"                     # Basic LLM call with messages
    WEB_SEARCH = "web_search"       # Search the web for information

def create_llm_node(config: NodeConfig) -> Callable:
    """
    Create a basic LLM node that processes messages using a language model.
    
    Args:
        config: Configuration for the node, including model_name, temperature and objective
        
    Returns:
        A callable function that represents the node in the agent graph
    """
    model_name = config.model_name if hasattr(config, 'model_name') else "gpt-4o-mini"
    temperature = config.temperature if hasattr(config, 'temperature') else 0.3
    system_prompt = config.objective
    
    def llm_node(state: AgentsGenerationState) -> AgentsGenerationState:
        llm = ChatOpenAI(model=model_name, temperature=temperature)
        
        logger.info(f"[{config.id}] querying LLM with {len(state['messages'])} messages")
        if state['messages']:
            logger.info(f"[{config.id}] last message: {state['messages'][-1].content[:100]}...")
        
        # Limit messages to last MAX_MESSAGES
        limited_messages = state['messages'][-MAX_MESSAGES:] if len(state['messages']) > MAX_MESSAGES else state['messages']
        
        # Add system prompt if provided
        messages_with_system = [SystemMessage(content=system_prompt)] + limited_messages if system_prompt else limited_messages
        
        # Call LLM
        logger.info(f"[{config.id}] sending request to model {model_name}")
        response = llm.invoke(messages_with_system)
        logger.info(f"[{config.id}] received response from LLM")
        
        # Return updated state
        return {"messages": [AIMessage(content=response.content)]}
    
    return llm_node

def create_web_search_node(config: NodeConfig) -> Callable:
    """
    Create a web search node that retrieves information from the internet.
    
    Args:
        config: Configuration for the node, including model_name and temperature
        
    Returns:
        A callable function that represents the node in the agent graph
    """
    class SearchQuery(BaseModel):
        search_query: str = Field(None, description="Search query for retrieval.")
        
    structured_llm = ChatOpenAI(model=config.model_name, temperature=config.temperature).with_structured_output(SearchQuery)
    
    
    def web_search_node(state: AgentsGenerationState) -> AgentsGenerationState:
        search_instructions = SystemMessage(content=f"""
            You will be given a conversation between an analyst and an expert. 
            Your goal is to generate a well-structured query for use in retrieval and / or web-search related to the conversation.     
            First, analyze the full conversation.
            Convert this final question into a well-structured web search query""")

        search_query = structured_llm.invoke([search_instructions]+state['messages'])
        
        logger.info(f"[{config.id}] performing web search with query: {search_query}")
         # Search
        tavily_search = TavilySearchResults(max_results=3)
        
        search_results = tavily_search.invoke(search_query.search_query)
        
        formatted_search_results = "\n\n---\n\n".join(
            [
                f'<Document href="{doc["url"]}"/>\n{doc["content"]}\n</Document>'
                for doc in search_results
            ]
        )
        
        # Create response message
        response_message = AIMessage(content=f"Found the following information: {formatted_search_results}")
        
        # Return updated state with search results
        return {"messages": [response_message]}
    
    return web_search_node

# Factory function to create nodes based on type
def create_node(node_type: str, config: Dict[str, Any]) -> Callable:
    """
    Factory function to create nodes based on their type.
    
    Args:
        node_type: Type of node to create (should match a NodeType enum value)
        config: Configuration for the node
        
    Returns:
        A callable function that represents the node in the agent graph
        
    Raises:
        ValueError: If the node type is not recognized
    """
    
    logger.info(f"Creating node: {config.id} of type {config.type}")
    
    if node_type == NodeType.LLM:
        return create_llm_node(config)
    elif node_type == NodeType.WEB_SEARCH:
        return create_web_search_node(config)
    else:
        logger.error(f"Unknown node type: {node_type}")
        raise ValueError(f"Unknown node type: {node_type}. Supported types: {[t.value for t in NodeType]}") 