"""
LangChain/LangGraph Agent with MCP Integration
"""

import asyncio
import nest_asyncio
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
        mcp_client = MultiServerMCPClient(MCP_SERVERS)
        mcp_tools = await mcp_client.get_tools()
        tools.extend(mcp_tools)
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


def print_thinking_header():
    """Print a header for thinking process."""
    print("\n" + "="*60)
    print("🧠 AGENT THINKING PROCESS")
    print("="*60)


def print_thinking_step(step_type: str, content: str):
    """Print a thinking step to terminal."""
    icons = {
        "tool_call": "🔧",
        "tool_result": "📊",
        "thought": "💭",
        "action": "⚡",
        "final": "✅"
    }
    icon = icons.get(step_type, "•")
    print(f"\n{icon} {step_type.upper()}: {content}")


async def get_response_async(message: str, history: list, thread_id: str) -> str:
    """Get response from agent asynchronously with memory and print thinking."""
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
        
        print_thinking_header()
        print(f"📝 USER QUERY: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        # Stream agent execution to show thinking process
        final_response = None
        step_count = 0
        
        async for event in agent.astream({"messages": messages}, config=config):
            step_count += 1
            
            # Handle different event types
            if "agent" in event:
                agent_data = event["agent"]
                if "messages" in agent_data:
                    for msg in agent_data["messages"]:
                        # Check if it's a tool call
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                tool_name = tool_call.get("name", "unknown")
                                tool_args = str(tool_call.get("args", {}))[:100]
                                print_thinking_step("tool_call", f"{tool_name}({tool_args}...)")
                        
                        # Regular message content
                        elif hasattr(msg, "content") and msg.content:
                            content_preview = str(msg.content)[:200]
                            print_thinking_step("thought", content_preview)
            
            elif "tools" in event:
                tool_data = event["tools"]
                if "messages" in tool_data:
                    for msg in tool_data["messages"]:
                        if hasattr(msg, "content"):
                            result_preview = str(msg.content)[:150]
                            print_thinking_step("tool_result", result_preview)
            
            # Store the final response
            if "messages" in event.get("agent", {}):
                final_response = event["agent"]["messages"]
        
        # Extract final answer
        if final_response:
            final_content = final_response[-1].content
            print_thinking_step("final", f"Response ready ({len(final_content)} chars)")
            print("="*60 + "\n")
            return final_content
        
        # Fallback: use regular invoke if streaming didn't work
        response = await agent.ainvoke({"messages": messages}, config=config)
        final_content = response["messages"][-1].content
        print_thinking_step("final", "Response generated (fallback mode)")
        print("="*60 + "\n")
        return final_content
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        print("="*60 + "\n")
        return f"Error: {str(e)}"


def get_response(message: str, history: list, thread_id: str) -> str:
    """Get response from agent using the shared event loop."""
    global loop
    if loop is None:
        loop = get_or_create_event_loop()
    return loop.run_until_complete(get_response_async(message, history, thread_id))

