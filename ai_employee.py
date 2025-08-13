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
        
        # OpenAI client and Assistants support
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.assistant_id: Optional[str] = self.parameters.get("assistant_id")
        self.thread_id: Optional[str] = None
    
    async def generate_response(self, message: str, context: str = "") -> str:
        """Generate a response using OpenAI. Uses Assistants API if assistant_id is set; otherwise falls back to Chat Completions."""
        try:
            if self.assistant_id:
                ai_response = await self._generate_response_with_assistant(message, context)
            else:
                ai_response = await self._generate_response_with_chat_completions(message, context)

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

    async def _generate_response_with_chat_completions(self, message: str, context: str) -> str:
        """Fallback to Chat Completions for employees without assistant_id."""
        # Build the system prompt based on employee type and parameters
        system_prompt = self._build_system_prompt(context)

        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add conversation history if available
        if self.conversation_history:
            for conv in self.conversation_history[-5:]:  # Last 5 exchanges
                messages.append({"role": "user", "content": conv["user"]})
                messages.append({"role": "assistant", "content": conv["assistant"]})

        # Add current message
        messages.append({"role": "user", "content": message})

        # Use the legacy Chat Completions API via the new client
        def _call_chat_completions():
            # The new OpenAI SDK exposes chat.completions.create
            return self.client.chat.completions.create(
                model=self.parameters.get("model", "gpt-3.5-turbo"),
                messages=messages,
                temperature=self.parameters.get("temperature", 0.7),
                max_tokens=self.parameters.get("max_tokens", 1000)
            )

        response = await asyncio.to_thread(_call_chat_completions)
        return response.choices[0].message.content

    async def _generate_response_with_assistant(self, message: str, context: str) -> str:
        """Use the OpenAI Assistants API for responses when assistant_id is configured."""
        system_prompt = self._build_system_prompt(context)

        def _run_assistant_and_get_reply() -> str:
            # Ensure a thread exists for this employee instance
            if not self.thread_id:
                thread = self.client.beta.threads.create()
                self.thread_id = thread.id

            # Add the user message to the thread
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=message
            )

            # Create a run with optional instructions derived from our system prompt
            run = self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant_id,
                instructions=system_prompt
            )

            # Poll until the run completes
            while True:
                current = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id
                )
                if current.status in ("completed", "failed", "cancelled", "expired"):
                    break
                time.sleep(0.5)

            # If failed, provide a graceful message
            if current.status != "completed":
                return f"Assistant run did not complete successfully (status: {current.status})."

            # Fetch the latest assistant message
            messages_list = self.client.beta.threads.messages.list(thread_id=self.thread_id)
            for m in messages_list.data:
                if m.role == "assistant":
                    # Extract text content from message
                    parts = []
                    for c in m.content:
                        if getattr(c, "type", None) == "text" and getattr(c, "text", None):
                            parts.append(c.text.value)
                    if parts:
                        return "\n".join(parts)
            return "(No assistant reply available)"

        reply_text = await asyncio.to_thread(_run_assistant_and_get_reply)
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
