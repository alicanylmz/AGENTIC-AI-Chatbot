import unittest
from datetime import timedelta
from unittest.mock import patch
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from agent.agent import build_agent
from agent import tools
from app import create_demo

class ToolCallingModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

class ChatbotTests(unittest.TestCase):
    def test_order_normalization_and_unknown(self):
        self.assertEqual(tools.look_up_order.invoke({'order_id': ' ht-1001 '})['item'], 'Wireless headphones')
        self.assertIn('error', tools.look_up_order.invoke({'order_id': 'missing'}))

    def test_return_cases(self):
        self.assertTrue(tools.check_return_eligibility.invoke({'order_id': 'HT-1001'})['eligible'])
        for order_id in ['HT-1002', 'HT-1003', 'HT-1004', 'unknown']:
            self.assertFalse(tools.check_return_eligibility.invoke({'order_id': order_id})['eligible'])

    def test_return_boundaries(self):
        for days, eligible in [(0, True), (30, True), (31, False), (-1, False)]:
            record = {'status': 'delivered', 'delivered_on': (tools.DEMO_DATE - timedelta(days=days)).isoformat()}
            with patch.dict(tools.ORDERS, {'BOUNDARY': record}):
                self.assertEqual(tools.check_return_eligibility.invoke({'order_id': 'BOUNDARY'})['eligible'], eligible)

    def test_faq_multiple_topics_and_unknown(self):
        self.assertEqual(set(tools.search_faq.invoke({'question': 'shipping and returns'})), {'shipping', 'return'})
        self.assertIn('message', tools.search_faq.invoke({'question': 'unrelated'}))

    def test_escalations_are_simulated_and_unique(self):
        a = tools.escalate_to_human.invoke({'reason': 'Please help'})
        b = tools.escalate_to_human.invoke({'reason': 'Please help'})
        self.assertEqual(a['status'], 'simulated')
        self.assertNotEqual(a['ticket_id'], b['ticket_id'])

    def test_real_graph_executes_tool_and_separates_threads(self):
        model = ToolCallingModel(responses=[
            AIMessage(content='', tool_calls=[{'name': 'look_up_order', 'args': {'order_id': 'HT-1002'}, 'id': 'call1', 'type': 'tool_call'}]),
            AIMessage(content='Your keyboard has shipped.'),
            AIMessage(content='Another conversation.'),
            AIMessage(content='I remember your keyboard.'),
        ])
        agent, _ = build_agent(model)
        first = {'configurable': {'thread_id': 'first'}}
        second = {'configurable': {'thread_id': 'second'}}
        result = agent.invoke({'messages': [{'role': 'user', 'content': 'Where is HT-1002?'}]}, first)
        self.assertTrue(any(m.type == 'tool' and 'Mechanical keyboard' in m.content for m in result['messages']))
        result2 = agent.invoke({'messages': [{'role': 'user', 'content': 'Hello'}]}, second)
        self.assertEqual(len(result2['messages']), 2)
        result3 = agent.invoke({'messages': [{'role': 'user', 'content': 'What item?'}]}, first)
        self.assertEqual(len(result3['messages']), 6)

    def test_ui_builds_without_credentials(self):
        agent, _ = build_agent(ToolCallingModel(responses=[AIMessage(content='Hello')]))
        demo = create_demo(agent)
        self.assertTrue(demo.config['components'])
        demo.close()

if __name__ == '__main__':
    unittest.main()
