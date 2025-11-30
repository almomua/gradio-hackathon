# 🤖 MCP Agent Chat

An AI agent chat application with **MCP (Model Context Protocol)** server integration, built with Gradio, LangChain, LangGraph, and Google Gemini.

## ✨ Features

- 🔌 **MCP Server Integration** - Connect to any MCP-compatible server
- 🧠 **Conversational Memory** - Agent remembers the conversation
- 🤖 **LangGraph ReAct Agent** - Intelligent tool-using agent
- 💬 **Gradio Chat UI** - Simple web interface
- ⚡ **Google Gemini** - Powered by Gemini 2.5 Flash

## 📁 Project Structure

```
mcp agent/
├── app.py          # Gradio UI (main entry point)
├── agent.py        # LangChain/LangGraph agent logic
├── tools.py        # MCP server configuration
├── requirements.txt
├── .env            # Your API keys
└── README.md
```

| File | Description |
|------|-------------|
| `tools.py` | MCP server configs, system prompt, model settings |
| `agent.py` | Agent initialization, memory, response handling |
| `app.py` | Gradio chat interface (run this) |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key
```

### 3. Configure MCP Servers

Edit `tools.py` to add/modify MCP servers:

```python
MCP_SERVERS = {
    "my-server": {
        "url": "https://your-mcp-server.com/mcp",
        "transport": "streamable_http",
        "headers": {
            "Authorization": "Bearer YOUR_API_KEY"
        }
    },
}
```

### 4. Run the App

```bash
python app.py
```

Visit `http://localhost:7860`

## 🔧 Configuration

### Adding MCP Servers (tools.py)

**HTTP Server:**
```python
MCP_SERVERS = {
    "my-api": {
        "url": "http://localhost:8000/mcp",
        "transport": "streamable_http",
    },
}
```

**Local stdio Server:**
```python
MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/path"],
        "transport": "stdio",
    },
}
```

### Customizing the Agent (tools.py)

```python
# Change the model
MODEL_NAME = "gemini-2.5-flash"
MODEL_TEMPERATURE = 0.7

# Customize system prompt
SYSTEM_PROMPT = """Your custom prompt here..."""
```

## 📜 License

MIT License
