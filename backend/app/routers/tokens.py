from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from ..services.token_service import token_service

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


class MintRequest(BaseModel):
    user_id: str
    token_type: str
    amount: Optional[int] = None
    reason: Optional[str] = ""


class TransferRequest(BaseModel):
    from_user: str
    to_user: str
    amount: int
    reason: Optional[str] = ""


class CheckinRequest(BaseModel):
    user_id: str


@router.get("/balance/{user_id}")
async def get_balance(user_id: str):
    """Get token balance for a user."""
    return await token_service.get_balance(user_id)


@router.post("/mint")
async def mint_tokens(request: MintRequest):
    """Mint new tokens for a user."""
    return await token_service.mint_tokens(
        user_id=request.user_id,
        token_type=request.token_type,
        amount=request.amount,
        reason=request.reason
    )


@router.post("/transfer")
async def transfer_tokens(request: TransferRequest):
    """Transfer tokens between users."""
    return await token_service.transfer_tokens(
        from_user=request.from_user,
        to_user=request.to_user,
        amount=request.amount,
        reason=request.reason
    )


@router.get("/transactions/{user_id}")
async def get_transactions(user_id: str, limit: int = 50):
    """Get transaction history for a user."""
    return await token_service.get_transactions(user_id, limit)


@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """Get top token holders."""
    return await token_service.get_leaderboard(limit)


@router.post("/checkin")
async def daily_checkin(request: CheckinRequest):
    """Daily check-in to earn tokens."""
    return await token_service.reward_daily_checkin(request.user_id)


@router.post("/reward/coaching")
async def reward_coaching(user_id: str, session_type: str = ""):
    """Reward tokens for completing a coaching session."""
    return await token_service.reward_coaching(user_id, session_type)


@router.post("/reward/recognition")
async def reward_recognition(user_id: str, person_name: str = ""):
    """Reward tokens when a person is recognized."""
    return await token_service.reward_recognition(user_id, person_name)
