"""
LangChain/LangGraph Agent with MCP Integration
"""

import asyncio
import nest_asyncio
import warnings
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from tools import (
    MCP_SERVERS, 
    SYSTEM_PROMPT, 
    MODEL_NAME, 
    MODEL_TEMPERATURE,
    get_api_key
)

# Allow nested event loops (fixes gRPC async issues)
nest_asyncio.apply()

# Suppress MCP schema warnings and other verbose logs
warnings.filterwarnings("ignore", message=".*Key.*is not supported in schema.*")
logging.getLogger("langchain_mcp_adapters").setLevel(logging.ERROR)
logging.getLogger("mcp").setLevel(logging.ERROR)

# Global variables
agent = None
mcp_client = None
loop = None
memory = MemorySaver()  # Conversation memory


def get_or_create_event_loop():
    """Get existing event loop or create a new one."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop


async def build_agent_async():
    """Create the LangGraph agent with MCP tools and memory."""
    global mcp_client
    
    api_key = get_api_key()
    
    # Initialize Gemini model
    model = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=api_key,
        temperature=MODEL_TEMPERATURE,
    )
    
    tools = []
    
    # Load MCP tools if servers are configured
    if MCP_SERVERS:
        # Suppress stderr during MCP client initialization to hide schema warnings
        import sys
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        try:
            mcp_client = MultiServerMCPClient(MCP_SERVERS)
            mcp_tools = await mcp_client.get_tools()
            tools.extend(mcp_tools)
        finally:
            # Restore stderr
            sys.stderr = old_stderr
        
        print(f"✅ Loaded {len(mcp_tools)} tools from MCP servers")
        for tool in mcp_tools:
            desc = tool.description[:50] if tool.description else "No description"
            print(f"   - {tool.name}: {desc}...")
    else:
        print("⚠️ No MCP servers configured. Add servers to MCP_SERVERS in tools.py")
    
    # Create ReAct agent with LangGraph and memory checkpointer
    agent = create_agent(
        model, 
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=memory
    )
    
    return agent


def initialize_agent():
    """Initialize the agent."""
    global agent, loop
    try:
        loop = get_or_create_event_loop()
        agent = loop.run_until_complete(build_agent_async())
        return True, "Agent initialized successfully!"
    except Exception as e:
        return False, f"Failed to initialize agent: {str(e)}"


def convert_history_to_messages(history):
    """Convert Gradio chat history to LangChain message format."""
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            messages.append(("user", content))
        elif role == "assistant":
            messages.append(("assistant", content))
    return messages


async def get_response_async(message: str, history: list, thread_id: str) -> str:
    """Get response from agent asynchronously with memory and print thinking process."""
    global agent
    
    if agent is None:
        return "Error: Agent not initialized"
    
    try:
        # Convert history to messages format
        messages = convert_history_to_messages(history)
        # Add current message
        messages.append(("user", message))
        
        # Config with thread_id for memory persistence
        config = {"configurable": {"thread_id": thread_id}}
        
        print("\n" + "="*80)
        print("🤔 AGENT THINKING PROCESS")
        print("="*80)
        
        # Suppress stderr during agent execution to hide schema warnings
        import sys
        import io
        old_stderr = sys.stderr
        sys.stderr = io.StringIO()
        
        # Stream agent execution to see intermediate steps
        final_response = None
        step_count = 0
        
        try:
            async for event in agent.astream({"messages": messages}, config=config):
                for node_name, node_data in event.items():
                    step_count += 1
                    
                    # Print node being executed
                    if node_name == "agent":
                        print(f"\n💭 Step {step_count}: Agent Reasoning")
                        print("-" * 80)
                        
                        # Check if agent is calling a tool
                        if "messages" in node_data:
                            last_message = node_data["messages"][-1]
                            
                            # Tool call
                            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                                for tool_call in last_message.tool_calls:
                                    print(f"🔧 Tool Call: {tool_call['name']}")
                                    print(f"   Args: {tool_call.get('args', {})}")
                            
                            # Agent message
                            elif hasattr(last_message, "content") and last_message.content:
                                content = last_message.content
                                if content and len(content) < 500:
                                    print(f"💬 Thought: {content[:200]}...")
                    
                    elif node_name == "tools":
                        print(f"\n🛠️  Step {step_count}: Tool Execution")
                        print("-" * 80)
                        
                        if "messages" in node_data:
                            for msg in node_data["messages"]:
                                if hasattr(msg, "name"):
                                    print(f"📊 Tool: {msg.name}")
                                    result = str(msg.content)
                                    # Truncate long results
                                    if len(result) > 300:
                                        print(f"   Result: {result[:300]}... (truncated)")
                                    else:
                                        print(f"   Result: {result}")
                    
                    # Store final response
                    if "messages" in node_data:
                        final_response = node_data["messages"][-1].content
        
        finally:
            # Restore stderr
            sys.stderr = old_stderr
        
        print("\n" + "="*80)
        print("✅ THINKING COMPLETE")
        print("="*80 + "\n")
        
        return final_response if final_response else "No response generated"
        
    except Exception as e:
        # Restore stderr in case of error
        sys.stderr = old_stderr
        print(f"\n❌ Error during agent execution: {str(e)}\n")
        return f"Error: {str(e)}"


def get_response(message: str, history: list, thread_id: str) -> str:
    """Get response from agent using the shared event loop."""
    global loop
    if loop is None:
        loop = get_or_create_event_loop()
    return loop.run_until_complete(get_response_async(message, history, thread_id))

