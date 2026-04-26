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
- LangChain + GPT-4o-mini (overridable via `HEALTH_AGENT_MODEL`)
- FAISS vector store (RAG, in-memory; rebuilt on first run)
- SQLite (memory & logs, **per-session** on the deployed app)
- Streamlit

## Run Locally
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI API key to .env
streamlit run app.py
```

### Configuration
- `OPENAI_API_KEY` — required.
- `HEALTH_AGENT_MODEL` — default `gpt-4o-mini`. Set to `gpt-4o` for the
  larger model (≈10× the per-token cost).
- `HEALTH_AGENT_DB_PATH` — override the SQLite location for the local CLI
  scripts. Streamlit ignores this and uses a per-session temp file.

## Course
AI Agent Course — Final Project
