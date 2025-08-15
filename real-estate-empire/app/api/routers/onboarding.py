"""
Onboarding and tutorial API router.
Provides endpoints for user onboarding, tutorials, and help system.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.services.onboarding_service import OnboardingService
from app.services.onboarding_service import (
    Tutorial, OnboardingFlow, UserProgress, HelpArticle, TutorialStep
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.get("/status", response_model=Dict[str, Any])
async def get_onboarding_status(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's onboarding completion status."""
    
    service = OnboardingService(db)
    status = service.get_user_onboarding_status(current_user.user_id, current_user.role)
    
    return status

@router.get("/flow", response_model=Optional[OnboardingFlow])
async def get_onboarding_flow(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get onboarding flow for user's role."""
    
    service = OnboardingService(db)
    flow = service.get_user_onboarding_flow(current_user.role)
    
    return flow

@router.get("/tutorials", response_model=List[Tutorial])
async def list_tutorials(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available tutorials."""
    
    service = OnboardingService(db)
    tutorials = list(service.tutorials.values())
    
    # Apply filters
    if category:
        tutorials = [t for t in tutorials if t.category == category]
    
    if difficulty:
        tutorials = [t for t in tutorials if t.difficulty == difficulty]
    
    return tutorials

@router.get("/tutorials/{tutorial_id}", response_model=Tutorial)
async def get_tutorial(
    tutorial_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific tutorial details."""
    
    service = OnboardingService(db)
    tutorial = service.get_tutorial(tutorial_id)
    
    if not tutorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutorial not found"
        )
    
    return tutorial

@router.post("/tutorials/{tutorial_id}/start", response_model=UserProgress)
async def start_tutorial(
    tutorial_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a tutorial."""
    
    service = OnboardingService(db)
    
    try:
        progress = service.start_tutorial(current_user.user_id, tutorial_id)
        return progress
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tutorials/{tutorial_id}/progress", response_model=Optional[UserProgress])
async def get_tutorial_progress(
    tutorial_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's progress for a tutorial."""
    
    service = OnboardingService(db)
    progress = service.get_user_progress(current_user.user_id, tutorial_id)
    
    return progress

@router.post("/tutorials/{tutorial_id}/progress", response_model=UserProgress)
async def update_tutorial_progress(
    tutorial_id: str,
    step_data: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update tutorial progress."""
    
    service = OnboardingService(db)
    
    try:
        progress = service.update_progress(current_user.user_id, tutorial_id, step_data)
        return progress
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/tutorials/{tutorial_id}/next-step", response_model=Optional[TutorialStep])
async def get_next_tutorial_step(
    tutorial_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the next step in a tutorial."""
    
    service = OnboardingService(db)
    tutorial = service.get_tutorial(tutorial_id)
    progress = service.get_user_progress(current_user.user_id, tutorial_id)
    
    if not tutorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutorial not found"
        )
    
    if not progress:
        # Return first step if tutorial not started
        return tutorial.steps[0] if tutorial.steps else None
    
    if progress.completed:
        return None  # Tutorial completed
    
    if progress.current_step < len(tutorial.steps):
        return tutorial.steps[progress.current_step]
    
    return None

@router.get("/help/search", response_model=List[HelpArticle])
async def search_help_articles(
    q: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search help articles."""
    
    service = OnboardingService(db)
    results = service.search_help_articles(q, category)
    
    return results[:limit]

@router.get("/help/articles/{article_id}", response_model=HelpArticle)
async def get_help_article(
    article_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific help article."""
    
    service = OnboardingService(db)
    article = service.get_help_article(article_id)
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    
    return article

@router.post("/help/articles/{article_id}/rate")
async def rate_help_article(
    article_id: str,
    helpful: bool,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate a help article as helpful or not."""
    
    service = OnboardingService(db)
    success = service.rate_help_article(article_id, helpful)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help article not found"
        )
    
    return {"message": "Rating recorded successfully"}

@router.get("/help/contextual", response_model=List[Dict[str, Any]])
async def get_contextual_help(
    page: str = Query(..., description="Current page/section"),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get contextual help for current page."""
    
    service = OnboardingService(db)
    suggestions = service.get_contextual_help(page, current_user.role)
    
    return suggestions

@router.get("/help/categories", response_model=List[str])
async def get_help_categories(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available help categories."""
    
    service = OnboardingService(db)
    categories = list(set(article.category for article in service.help_articles.values()))
    
    return sorted(categories)

@router.get("/tutorials/categories", response_model=List[str])
async def get_tutorial_categories(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available tutorial categories."""
    
    service = OnboardingService(db)
    categories = list(set(tutorial.category for tutorial in service.tutorials.values()))
    
    return sorted(categories)

@router.post("/tutorials/{tutorial_id}/reset", response_model=Dict[str, str])
async def reset_tutorial_progress(
    tutorial_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset tutorial progress to start over."""
    
    service = OnboardingService(db)
    tutorial = service.get_tutorial(tutorial_id)
    
    if not tutorial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutorial not found"
        )
    
    # Reset progress by starting tutorial again
    try:
        service.start_tutorial(current_user.user_id, tutorial_id)
        return {"message": "Tutorial progress reset successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/progress/summary", response_model=Dict[str, Any])
async def get_progress_summary(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall progress summary for user."""
    
    service = OnboardingService(db)
    
    # Get onboarding status
    onboarding_status = service.get_user_onboarding_status(current_user.user_id, current_user.role)
    
    # Get individual tutorial progress
    tutorial_progress = []
    for tutorial_id, tutorial in service.tutorials.items():
        progress = service.get_user_progress(current_user.user_id, tutorial_id)
        
        if progress:
            tutorial_progress.append({
                "tutorial_id": tutorial_id,
                "name": tutorial.name,
                "category": tutorial.category,
                "completed": progress.completed,
                "current_step": progress.current_step,
                "total_steps": len(tutorial.steps),
                "started_at": progress.started_at,
                "completed_at": progress.completed_at
            })
    
    return {
        "onboarding": onboarding_status,
        "tutorials": tutorial_progress,
        "total_tutorials_available": len(service.tutorials),
        "total_tutorials_completed": len([t for t in tutorial_progress if t["completed"]])
    }

@router.get("/recommendations", response_model=List[Dict[str, Any]])
async def get_learning_recommendations(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized learning recommendations."""
    
    service = OnboardingService(db)
    recommendations = []
    
    # Check onboarding completion
    onboarding_status = service.get_user_onboarding_status(current_user.user_id, current_user.role)
    
    if not onboarding_status["completed"]:
        # Recommend next onboarding tutorial
        for tutorial_info in onboarding_status["tutorials"]:
            if tutorial_info["status"] == "not_started":
                tutorial = service.get_tutorial(tutorial_info["tutorial_id"])
                recommendations.append({
                    "type": "onboarding",
                    "priority": "high",
                    "tutorial_id": tutorial_info["tutorial_id"],
                    "title": tutorial.name,
                    "description": tutorial.description,
                    "estimated_time": tutorial.estimated_time,
                    "reason": "Complete your onboarding"
                })
                break
    
    # Recommend advanced tutorials based on role
    role_recommendations = {
        "agent": ["advanced_analysis", "marketing_automation"],
        "investor": ["portfolio_optimization", "tax_strategies"],
        "manager": ["team_management", "reporting_advanced"]
    }
    
    for tutorial_id in role_recommendations.get(current_user.role, []):
        if tutorial_id in service.tutorials:
            tutorial = service.tutorials[tutorial_id]
            if not service.is_tutorial_completed(current_user.user_id, tutorial_id):
                recommendations.append({
                    "type": "advanced",
                    "priority": "medium",
                    "tutorial_id": tutorial_id,
                    "title": tutorial.name,
                    "description": tutorial.description,
                    "estimated_time": tutorial.estimated_time,
                    "reason": f"Recommended for {current_user.role}s"
                })
    
    return recommendations[:5]  # Limit to top 5 recommendations