"""HealthAgent: LangChain agent wiring over a configurable OpenAI model."""
from __future__ import annotations

import os
from typing import Any, Callable

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import AIMessage, HumanMessage
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


def _usage_from_callback(cb: Any) -> dict[str, Any]:
    return {
        "total_tokens": int(getattr(cb, "total_tokens", 0) or 0),
        "prompt_tokens": int(getattr(cb, "prompt_tokens", 0) or 0),
        "completion_tokens": int(getattr(cb, "completion_tokens", 0) or 0),
        "successful_requests": int(getattr(cb, "successful_requests", 0) or 0),
        "total_cost_usd": float(getattr(cb, "total_cost", 0) or 0),
    }


class HealthAgent:
    """Thin wrapper around a LangChain OpenAI-tools agent."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.3, verbose: bool = True):
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
            max_iterations=5,
            handle_parsing_errors=True,
        )
        self._chat_history: list = []

    def _invoke(
        self,
        user_message: str,
        chat_history: list,
        on_step: Callable[[str, Any], None] | None,
        update_history: bool,
    ) -> dict[str, Any]:
        try:
            from langchain_community.callbacks.manager import get_openai_callback
        except ImportError:
            get_openai_callback = None  # type: ignore[assignment]

        if get_openai_callback is not None:
            with get_openai_callback() as cb:
                result = self.executor.invoke(
                    {"input": user_message, "chat_history": chat_history}
                )
            usage = _usage_from_callback(cb)
        else:
            result = self.executor.invoke(
                {"input": user_message, "chat_history": chat_history}
            )
            usage = None

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

        if update_history:
            self._chat_history.append(HumanMessage(content=user_message))
            self._chat_history.append(AIMessage(content=output))

        out: dict[str, Any] = {
            "output": output,
            "tool_calls": tool_calls,
            "tool_call_count": len(tool_calls),
        }
        if usage is not None:
            out["usage"] = usage
        return out

    def chat(self, user_message: str, on_step: Callable[[str, Any], None] | None = None) -> dict:
        """Send a user message and return output, tool trace, token usage, etc.

        `on_step` is an optional callback invoked as (tool_name, tool_input) when
        a tool is about to run, handy for live demo status updates.
        """
        return self._invoke(
            user_message,
            self._chat_history,
            on_step,
            update_history=True,
        )

    def run_ephemeral(
        self,
        user_message: str,
        on_step: Callable[[str, Any], None] | None = None,
    ) -> dict:
        """Single-shot run with empty chat history; does not mutate `_chat_history`.

        Used for daily briefing so the main conversation agent stays isolated.
        """
        return self._invoke(
            user_message,
            [],
            on_step,
            update_history=False,
        )

    def proactive_check(self, on_step: Callable[[str, Any], None] | None = None) -> dict:
        """Run the auto morning check-in. Intended for app load."""
        return self.chat(PROACTIVE_TRIGGER, on_step=on_step)

    def reset_history(self) -> None:
        self._chat_history = []
