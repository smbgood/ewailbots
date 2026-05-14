import unittest
from unittest.mock import MagicMock, patch

from ai_employee import AIEmployee


class AIEmployeeConversationTests(unittest.IsolatedAsyncioTestCase):
    @patch("ai_employee.OpenAIService")
    async def test_reset_clears_local_and_remote_state(self, mock_service_cls):
        mock_service = MagicMock()
        mock_service_cls.return_value = mock_service

        employee = AIEmployee(
            name="TestEmp",
            employee_type="GENERAL",
            parameters={"model": "gpt-5.5-mini"},
            employee_id=1,
            db=MagicMock(),
        )
        employee.conversation_history = [{"user": "a", "assistant": "b"}]
        employee.conversation_id = "conv_1"
        employee.previous_response_id = "resp_1"

        await employee.reset_conversation()

        self.assertEqual(employee.conversation_history, [])
        self.assertIsNone(employee.conversation_id)
        self.assertIsNone(employee.previous_response_id)


if __name__ == "__main__":
    unittest.main()
