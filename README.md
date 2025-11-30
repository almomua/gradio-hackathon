---
title: 'research-nexus'
emoji: '📈'
colorFrom: 'red'
colorTo: 'green'
sdk: 'gradio'
sdk_version: "6.0.0"
app_file: app.py
pinned: false
license: mit
tags:
  - mcp-in-action-track-consumer

---

# 🔬 Research Nexus - AI Research Paper Assistant

## 📖 Project Overview

**Research Nexus** is an intelligent research assistant powered by Google Gemini and Model Context Protocol (MCP) that helps researchers, students, and academics discover, analyze, and visualize scientific papers. The agent can search for papers, provide structured summaries, and generate visual explanations like scientific posters to make complex research more accessible.

### ✨ Key Features

- 🔍 **Smart Paper Search**: Find relevant research papers on any topic using MCP-powered search tools
- 📝 **Intelligent Summarization**: Get structured, comprehensive summaries with key insights, methodology, and results
- 🎨 **Visual Generation**: Create scientific posters and diagrams to explain complex concepts
- 💬 **Conversational Memory**: Maintains context throughout your research session
- 🖼️ **Rich Media Display**: Automatically renders images with beautiful styling and modal lightbox viewing
- 🎯 **Custom UI**: Modern black and orange themed interface with smooth animations

### 🛠️ Technology Stack

- **Frontend**: Gradio 6.0 with custom CSS/HTML
- **LLM**: Google Gemini 2.5 Flash
- **Agent Framework**: LangChain + LangGraph
- **MCP Integration**: langchain-mcp-adapters for external tool connectivity

---

## 🎥 Demo Video

**Watch Research Nexus in action (1-5 minutes):**

[![Demo Video](https://img.shields.io/badge/Watch-Demo%20Video-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE)


---

## 📱 Social Media

**Check out my post about this project:**

- 💼 **LinkedIn**: [View Post](https://www.linkedin.com/posts/YOUR_PROFILE_YOUR_POST_ID)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google API Key (for Gemini)
- MCP Server Access (optional, for paper search/generation)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/research-nexus.git
cd research-nexus
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```env
GOOGLE_API_KEY=your_google_api_key_here
```

4. Run the application:
```bash
python app.py
```

5. Open your browser at `http://localhost:7860`

---

## 📁 Project Structure

```
research-nexus/
├── app.py           # Gradio UI and main interface
├── agent.py         # LangChain/LangGraph agent logic
├── tools.py         # MCP server config and system prompt
├── requirements.txt # Python dependencies
└── .env            # Environment variables (not tracked)
```

---

## 🎯 How to Use

1. **Start a conversation**: Ask about any research topic
2. **Provide paper details**: Share a paper link or let the agent search
3. **Request visualizations**: Ask for scientific posters or diagrams
4. **Explore insights**: Get structured summaries with key findings
5. **Continue chatting**: The agent remembers your conversation context

### Example Queries

```
"Find recent papers on quantum computing"
"Summarize this paper: https://arxiv.org/abs/..."
"Generate a scientific poster for YOLO paper"
"What are the latest advances in transformer models?"
```

---

## 🏆 MCP in Action Track

This project is part of the **MCP in Action Track** showcasing practical applications of the Model Context Protocol for connecting AI agents to external tools and data sources.

### MCP Integration Highlights

- ✅ Uses `langchain-mcp-adapters` for seamless tool integration
- ✅ Connects to research paper APIs and generation services
- ✅ Demonstrates real-world MCP consumer application
- ✅ Handles async operations with proper event loop management

---

## 📄 License

MIT License - feel free to use and modify for your own projects!

---

## 🙏 Acknowledgments

- Built for the MCP in Action hackathon
- Powered by Google Gemini and LangChain
- MCP integration via langchain-mcp-adapters

---

**Made with ❤️ for the research community**
