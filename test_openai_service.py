import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from openai_service import OpenAIService


class OpenAIServiceTests(unittest.TestCase):
    @patch("openai_service.OpenAI")
    def test_generate_text_prefers_output_text(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.create.return_value = SimpleNamespace(
            id="resp_1",
            output_text="hello world",
        )

        service = OpenAIService(api_key="sk-test")
        response = service.generate_text(
            message="hello",
            instructions="be helpful",
            model="gpt-5.5-mini",
            temperature=0.7,
            max_output_tokens=200,
            conversation_id="conv_1",
            store=True,
        )

        self.assertEqual(response["text"], "hello world")
        self.assertEqual(response["response_id"], "resp_1")
        called_kwargs = mock_client.responses.create.call_args.kwargs
        self.assertEqual(called_kwargs["conversation"], "conv_1")
        self.assertTrue(called_kwargs["store"])
        self.assertEqual(called_kwargs["max_output_tokens"], 200)

    @patch("openai_service.OpenAI")
    def test_generate_text_falls_back_to_output_items(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.responses.create.return_value = SimpleNamespace(
            id="resp_2",
            output=[
                SimpleNamespace(
                    content=[
                        SimpleNamespace(type="output_text", text="fallback text"),
                    ]
                )
            ],
        )

        service = OpenAIService(api_key="sk-test")
        response = service.generate_text(
            message="hello",
            instructions="be helpful",
            model="gpt-5.5-mini",
            temperature=0.7,
        )
        self.assertEqual(response["text"], "fallback text")

    @patch("openai_service.OpenAI")
    def test_generate_image_requests_b64_payload(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        image_result = SimpleNamespace(b64_json="ZmFrZQ==", revised_prompt="rev")
        mock_client.images.generate.return_value = SimpleNamespace(data=[image_result])

        service = OpenAIService(api_key="sk-test")
        output = service.generate_image(
            prompt="cat",
            model="gpt-image-2",
            size="1024x1024",
            quality="medium",
            output_format="png",
            moderation="auto",
            background="auto",
        )
        self.assertEqual(output, image_result)
        called_kwargs = mock_client.images.generate.call_args.kwargs
        self.assertEqual(called_kwargs["response_format"], "b64_json")
        self.assertEqual(called_kwargs["model"], "gpt-image-2")


if __name__ == "__main__":
    unittest.main()
