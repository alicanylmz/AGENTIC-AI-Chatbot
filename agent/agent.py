"""Agent construction and command-line entry point."""
import os
from pathlib import Path
from uuid import uuid4
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS


def build_agent(model=None):
    """Create isolated in-memory state; inject a model for offline tests."""
    if model is None:
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Set GOOGLE_API_KEY in the project .env or environment. See README.md.")
        model = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
                                      api_key=key, temperature=0, max_retries=2, timeout=60)
    return create_agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT,
                        checkpointer=InMemorySaver()), model


def main():
    from .records import file_ticket
    agent, model = build_agent()
    config = {"configurable": {"thread_id": uuid4().hex}, "recursion_limit": 20}
    print("Husky Tech demo. Type quit to finish and generate a ticket summary.")
    result = None
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in {"quit", "exit"}:
            break
        if not text:
            continue
        result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
        print("Agent:", result["messages"][-1].text)
    if result:
        print(file_ticket(model, result).model_dump_json(indent=2))

if __name__ == "__main__":
    main()
