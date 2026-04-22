"""HealthAgent: LangChain agent wiring over GPT-4o."""
from __future__ import annotations

import os
from typing import Any, Callable

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
except ImportError:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from .prompts import PROACTIVE_TRIGGER, SYSTEM_PROMPT
from .tools import ALL_TOOLS


def _build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )


class HealthAgent:
    """Thin wrapper around a LangChain OpenAI-tools agent."""

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.3, verbose: bool = True):
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        self.llm = ChatOpenAI(model=model, temperature=temperature)
        self.prompt = _build_prompt()
        self.tools = ALL_TOOLS
        self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=verbose,
            return_intermediate_steps=True,
            max_iterations=8,
            handle_parsing_errors=True,
        )
        self._chat_history: list = []

    # --------- Public API ---------
    def chat(self, user_message: str, on_step: Callable[[str, Any], None] | None = None) -> dict:
        """Send a user message and return {'output': str, 'tool_calls': list[dict]}.

        `on_step` is an optional callback invoked as (tool_name, tool_input) when
        a tool is about to run, handy for live demo status updates.
        """
        result = self.executor.invoke(
            {"input": user_message, "chat_history": self._chat_history}
        )
        output = result.get("output", "")
        intermediate = result.get("intermediate_steps", []) or []

        tool_calls: list[dict] = []
        for action, observation in intermediate:
            name = getattr(action, "tool", "unknown_tool")
            tool_input = getattr(action, "tool_input", "")
            if on_step is not None:
                try:
                    on_step(name, tool_input)
                except Exception:
                    pass
            tool_calls.append(
                {"tool": name, "input": tool_input, "output": str(observation)[:500]}
            )

        # Update chat history using LangChain message objects.
        from langchain_core.messages import AIMessage, HumanMessage

        self._chat_history.append(HumanMessage(content=user_message))
        self._chat_history.append(AIMessage(content=output))

        return {"output": output, "tool_calls": tool_calls}

    def proactive_check(self, on_step: Callable[[str, Any], None] | None = None) -> dict:
        """Run the auto morning check-in. Intended for app load."""
        return self.chat(PROACTIVE_TRIGGER, on_step=on_step)

    def reset_history(self) -> None:
        self._chat_history = []
