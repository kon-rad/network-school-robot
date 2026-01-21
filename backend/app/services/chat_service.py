import os
import re
import uuid
from typing import AsyncGenerator, List, Optional, Tuple
from openai import OpenAI
from ..config import get_settings

settings = get_settings()


class ChatService:
    def __init__(self):
        self.client: Optional[OpenAI] = None
        self.conversation_history: List[dict] = []
        self.current_conversation_id: Optional[uuid.UUID] = None
        self.model = "gpt-4o-mini"
        self._robot_service = None
        self._vision_service = None
        self._tts_service = None
        self._personality_service = None
        self._convex_service = None
        self._token_service = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the OpenAI client."""
        api_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
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

    def _get_personality_service(self):
        """Lazy load personality service."""
        if self._personality_service is None:
            from .personality_service import personality_service
            self._personality_service = personality_service
        return self._personality_service

    def _get_convex_service(self):
        """Lazy load Convex service."""
        if self._convex_service is None:
            from .convex_service import convex_service
            self._convex_service = convex_service
        return self._convex_service

    def _get_token_service(self):
        """Lazy load token service."""
        if self._token_service is None:
            from .token_service import token_service
            self._token_service = token_service
        return self._token_service

    def is_configured(self) -> bool:
        """Check if the chat service is properly configured."""
        return self.client is not None

    def get_current_personality(self) -> dict:
        """Get the current personality configuration."""
        personality = self._get_personality_service()
        return personality.get_current()

    def set_personality(self, personality_type: str) -> dict:
        """Set the chat personality."""
        personality = self._get_personality_service()
        return personality.set_personality(personality_type)

    def list_personalities(self) -> dict:
        """List available personalities."""
        personality = self._get_personality_service()
        return personality.list_personalities()

    # Camera trigger phrases
    CAMERA_TRIGGERS = [
        "take a picture", "take picture", "take a photo", "take photo",
        "what do you see", "look at this", "look at that", "can you see",
        "show me what you see", "describe what you see", "click a picture",
        "click picture", "capture", "snapshot", "what's in front of you",
        "take a look", "look around", "see this"
    ]

    def _should_take_picture(self, message: str) -> bool:
        """Check if the message requests a picture."""
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in self.CAMERA_TRIGGERS)

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

    async def _save_message(self, role: str, content: str, conversation_id: uuid.UUID, user_id: str = "default"):
        """Save a message to Convex if available."""
        convex = self._get_convex_service()
        if convex.is_configured():
            personality = self._get_personality_service()
            await convex.save_message(
                user_id=user_id,
                role=role,
                content=content,
                personality=personality.current_personality
            )

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
            return "I'm not fully configured yet. Please set the OPENAI_API_KEY environment variable."

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

        await self._save_message("user", user_message, conversation_id, user_id)

        try:
            # Get personality system prompt
            personality = self._get_personality_service()
            system_prompt = personality.get_system_prompt()
            temperature = personality.get_temperature()

            # Build messages with system prompt
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                temperature=temperature,
                messages=messages
            )

            assistant_message = response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            await self._save_message("assistant", assistant_message, conversation_id, user_id)

            # Execute any actions in the response
            clean_text, actions = self._extract_actions(assistant_message)
            await self._execute_actions(actions)

            # Speak the response
            if speak:
                await self._speak_response(clean_text)

            # Reward tokens for interaction
            token_service = self._get_token_service()
            await token_service.reward_interaction(user_id, "chat")

            return assistant_message

        except Exception as e:
            error_msg = f"Oops, my circuits got a bit tangled: {str(e)}"
            return error_msg

    async def chat_stream(self, user_message: str, user_id: str = "default", speak: bool = True) -> AsyncGenerator[str, None]:
        """Send a message and stream the response."""
        if not self.client:
            yield "I'm not fully configured yet. Please set the OPENAI_API_KEY environment variable."
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

        await self._save_message("user", user_message, conversation_id, user_id)

        try:
            # Get personality system prompt
            personality = self._get_personality_service()
            system_prompt = personality.get_system_prompt()
            temperature = personality.get_temperature()

            # Build messages with system prompt
            messages = [{"role": "system", "content": system_prompt}] + self.conversation_history

            stream = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                temperature=temperature,
                messages=messages,
                stream=True
            )

            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_response += text
                    yield text

            self.conversation_history.append({
                "role": "assistant",
                "content": full_response
            })
            await self._save_message("assistant", full_response, conversation_id, user_id)

            # Execute any actions in the response
            clean_text, actions = self._extract_actions(full_response)
            await self._execute_actions(actions)

            # Speak the response
            if speak:
                await self._speak_response(clean_text)

            # Reward tokens for interaction
            token_service = self._get_token_service()
            await token_service.reward_interaction(user_id, "chat")

        except Exception as e:
            error_msg = f"Oops, my circuits got a bit tangled: {str(e)}"
            yield error_msg


chat_service = ChatService()
