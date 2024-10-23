# chatbots/gpt_bot.py

from .chatbot import Chatbot
import asyncio
import os
import re
from openai import OpenAI
from typing import List, Dict, Optional
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

class GPTBot(Chatbot):
    URL_REGEX = re.compile(
        r'(https?://(?:www\.|(?!www))[^\s]+)|(www\.[^\s]+)'
    )
    
    def __init__(self, personality: Optional[Dict[str, str]] = None):
        super().__init__("GPT")
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.conversation_history: List[Dict[str, str]] = []
        self.session: Optional[aiohttp.ClientSession] = None  # Initialize as None
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

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def fetch_url_content(self, url: str) -> Optional[str]:
        # Initialize the session if it hasn't been created yet
        if self.session is None:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    html = await response.text()
                    return self.extract_text_from_html(html)
                else:
                    return f"Failed to fetch URL: {url} with status code {response.status}"
        except Exception as e:
            return f"Error fetching URL: {url}. Error: {str(e)}"
    
    def extract_text_from_html(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts and styles
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n')
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Optionally, truncate to a reasonable length
        max_length = 2000  # Adjust as needed
        return text[:max_length] + ('...' if len(text) > max_length else '')
    
    async def process_message(self, message: str) -> str:
        # Detect URLs in the message
        urls = self.extract_urls(message)
        if urls:
            for url in urls:
                content = await self.fetch_url_content(url)
                if content:
                    # Add the fetched content to the conversation history as a system message
                    self.conversation_history.append({
                        "role": "system",
                        "content": f"Content from {url}:\n{content}"
                    })
        
        # Add the user's message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Create a chat completion
            chat_completion = await asyncio.to_thread(
                self.client.chat.completions.create,
                messages=self.conversation_history,
                model="gpt-4",  # Use GPT-4 for better performance
                temperature=0.7,  # Adjusted for a friendly tone
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
                # max_tokens=150  # Limit response length if desired
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
    
    def extract_urls(self, text: str) -> List[str]:
        matches = self.URL_REGEX.findall(text)
        urls = []
        for match in matches:
            url = match[0] or match[1]
            if not url.startswith('http'):
                url = 'http://' + url
            urls.append(url)
        return urls
    
    def format_message(self, response: str) -> str:
        """Format the bot's response with timestamp and bot name."""
        timestamp = datetime.now().strftime("%H:%M")
        return f"{timestamp} {self.name}: {response}\n"
    
    async def reset_conversation(self):
        """Reset the conversation history to start fresh."""
        self.conversation_history = [self.personality]
