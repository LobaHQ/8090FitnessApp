from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Dict, Any

from ...schemas.profile import UserProfileUpdateRequest, UserProfileResponse
from ...models import User, UserProfile
from ...database.session import get_async_session
from ...core.security import get_current_user

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.put("", response_model=UserProfileResponse)
async def complete_onboarding(
    request: UserProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    cognito_id = current_user['sub']
    
    stmt = select(User).where(User.cognito_id == cognito_id).options(
        selectinload(User.profile)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.profile:
        profile = UserProfile(user_id=user.id)
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        user.profile = profile
    
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user.profile, field, value)
    
    user.profile.has_completed_onboarding = True
    
    await session.commit()
    await session.refresh(user.profile)
    
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        fitness_level=user.profile.fitness_level,
        goals=user.profile.goals,
        equipment=user.profile.equipment,
        has_completed_onboarding=user.profile.has_completed_onboarding,
        age=user.profile.age,
        height_cm=user.profile.height_cm,
        weight_kg=user.profile.weight_kg,
        preferred_workout_time=user.profile.preferred_workout_time,
        injury_notes=user.profile.injury_notes,
        created_at=user.created_at,
        updated_at=user.updated_at
    )