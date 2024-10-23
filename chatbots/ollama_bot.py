from .chatbot import Chatbot
import asyncio
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Optional

class OllamaBot(Chatbot):
    def __init__(self, personality: Optional[Dict[str, str]] = None, model: str = "llama3.2"):
        super().__init__("Ollama")
        # Initialize OpenAI client with custom base URL
        self.client = OpenAI(
            base_url="https://verified-suitably-baboon.ngrok-free.app/v1",
            api_key="not-needed"  # Can be any string
        )
        self.model = model
        self.conversation_history: List[Dict[str, str]] = []
        self.personality = personality or {
            "role": "system",
            "content": (
                "You are a friendly and helpful assistant. "
                "Respond in a conversational and approachable manner, "
                "using clear and concise language. "
                "Feel free to use a touch of humor where appropriate."
            )
        }
        # Initialize conversation history with the personality
        self.conversation_history.append(self.personality)
        
    async def process_message(self, message: str) -> str:
        # Add the user's message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Create a chat completion using the OpenAI client
            chat_completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=self.conversation_history,
                model=self.model,
                temperature=0.7,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Get the response
            response = chat_completion.choices[0].message.content
            
            # Add the assistant's response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })
            
            # Keep conversation history to a reasonable size (last 10 messages)
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            return response
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def format_message(self, response: str) -> str:
        """Format the bot's response with timestamp and bot name."""
        timestamp = datetime.now().strftime("%H:%M")
        return f"{timestamp} {self.name}: {response}\n"
    
    async def reset_conversation(self):
        """Reset the conversation history to start fresh."""
        self.conversation_history = [self.personality]
