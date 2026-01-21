"""
Convex Service - Real-time AI backend for messages and data.
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from convex import ConvexClient

from ..config import get_settings

settings = get_settings()


class ConvexService:
    def __init__(self):
        self.deployment_url = getattr(settings, 'convex_url', '') or ''
        self.enabled = bool(self.deployment_url)
        self._client = None

    def _get_client(self):
        """Get or create Convex client."""
        if self._client is None and self.enabled:
            self._client = ConvexClient(self.deployment_url)
        return self._client

    def is_configured(self) -> bool:
        return self.enabled

    async def save_message(self, user_id: str, role: str, content: str,
                          personality: str = "tars", metadata: Optional[dict] = None) -> dict:
        """Save a chat message to Convex."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured"}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            message_data = {
                "userId": user_id,
                "role": role,
                "content": content,
                "personality": personality,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            result = await loop.run_in_executor(
                None,
                lambda: client.mutation("messages:saveMessage", message_data)
            )

            return {
                "success": True,
                "message_id": str(result) if result else None
            }

        except Exception as e:
            print(f"[Convex] Save message error: {e}")
            return {"success": False, "message": str(e)}

    async def get_messages(self, user_id: str, limit: int = 50) -> dict:
        """Get chat messages for a user from Convex."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured", "messages": []}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            messages = await loop.run_in_executor(
                None,
                lambda: client.query("messages:getMessages", {"userId": user_id, "limit": limit})
            )

            return {
                "success": True,
                "messages": messages or []
            }

        except Exception as e:
            print(f"[Convex] Get messages error: {e}")
            return {"success": False, "message": str(e), "messages": []}

    async def save_person(self, person_data: dict) -> dict:
        """Save a recognized person to Convex."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured"}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            result = await loop.run_in_executor(
                None,
                lambda: client.mutation("people:savePerson", person_data)
            )

            return {"success": True, "person_id": str(result) if result else None}

        except Exception as e:
            print(f"[Convex] Save person error: {e}")
            return {"success": False, "message": str(e)}

    async def get_people(self) -> dict:
        """Get all recognized people from Convex."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured", "people": []}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            people = await loop.run_in_executor(
                None,
                lambda: client.query("people:getPeople", {})
            )

            return {"success": True, "people": people or []}

        except Exception as e:
            print(f"[Convex] Get people error: {e}")
            return {"success": False, "message": str(e), "people": []}

    async def log_interaction(self, user_id: str, person_id: str,
                             interaction_type: str, notes: str = "") -> dict:
        """Log an interaction to Convex."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured"}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            interaction_data = {
                "userId": user_id,
                "personId": person_id,
                "type": interaction_type,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }

            result = await loop.run_in_executor(
                None,
                lambda: client.mutation("interactions:logInteraction", interaction_data)
            )

            return {"success": True, "interaction_id": str(result) if result else None}

        except Exception as e:
            print(f"[Convex] Log interaction error: {e}")
            return {"success": False, "message": str(e)}

    async def save_token_mint(self, mint_data: dict) -> dict:
        """Save token mint record to Convex."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured"}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            mint_data["timestamp"] = datetime.now().isoformat()

            result = await loop.run_in_executor(
                None,
                lambda: client.mutation("tokens:saveMint", mint_data)
            )

            return {"success": True, "mint_id": str(result) if result else None}

        except Exception as e:
            print(f"[Convex] Save token mint error: {e}")
            return {"success": False, "message": str(e)}

    async def get_user_tokens(self, user_id: str) -> dict:
        """Get token balance for a user."""
        if not self.enabled:
            return {"success": False, "message": "Convex not configured", "tokens": []}

        try:
            client = self._get_client()
            loop = asyncio.get_event_loop()

            tokens = await loop.run_in_executor(
                None,
                lambda: client.query("tokens:getUserTokens", {"userId": user_id})
            )

            return {"success": True, "tokens": tokens or []}

        except Exception as e:
            print(f"[Convex] Get tokens error: {e}")
            return {"success": False, "message": str(e), "tokens": []}


# Singleton instance
convex_service = ConvexService()
