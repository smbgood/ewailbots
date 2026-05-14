import asyncio
from typing import Dict, Any, Optional
from config import Config
from database import DatabaseManager
from openai_service import OpenAIService, OpenAIServiceError

class AIEmployee:
    def __init__(
        self,
        name: str,
        employee_type: str,
        parameters: Dict[str, Any],
        *,
        employee_id: Optional[int] = None,
        db: Optional[DatabaseManager] = None,
    ):
        self.id = employee_id
        self.name = name
        self.employee_type = employee_type
        self.parameters = parameters
        self.conversation_history = []
        self.db = db or DatabaseManager()
        
        # Centralized OpenAI integration boundary.
        self.openai = OpenAIService(api_key=Config.OPENAI_API_KEY)
        # assistant_id kept for backward compatibility with older configs; no longer used
        self.assistant_id: Optional[str] = self.parameters.get("assistant_id")
        # Stateful response tracking.
        self.conversation_id: Optional[str] = None
        self.previous_response_id: Optional[str] = None
    
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

        except asyncio.TimeoutError:
            return "I hit a timeout while generating that response. Please try again in a moment."
        except Exception as e:
            print(f"Error generating AI response for {self.name}: {e}")
            return "I apologize, but I'm experiencing technical difficulties right now. Please try again shortly."

    async def _generate_response_with_responses_api(self, message: str, context: str) -> str:
        """Primary path using the OpenAI Responses API with Conversations.

        - Creates a server-side conversation on first use and reuses it for context.
        """
        system_prompt = self._build_system_prompt(context)

        def _call_responses_api() -> str:
            model = (self.parameters.get("model") or Config.OPENAI_TEXT_MODEL).strip()
            temperature = float(self.parameters.get("temperature", 0.7))
            max_tokens = self.parameters.get("max_tokens")
            strategy = (Config.OPENAI_CONVERSATION_STRATEGY or "conversations").strip().lower()

            use_previous_response = strategy == "previous_response_id"
            conversation_id: Optional[str] = None
            previous_response_id: Optional[str] = None

            if use_previous_response:
                previous_response_id = self.previous_response_id
            else:
                if not self.conversation_id:
                    self.conversation_id = self.openai.create_conversation()
                conversation_id = self.conversation_id

            response = self.openai.generate_text(
                message=message,
                instructions=system_prompt,
                model=model,
                temperature=temperature,
                max_output_tokens=max_tokens if isinstance(max_tokens, int) else None,
                conversation_id=conversation_id,
                previous_response_id=previous_response_id,
                store=Config.OPENAI_RESPONSE_STORE,
            )

            # Track response chain for previous_response_id strategy.
            self.previous_response_id = response.get("response_id")
            return response.get("text") or "(No response text)"

        try:
            reply_text = await asyncio.wait_for(
                asyncio.to_thread(_call_responses_api),
                timeout=Config.OPENAI_TIMEOUT_SECONDS + 5,
            )
        except OpenAIServiceError:
            raise
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
        self.conversation_id = None
        self.previous_response_id = None
    
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
