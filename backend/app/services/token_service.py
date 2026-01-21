"""
Token Service - Token minting and rewards system.
Supports both internal points system and blockchain token integration.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import json
import uuid

from ..config import get_settings

settings = get_settings()

# Local storage for tokens when Convex is not available
TOKENS_DIR = Path(__file__).parent.parent.parent / "data" / "tokens"
TOKENS_DIR.mkdir(parents=True, exist_ok=True)


class TokenType:
    INTERACTION = "interaction"      # Earned through interactions
    RECOGNITION = "recognition"      # Earned when recognized by robot
    COACHING = "coaching"            # Earned through coaching sessions
    ACHIEVEMENT = "achievement"      # Special achievements
    REFERRAL = "referral"           # Referring new users
    DAILY_CHECKIN = "daily_checkin" # Daily check-in bonus


# Token reward amounts
REWARD_AMOUNTS = {
    TokenType.INTERACTION: 1,
    TokenType.RECOGNITION: 5,
    TokenType.COACHING: 10,
    TokenType.ACHIEVEMENT: 50,
    TokenType.REFERRAL: 25,
    TokenType.DAILY_CHECKIN: 3
}


class TokenService:
    def __init__(self):
        self._convex_service = None
        self._balances: Dict[str, int] = {}
        self._transactions: List[dict] = []
        self._load_data()

    def _get_convex_service(self):
        """Lazy load Convex service."""
        if self._convex_service is None:
            from .convex_service import convex_service
            self._convex_service = convex_service
        return self._convex_service

    def _load_data(self):
        """Load token data from local storage."""
        balances_file = TOKENS_DIR / "balances.json"
        transactions_file = TOKENS_DIR / "transactions.json"

        if balances_file.exists():
            try:
                with open(balances_file, 'r') as f:
                    self._balances = json.load(f)
            except Exception:
                self._balances = {}

        if transactions_file.exists():
            try:
                with open(transactions_file, 'r') as f:
                    self._transactions = json.load(f)
            except Exception:
                self._transactions = []

    def _save_data(self):
        """Save token data to local storage."""
        try:
            with open(TOKENS_DIR / "balances.json", 'w') as f:
                json.dump(self._balances, f, indent=2)
            with open(TOKENS_DIR / "transactions.json", 'w') as f:
                json.dump(self._transactions[-1000:], f, indent=2)  # Keep last 1000
        except Exception as e:
            print(f"[Token] Failed to save data: {e}")

    async def mint_tokens(self, user_id: str, token_type: str,
                         amount: Optional[int] = None, reason: str = "") -> dict:
        """Mint tokens for a user."""
        if amount is None:
            amount = REWARD_AMOUNTS.get(token_type, 1)

        # Create transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "mint",
            "token_type": token_type,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # Update local balance
        if user_id not in self._balances:
            self._balances[user_id] = 0
        self._balances[user_id] += amount

        # Record transaction
        self._transactions.append(transaction)
        self._save_data()

        # Try to save to Convex
        convex = self._get_convex_service()
        if convex.is_configured():
            await convex.save_token_mint({
                "userId": user_id,
                "tokenType": token_type,
                "amount": amount,
                "reason": reason,
                "transactionId": transaction["id"]
            })

        return {
            "success": True,
            "transaction_id": transaction["id"],
            "amount": amount,
            "new_balance": self._balances[user_id],
            "message": f"Minted {amount} tokens for {token_type}"
        }

    async def transfer_tokens(self, from_user: str, to_user: str, amount: int,
                             reason: str = "") -> dict:
        """Transfer tokens between users."""
        # Check balance
        from_balance = self._balances.get(from_user, 0)
        if from_balance < amount:
            return {
                "success": False,
                "message": f"Insufficient balance. Have {from_balance}, need {amount}"
            }

        # Create transaction
        transaction = {
            "id": str(uuid.uuid4()),
            "type": "transfer",
            "from_user": from_user,
            "to_user": to_user,
            "amount": amount,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

        # Update balances
        self._balances[from_user] -= amount
        if to_user not in self._balances:
            self._balances[to_user] = 0
        self._balances[to_user] += amount

        self._transactions.append(transaction)
        self._save_data()

        return {
            "success": True,
            "transaction_id": transaction["id"],
            "amount": amount,
            "from_balance": self._balances[from_user],
            "to_balance": self._balances[to_user]
        }

    async def get_balance(self, user_id: str) -> dict:
        """Get token balance for a user."""
        balance = self._balances.get(user_id, 0)
        return {
            "success": True,
            "user_id": user_id,
            "balance": balance
        }

    async def get_transactions(self, user_id: str, limit: int = 50) -> dict:
        """Get transaction history for a user."""
        user_transactions = [
            t for t in self._transactions
            if t.get("user_id") == user_id or
               t.get("from_user") == user_id or
               t.get("to_user") == user_id
        ]

        # Sort by timestamp descending
        user_transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "success": True,
            "transactions": user_transactions[:limit]
        }

    async def get_leaderboard(self, limit: int = 10) -> dict:
        """Get top token holders."""
        sorted_balances = sorted(
            self._balances.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]

        leaderboard = [
            {"rank": i + 1, "user_id": user_id, "balance": balance}
            for i, (user_id, balance) in enumerate(sorted_balances)
        ]

        return {
            "success": True,
            "leaderboard": leaderboard
        }

    async def reward_interaction(self, user_id: str, interaction_type: str = "") -> dict:
        """Reward tokens for an interaction."""
        return await self.mint_tokens(
            user_id=user_id,
            token_type=TokenType.INTERACTION,
            reason=f"Interaction: {interaction_type}" if interaction_type else "Chat interaction"
        )

    async def reward_recognition(self, user_id: str, person_name: str = "") -> dict:
        """Reward tokens when a person is recognized."""
        return await self.mint_tokens(
            user_id=user_id,
            token_type=TokenType.RECOGNITION,
            reason=f"Recognized: {person_name}" if person_name else "Person recognition"
        )

    async def reward_coaching(self, user_id: str, session_type: str = "") -> dict:
        """Reward tokens for completing a coaching session."""
        return await self.mint_tokens(
            user_id=user_id,
            token_type=TokenType.COACHING,
            reason=f"Coaching session: {session_type}" if session_type else "Coaching session"
        )

    async def reward_daily_checkin(self, user_id: str) -> dict:
        """Reward tokens for daily check-in."""
        # Check if already checked in today
        today = datetime.now().date().isoformat()
        recent_checkins = [
            t for t in self._transactions
            if t.get("user_id") == user_id and
               t.get("token_type") == TokenType.DAILY_CHECKIN and
               t.get("timestamp", "").startswith(today)
        ]

        if recent_checkins:
            return {
                "success": False,
                "message": "Already checked in today",
                "balance": self._balances.get(user_id, 0)
            }

        return await self.mint_tokens(
            user_id=user_id,
            token_type=TokenType.DAILY_CHECKIN,
            reason=f"Daily check-in: {today}"
        )


# Singleton instance
token_service = TokenService()
