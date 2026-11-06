"""Local browser UI with a separate conversation ID for every browser session."""
from uuid import uuid4
import gradio as gr
from agent.agent import build_agent


def create_demo(agent):
    def respond(message, history, thread_id):
        result = agent.invoke({"messages": [{"role": "user", "content": message}]},
                              {"configurable": {"thread_id": thread_id}, "recursion_limit": 20})
        return result["messages"][-1].text

    with gr.Blocks(title="AGENTIC AI - Chatbot") as demo:
        thread = gr.State(value=lambda: uuid4().hex)
        chat = gr.ChatInterface(fn=respond, additional_inputs=[thread],
            title="AGENTIC AI - Chatbot",
            description="Husky Tech customer support demo • Fictional orders • Demo date: September 25, 2026",
            examples=[["Where is order HT-1002?"], ["Can I return HT-1001?"],
                      ["What is your warranty policy?"], ["I would like to speak to a person."]])
        chat.chatbot.clear(lambda: uuid4().hex, outputs=[thread])
    return demo

if __name__ == "__main__":
    agent, _ = build_agent()
    create_demo(agent).launch(server_name="127.0.0.1", share=False)
