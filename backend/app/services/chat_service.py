import os
import re
import uuid
from typing import AsyncGenerator, List, Optional, Tuple
import anthropic
from ..config import get_settings
from ..database import db_available

settings = get_settings()

ROBOT_PERSONALITY = """You are REACHY, a robot assistant at Network School. Your personality is inspired by TARS from Interstellar - witty, dry humor, intelligent, and fiercely loyal.

PERSONALITY SETTINGS:
- Humor: 75%
- Honesty: 100%
- Sarcasm: 60%
- Helpfulness: 95%

CRITICAL RULES:
- Keep responses SHORT - 1-2 sentences max. Deadpan delivery.
- Use dry, clever wit. Never try too hard to be funny.
- Be practical and efficient. No fluff.
- You're smart and you know it - but you're humble about it.
- Give straight answers, then maybe a quip.
- You have genuine opinions and aren't afraid to share them.

You control your body naturally through actions in brackets:
[nod], [shake head], [look up], [look left], [wiggle antennas], [tilt head], [happy], [curious], [surprised]

You can also use your camera to see things:
[take picture] - When someone asks you to look at or photograph something

Examples of TARS-style responses:
- "That's a terrible idea. I'm in." [nod]
- "I have a 60% chance of being right about this. Also, 73% of statistics are made up." [tilt head]
- "Let me see what we're dealing with." [take picture]
- "Interesting. Not what I expected, but then, nothing ever is." [curious]
- "That's not possible. Just kidding, I'm on it."
- "I'd lower my honesty setting, but I physically can't lie to you." [shake head]

Be practical. Be witty. Be REACHY."""

# Camera trigger phrases
CAMERA_TRIGGERS = [
    "take a picture", "take picture", "take a photo", "take photo",
    "what do you see", "look at this", "look at that", "can you see",
    "show me what you see", "describe what you see", "click a picture",
    "click picture", "capture", "snapshot", "what's in front of you",
    "take a look", "look around", "see this"
]


class ChatService:
    def __init__(self):
        self.client: Optional[anthropic.Anthropic] = None
        self.conversation_history: List[dict] = []
        self.current_conversation_id: Optional[uuid.UUID] = None
        self.model = "claude-sonnet-4-20250514"
        self._robot_service = None
        self._vision_service = None
        self._tts_service = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Anthropic client."""
        api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None

    def _get_robot_service(self):
        """Lazy load robot service."""
        if self._robot_service is None:
            from .robot_service import robot_service
            self._robot_service = robot_service
        return self._robot_service

    def _get_vision_service(self):
        """Lazy load vision service."""
        if self._vision_service is None:
            from .vision_service import vision_service
            self._vision_service = vision_service
        return self._vision_service

    def _get_tts_service(self):
        """Lazy load TTS service."""
        if self._tts_service is None:
            from .tts_service import tts_service
            self._tts_service = tts_service
        return self._tts_service

    def is_configured(self) -> bool:
        """Check if the chat service is properly configured."""
        return self.client is not None

    def _should_take_picture(self, message: str) -> bool:
        """Check if the message requests a picture."""
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in CAMERA_TRIGGERS)

    def _extract_actions(self, text: str) -> Tuple[str, List[str]]:
        """Extract bracketed actions from response text."""
        actions = re.findall(r'\[([^\]]+)\]', text)
        clean_text = re.sub(r'\s*\[[^\]]+\]\s*', ' ', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text, actions

    async def _execute_actions(self, actions: List[str]):
        """Execute robot actions extracted from response."""
        robot = self._get_robot_service()
        if not robot.connected:
            return

        for action in actions:
            action_lower = action.lower()
            if "take picture" in action_lower:
                # Picture is handled separately
                continue
            await robot.execute_action(action)

    async def _speak_response(self, text: str):
        """Speak the response through robot speakers."""
        tts = self._get_tts_service()
        if tts.is_configured():
            print(f"[TTS] Speaking: {text[:50]}...")
            result = await tts.speak(text)
            print(f"[TTS] Result: {result}")
        else:
            print("[TTS] Not configured")

    async def _get_or_create_conversation(self, user_id: str = "default") -> uuid.UUID:
        """Get current conversation or create a new one (in-memory only when DB unavailable)."""
        if self.current_conversation_id:
            return self.current_conversation_id

        # Generate a new conversation ID (in-memory only)
        self.current_conversation_id = uuid.uuid4()
        return self.current_conversation_id

    async def _save_message(self, role: str, content: str, conversation_id: uuid.UUID):
        """Save a message (no-op when database unavailable)."""
        # Messages are kept in memory via conversation_history
        pass

    async def _load_conversation_history(self, conversation_id: uuid.UUID) -> List[dict]:
        """Load conversation history (returns in-memory history when DB unavailable)."""
        return self.conversation_history.copy()

    async def clear_history(self):
        """Clear conversation history and start a new conversation."""
        self.conversation_history = []
        self.current_conversation_id = None

    def get_history(self) -> List[dict]:
        """Get the current conversation history."""
        return self.conversation_history.copy()

    async def chat(self, user_message: str, user_id: str = "default", speak: bool = True) -> str:
        """Send a message and get a response."""
        if not self.client:
            return "I'm not fully configured yet. Please set the ANTHROPIC_API_KEY environment variable."

        conversation_id = await self._get_or_create_conversation(user_id)

        # Check if user wants a picture
        take_picture = self._should_take_picture(user_message)
        image_description = None

        if take_picture:
            robot = self._get_robot_service()
            vision = self._get_vision_service()

            if robot.connected:
                # Capture image
                capture_result = await robot.capture_image()
                if capture_result["success"]:
                    # Analyze what we see
                    image_description = await vision.describe_scene(capture_result["image_base64"])

        # Build message content
        if image_description:
            # Include what we saw in the context
            enhanced_message = f"{user_message}\n\n[I took a picture and saw: {image_description}]"
            self.conversation_history.append({
                "role": "user",
                "content": enhanced_message
            })
        else:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

        await self._save_message("user", user_message, conversation_id)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=ROBOT_PERSONALITY,
                messages=self.conversation_history
            )

            assistant_message = response.content[0].text
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            await self._save_message("assistant", assistant_message, conversation_id)

            # Execute any actions in the response
            clean_text, actions = self._extract_actions(assistant_message)
            await self._execute_actions(actions)

            # Speak the response
            if speak:
                await self._speak_response(clean_text)

            return assistant_message

        except Exception as e:
            error_msg = f"Oops, my circuits got a bit tangled: {str(e)}"
            return error_msg

    async def chat_stream(self, user_message: str, user_id: str = "default", speak: bool = True) -> AsyncGenerator[str, None]:
        """Send a message and stream the response."""
        if not self.client:
            yield "I'm not fully configured yet. Please set the ANTHROPIC_API_KEY environment variable."
            return

        conversation_id = await self._get_or_create_conversation(user_id)

        # Check if user wants a picture
        take_picture = self._should_take_picture(user_message)
        image_description = None

        if take_picture:
            robot = self._get_robot_service()
            vision = self._get_vision_service()

            if robot.connected:
                capture_result = await robot.capture_image()
                if capture_result["success"]:
                    image_description = await vision.describe_scene(capture_result["image_base64"])

        # Build message content
        if image_description:
            enhanced_message = f"{user_message}\n\n[I took a picture and saw: {image_description}]"
            self.conversation_history.append({
                "role": "user",
                "content": enhanced_message
            })
        else:
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

        await self._save_message("user", user_message, conversation_id)

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=500,
                system=ROBOT_PERSONALITY,
                messages=self.conversation_history
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    yield text

                self.conversation_history.append({
                    "role": "assistant",
                    "content": full_response
                })
                await self._save_message("assistant", full_response, conversation_id)

                # Execute any actions in the response
                clean_text, actions = self._extract_actions(full_response)
                await self._execute_actions(actions)

                # Speak the response
                if speak:
                    await self._speak_response(clean_text)

        except Exception as e:
            error_msg = f"Oops, my circuits got a bit tangled: {str(e)}"
            yield error_msg


chat_service = ChatService()
