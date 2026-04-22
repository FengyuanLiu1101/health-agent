# HealthAgent 🫀

AI-powered personal health monitoring agent that continuously monitors wearable data, performs multi-step reasoning, and delivers personalized daily recommendations.

## Live Demo
👉 [health-agent-fengyuan.streamlit.app](https://health-agent-fengyuan.streamlit.app)

## Features
- Proactive anomaly alerts — no user prompt needed
- ReAct reasoning loop with 5 callable tools
- RAG knowledge base (FAISS + WHO guidelines)
- 3-tier memory: short-term, long-term, episodic
- Feedback-driven preference adaptation

## Tech Stack
- LangChain + GPT-4o-mini
- FAISS vector store (RAG)
- SQLite (memory & logs)
- Streamlit

## Run Locally
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI API key to .env
streamlit run app.py
```

## Course
AI Agent Course — Final Project
