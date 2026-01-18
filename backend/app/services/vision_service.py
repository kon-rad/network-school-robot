import base64
import anthropic
from typing import Optional
from ..config import get_settings

settings = get_settings()


class VisionService:
    def __init__(self):
        self.client: Optional[anthropic.Anthropic] = None
        self.model = "claude-sonnet-4-20250514"
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Anthropic client."""
        api_key = settings.anthropic_api_key
        if api_key:
            self.client = anthropic.Anthropic(api_key=api_key)

    def is_configured(self) -> bool:
        return self.client is not None

    async def analyze_image(self, image_base64: str, prompt: str = None) -> dict:
        """Analyze an image using Claude's vision capabilities."""
        if not self.client:
            return {"success": False, "message": "Vision not configured", "description": None}

        if prompt is None:
            prompt = "What do you see in this image? Be concise and describe the key elements."

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )

            description = response.content[0].text
            return {
                "success": True,
                "description": description,
                "message": "Image analyzed successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Vision error: {str(e)}",
                "description": None
            }

    async def describe_scene(self, image_base64: str) -> str:
        """Get a brief natural description of what's in the image."""
        result = await self.analyze_image(
            image_base64,
            "You're a friendly robot. Briefly describe what you see in 1-2 casual sentences, like you're telling a friend."
        )
        return result.get("description", "I couldn't quite see that clearly.")

    async def identify_person(self, image_base64: str) -> dict:
        """Try to describe the person in the image."""
        result = await self.analyze_image(
            image_base64,
            "Describe the person you see (general appearance, clothing, expression). Keep it brief and friendly. If no person is visible, say so."
        )
        return result

    async def read_text(self, image_base64: str) -> dict:
        """Read any text visible in the image."""
        result = await self.analyze_image(
            image_base64,
            "Read and transcribe any text visible in this image. If no text is visible, say so briefly."
        )
        return result

    async def answer_about_image(self, image_base64: str, question: str) -> str:
        """Answer a specific question about the image."""
        result = await self.analyze_image(image_base64, question)
        return result.get("description", "I'm not sure about that.")


vision_service = VisionService()
