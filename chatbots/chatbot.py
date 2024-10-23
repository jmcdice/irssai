# chatbots/chatbot.py
import random
from datetime import datetime

class Chatbot:
    def __init__(self, name: str):
        self.name = name
        self.color = f"38;5;{random.randint(1, 255)}"  # Random ANSI color

    async def process_message(self, message: str) -> str:
        """Process a message and return a response."""
        raise NotImplementedError

    def format_message(self, message: str) -> str:
        """Format the bot's message with color and name."""
        timestamp = datetime.now().strftime("%H:%M")
        return f"\x1b[{self.color}m{timestamp} {self.name}: {message}\x1b[0m\n"
