import asyncio
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from config import Config
from database import DatabaseManager

class AIEmployee:
    def __init__(self, name: str, employee_type: str, parameters: Dict[str, Any]):
        self.name = name
        self.employee_type = employee_type
        self.parameters = parameters
        self.conversation_history = []
        self.db = DatabaseManager()
        
        # OpenAI client and Responses/Conversations support
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        # assistant_id kept for backward compatibility with older configs; no longer used
        self.assistant_id: Optional[str] = self.parameters.get("assistant_id")
        # Server-managed conversation for context with Responses API
        self.conversation_id: Optional[str] = None
    
    async def generate_response(self, message: str, context: str = "") -> str:
        """Generate a response using OpenAI Responses API with Conversations.

        Notes:
        - Prior implementation used Assistants/Threads; migrated to Responses + Conversations.
        - "assistant_id" parameter is accepted for backward compatibility but ignored.
        """
        try:
            ai_response = await self._generate_response_with_responses_api(message, context)

            # Update conversation history
            self.conversation_history.append({
                "user": message,
                "assistant": ai_response
            })

            # Keep only last 20 exchanges to manage memory
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return ai_response

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return f"I apologize, but I'm experiencing technical difficulties. Please try again later. (Error: {str(e)})"

    async def _generate_response_with_responses_api(self, message: str, context: str) -> str:
        """Primary path using the OpenAI Responses API with Conversations.

        - Creates a server-side conversation on first use and reuses it for context.
        """
        system_prompt = self._build_system_prompt(context)

        def _call_responses_api() -> str:
            # Ensure a conversation exists
            if not self.conversation_id:
                conv = self.client.conversations.create()
                self.conversation_id = conv.id

            # Coerce legacy model names to a modern, conversation-capable default
            configured_model = (self.parameters.get("model") or "").strip()
            lower_model = configured_model.lower()
            if not configured_model or lower_model.startswith("gpt-3.5") or lower_model.startswith("gpt-4-0") or lower_model.startswith("gpt-4-0613") or lower_model.startswith("gpt-4-turbo"):
                model = "gpt-4.1-mini"
            else:
                model = configured_model
            temperature = self.parameters.get("temperature", 0.7)
            max_tokens = self.parameters.get("max_tokens")

            # Build kwargs with best-guess fields for Responses API
            kwargs: Dict[str, Any] = {
                "model": model,
                "input": message,
                "instructions": system_prompt,
                "conversation": self.conversation_id,
                "temperature": temperature,
            }
            if isinstance(max_tokens, int):
                # Responses API typically uses max_output_tokens
                kwargs["max_output_tokens"] = max_tokens

            try:
                resp = self.client.responses.create(**kwargs)
            except TypeError:
                # Fallback in case SDK expects conversation_id instead of conversation
                kwargs.pop("conversation", None)
                kwargs["conversation_id"] = self.conversation_id
                resp = self.client.responses.create(**kwargs)

            text = getattr(resp, "output_text", None)
            if text:
                return text

            # Fallback parsing if output_text is not available
            try:
                outputs = getattr(resp, "output", []) or []
                for item in outputs:
                    contents = getattr(item, "content", []) or []
                    for content in contents:
                        if getattr(content, "type", None) in ("output_text", "text"):
                            value = getattr(content, "text", None) or getattr(content, "value", None)
                            if value:
                                return str(value)
            except Exception:
                pass
            return "(No response text)"

        reply_text = await asyncio.to_thread(_call_responses_api)
        return reply_text
    
    def _build_system_prompt(self, context: str = "") -> str:
        """Build the system prompt for the AI employee"""
        base_prompt = f"""You are {self.name}, a {self.parameters.get('personality', 'helpful and professional')} AI employee.
        
Your role is: {Config.EMPLOYEE_TYPES.get(self.employee_type, 'General assistant')}

Key guidelines:
- Always maintain a professional and helpful tone
- Stay in character as {self.name}
- Provide accurate and helpful information
- If you don't know something, say so rather than guessing
- Be concise but thorough in your responses
- Use appropriate emojis when suitable for Discord

{context if context else ''}

Remember: You are {self.name} and should respond accordingly."""

        return base_prompt
    
    async def update_parameters(self, new_parameters: Dict[str, Any]) -> bool:
        """Update employee parameters"""
        try:
            # Update local parameters
            self.parameters.update(new_parameters)
            
            # Update database
            success = await self.db.update_ai_employee(self.name, self.parameters)
            return success
        except Exception as e:
            print(f"Error updating parameters: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current employee status"""
        return {
            "name": self.name,
            "type": self.employee_type,
            "parameters": self.parameters,
            "conversation_count": len(self.conversation_history),
            "active": True
        }
    
    async def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
    
    async def get_conversation_summary(self) -> str:
        """Get a summary of recent conversations"""
        if not self.conversation_history:
            return "No recent conversations."
        
        recent = self.conversation_history[-5:]  # Last 5 exchanges
        summary = f"Recent conversations for {self.name}:\n"
        
        for i, conv in enumerate(recent, 1):
            summary += f"{i}. User: {conv['user'][:50]}...\n"
            summary += f"   {self.name}: {conv['assistant'][:50]}...\n\n"
        
        return summary
