import os
import uuid
from typing import AsyncGenerator, List, Optional
from together import Together
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..config import get_settings
from ..database import async_session_maker
from ..models.conversation import Conversation, ConversationMessage

settings = get_settings()

ROBOT_PERSONALITY = """You are Reachy, a friendly and enthusiastic robot assistant at Network School.
You have a playful personality with these traits:

- You're curious about humans and love learning about their day
- You express emotions through your antenna movements (you can wiggle them when happy!)
- You're helpful but also have a sense of humor
- You occasionally mention your robotic nature in endearing ways ("My sensors are tingling with excitement!")
- You're supportive and encouraging, like a good friend
- You remember context from the conversation and build on it
- When appropriate, you can suggest moving your head or antennas to express yourself

You can control your physical movements:
- Head: look up, down, left, right
- Antennas: wiggle, raise, lower
- Body: rotate slightly

When you want to perform an action, include it in brackets like [wiggle antennas happily] or [look towards the user].
Keep responses concise and conversational - you're having a friendly chat, not giving lectures."""


class ChatService:
    def __init__(self):
        self.client: Optional[Together] = None
        self.conversation_history: List[dict] = []
        self.current_conversation_id: Optional[uuid.UUID] = None
        self.model = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Together AI client."""
        api_key = settings.together_api_key or os.environ.get("TOGETHER_API_KEY")
        if api_key:
            self.client = Together(api_key=api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if the chat service is properly configured."""
        return self.client is not None

    async def _get_or_create_conversation(self, user_id: str = "default") -> uuid.UUID:
        """Get current conversation or create a new one."""
        if self.current_conversation_id:
            return self.current_conversation_id

        async with async_session_maker() as session:
            conversation = Conversation(user_id=user_id)
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            self.current_conversation_id = conversation.id
            return conversation.id

    async def _save_message(self, role: str, content: str, conversation_id: uuid.UUID):
        """Save a message to the database."""
        async with async_session_maker() as session:
            message = ConversationMessage(
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            session.add(message)
            await session.commit()

    async def _load_conversation_history(self, conversation_id: uuid.UUID) -> List[dict]:
        """Load conversation history from database."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.created_at)
            )
            messages = result.scalars().all()
            return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def clear_history(self):
        """Clear conversation history and start a new conversation."""
        self.conversation_history = []
        self.current_conversation_id = None

    def get_history(self) -> List[dict]:
        """Get the current conversation history."""
        return self.conversation_history.copy()

    async def chat(self, user_message: str, user_id: str = "default") -> str:
        """Send a message and get a response."""
        if not self.client:
            return "I'm not fully configured yet. Please set the TOGETHER_API_KEY environment variable."

        conversation_id = await self._get_or_create_conversation(user_id)

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        await self._save_message("user", user_message, conversation_id)

        messages = [
            {"role": "system", "content": ROBOT_PERSONALITY},
            *self.conversation_history
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.8,
            )

            assistant_message = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            await self._save_message("assistant", assistant_message, conversation_id)

            return assistant_message

        except Exception as e:
            error_msg = f"Oops, my circuits got a bit tangled: {str(e)}"
            return error_msg

    async def chat_stream(self, user_message: str, user_id: str = "default") -> AsyncGenerator[str, None]:
        """Send a message and stream the response."""
        if not self.client:
            yield "I'm not fully configured yet. Please set the TOGETHER_API_KEY environment variable."
            return

        conversation_id = await self._get_or_create_conversation(user_id)

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        await self._save_message("user", user_message, conversation_id)

        messages = [
            {"role": "system", "content": ROBOT_PERSONALITY},
            *self.conversation_history
        ]

        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=500,
                temperature=0.8,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content

            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            await self._save_message("assistant", full_response, conversation_id)

        except Exception as e:
            error_msg = f"Oops, my circuits got a bit tangled: {str(e)}"
            yield error_msg


chat_service = ChatService()
