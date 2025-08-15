"""
User onboarding and tutorial service.
Provides guided tours, interactive tutorials, and help system.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db

class TutorialStep(BaseModel):
    """Tutorial step model."""
    id: str
    title: str
    description: str
    target_element: Optional[str] = None  # CSS selector
    position: str = "bottom"  # top, bottom, left, right
    content: str
    action_required: bool = False
    action_type: Optional[str] = None  # click, input, navigate
    validation: Optional[Dict[str, Any]] = None

class Tutorial(BaseModel):
    """Tutorial model."""
    id: str
    name: str
    description: str
    category: str
    difficulty: str  # beginner, intermediate, advanced
    estimated_time: int  # minutes
    prerequisites: List[str] = []
    steps: List[TutorialStep]
    completion_criteria: Dict[str, Any]

class OnboardingFlow(BaseModel):
    """Onboarding flow model."""
    id: str
    name: str
    description: str
    target_role: str
    tutorials: List[str]  # Tutorial IDs
    required: bool = True
    order: int = 0

class UserProgress(BaseModel):
    """User progress tracking model."""
    user_id: str
    tutorial_id: str
    current_step: int = 0
    completed: bool = False
    started_at: datetime
    completed_at: Optional[datetime] = None
    progress_data: Dict[str, Any] = {}

class HelpArticle(BaseModel):
    """Help article model."""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    difficulty: str
    last_updated: datetime
    author: str
    views: int = 0
    helpful_votes: int = 0
    total_votes: int = 0

class OnboardingService:
    """User onboarding and tutorial service."""
    
    def __init__(self, db: Session):
        self.db = db
        self._initialize_tutorials()
        self._initialize_onboarding_flows()
        self._initialize_help_articles()
    
    def _initialize_tutorials(self):
        """Initialize default tutorials."""
        
        self.tutorials = {
            "getting_started": Tutorial(
                id="getting_started",
                name="Getting Started with Real Estate Empire",
                description="Learn the basics of navigating and using the platform",
                category="basics",
                difficulty="beginner",
                estimated_time=10,
                steps=[
                    TutorialStep(
                        id="welcome",
                        title="Welcome to Real Estate Empire",
                        description="Let's take a quick tour of your new investment platform",
                        content="Welcome! This tutorial will guide you through the main features of Real Estate Empire. You'll learn how to analyze properties, manage leads, and track your portfolio.",
                        target_element=".dashboard-header"
                    ),
                    TutorialStep(
                        id="navigation",
                        title="Main Navigation",
                        description="Learn about the main navigation menu",
                        content="The main navigation menu on the left provides access to all major features. Click on each section to explore different areas of the platform.",
                        target_element=".main-nav",
                        action_required=True,
                        action_type="click"
                    ),
                    TutorialStep(
                        id="dashboard",
                        title="Dashboard Overview",
                        description="Understanding your dashboard",
                        content="Your dashboard shows key metrics, recent activity, and quick actions. The widgets can be customized to show the information most important to you.",
                        target_element=".dashboard-widgets"
                    ),
                    TutorialStep(
                        id="profile",
                        title="Profile Settings",
                        description="Set up your profile",
                        content="Click on your profile icon to access settings, security options, and preferences. It's important to complete your profile and enable security features.",
                        target_element=".profile-menu",
                        action_required=True,
                        action_type="click"
                    )
                ],
                completion_criteria={"steps_completed": 4}
            ),
            
            "property_analysis": Tutorial(
                id="property_analysis",
                name="Property Analysis Basics",
                description="Learn how to analyze investment properties",
                category="analysis",
                difficulty="beginner",
                estimated_time=15,
                prerequisites=["getting_started"],
                steps=[
                    TutorialStep(
                        id="add_property",
                        title="Adding a Property",
                        description="Learn how to add a new property for analysis",
                        content="Click the 'Add Property' button to start analyzing a new investment opportunity. You'll need the property address and basic details.",
                        target_element=".add-property-btn",
                        action_required=True,
                        action_type="click"
                    ),
                    TutorialStep(
                        id="property_details",
                        title="Property Details Form",
                        description="Fill in property information",
                        content="Enter the property address, type, and basic specifications. The more accurate information you provide, the better the analysis will be.",
                        target_element=".property-form",
                        action_required=True,
                        action_type="input",
                        validation={"required_fields": ["address", "property_type", "price"]}
                    ),
                    TutorialStep(
                        id="analysis_results",
                        title="Understanding Analysis Results",
                        description="Learn to interpret the analysis",
                        content="The analysis shows key metrics like cap rate, cash flow, and ROI. Each metric helps you evaluate the investment potential.",
                        target_element=".analysis-results"
                    ),
                    TutorialStep(
                        id="comparables",
                        title="Comparable Properties",
                        description="Review comparable sales and listings",
                        content="The comparables section shows similar properties to help validate your analysis. Look for recent sales and active listings in the area.",
                        target_element=".comparables-section"
                    )
                ],
                completion_criteria={"steps_completed": 4, "property_analyzed": True}
            ),
            
            "lead_management": Tutorial(
                id="lead_management",
                name="Lead Management System",
                description="Learn to manage and nurture leads effectively",
                category="leads",
                difficulty="intermediate",
                estimated_time=20,
                prerequisites=["getting_started"],
                steps=[
                    TutorialStep(
                        id="lead_sources",
                        title="Understanding Lead Sources",
                        description="Learn about different lead sources",
                        content="Leads come from various sources: MLS listings, public records, foreclosures, and manual imports. Each source provides different types of opportunities.",
                        target_element=".lead-sources"
                    ),
                    TutorialStep(
                        id="lead_scoring",
                        title="Lead Scoring System",
                        description="How leads are scored and prioritized",
                        content="Leads are automatically scored based on property characteristics, owner motivation, and market conditions. Higher scores indicate better opportunities.",
                        target_element=".lead-score"
                    ),
                    TutorialStep(
                        id="contact_lead",
                        title="Contacting Leads",
                        description="Learn to reach out to property owners",
                        content="Use the communication tools to contact property owners via email, SMS, or phone. Personalized messages get better response rates.",
                        target_element=".contact-buttons",
                        action_required=True,
                        action_type="click"
                    ),
                    TutorialStep(
                        id="track_responses",
                        title="Tracking Responses",
                        description="Monitor and manage lead responses",
                        content="All communications are tracked in the lead record. Update the lead status as you progress through negotiations.",
                        target_element=".communication-history"
                    )
                ],
                completion_criteria={"steps_completed": 4, "lead_contacted": True}
            ),
            
            "security_setup": Tutorial(
                id="security_setup",
                name="Security Setup",
                description="Set up security features to protect your account",
                category="security",
                difficulty="beginner",
                estimated_time=8,
                steps=[
                    TutorialStep(
                        id="password_strength",
                        title="Strong Password",
                        description="Ensure your password meets security requirements",
                        content="Your password should be at least 8 characters with uppercase, lowercase, numbers, and special characters. Avoid common words or personal information.",
                        target_element=".password-requirements"
                    ),
                    TutorialStep(
                        id="enable_mfa",
                        title="Enable Multi-Factor Authentication",
                        description="Add an extra layer of security",
                        content="MFA significantly improves account security. You'll need an authenticator app like Google Authenticator or Authy.",
                        target_element=".mfa-setup",
                        action_required=True,
                        action_type="click"
                    ),
                    TutorialStep(
                        id="backup_codes",
                        title="Save Backup Codes",
                        description="Store your backup codes safely",
                        content="Backup codes allow you to access your account if you lose your phone. Save them in a secure location like a password manager.",
                        target_element=".backup-codes"
                    ),
                    TutorialStep(
                        id="session_management",
                        title="Session Management",
                        description="Monitor your active sessions",
                        content="Regularly review your active sessions and revoke any you don't recognize. This helps detect unauthorized access.",
                        target_element=".active-sessions"
                    )
                ],
                completion_criteria={"steps_completed": 4, "mfa_enabled": True}
            )
        }
    
    def _initialize_onboarding_flows(self):
        """Initialize onboarding flows for different user roles."""
        
        self.onboarding_flows = {
            "agent": OnboardingFlow(
                id="agent_onboarding",
                name="Real Estate Agent Onboarding",
                description="Complete onboarding for real estate agents",
                target_role="agent",
                tutorials=["getting_started", "security_setup", "property_analysis", "lead_management"],
                required=True,
                order=1
            ),
            "investor": OnboardingFlow(
                id="investor_onboarding",
                name="Investor Onboarding",
                description="Complete onboarding for investors",
                target_role="investor",
                tutorials=["getting_started", "security_setup", "property_analysis"],
                required=True,
                order=1
            ),
            "manager": OnboardingFlow(
                id="manager_onboarding",
                name="Manager Onboarding",
                description="Complete onboarding for managers",
                target_role="manager",
                tutorials=["getting_started", "security_setup", "property_analysis", "lead_management"],
                required=True,
                order=1
            )
        }
    
    def _initialize_help_articles(self):
        """Initialize help articles."""
        
        self.help_articles = {
            "password_reset": HelpArticle(
                id="password_reset",
                title="How to Reset Your Password",
                content="""
                If you've forgotten your password, follow these steps:
                
                1. Go to the login page
                2. Click "Forgot Password?"
                3. Enter your email address
                4. Check your email for reset instructions
                5. Click the reset link and create a new password
                
                If you don't receive the email:
                - Check your spam folder
                - Verify you entered the correct email
                - Contact support if the issue persists
                """,
                category="account",
                tags=["password", "login", "reset"],
                difficulty="beginner",
                last_updated=datetime.utcnow(),
                author="Support Team"
            ),
            
            "mfa_setup": HelpArticle(
                id="mfa_setup",
                title="Setting Up Multi-Factor Authentication",
                content="""
                Multi-Factor Authentication (MFA) adds an extra layer of security:
                
                1. Go to Settings > Security
                2. Click "Enable MFA"
                3. Install an authenticator app (Google Authenticator, Authy)
                4. Scan the QR code with your app
                5. Enter the verification code
                6. Save your backup codes securely
                
                Recommended authenticator apps:
                - Google Authenticator (iOS/Android)
                - Authy (iOS/Android/Desktop)
                - Microsoft Authenticator (iOS/Android)
                """,
                category="security",
                tags=["mfa", "security", "authentication"],
                difficulty="beginner",
                last_updated=datetime.utcnow(),
                author="Security Team"
            ),
            
            "property_analysis_guide": HelpArticle(
                id="property_analysis_guide",
                title="Understanding Property Analysis Metrics",
                content="""
                Key metrics in property analysis:
                
                **Cap Rate**: Annual return on investment
                - Formula: Net Operating Income / Property Value
                - Good cap rates vary by market (typically 4-10%)
                
                **Cash Flow**: Monthly income after expenses
                - Positive cash flow means profit each month
                - Negative cash flow requires monthly contributions
                
                **Cash-on-Cash Return**: Return on actual cash invested
                - Formula: Annual Cash Flow / Cash Invested
                - Accounts for financing and leverage
                
                **ROI**: Total return including appreciation
                - Includes cash flow and property value growth
                - Annualized percentage return
                """,
                category="analysis",
                tags=["analysis", "metrics", "roi", "cash-flow"],
                difficulty="intermediate",
                last_updated=datetime.utcnow(),
                author="Analysis Team"
            )
        }
    
    def get_user_onboarding_flow(self, user_role: str) -> Optional[OnboardingFlow]:
        """Get onboarding flow for user role."""
        return self.onboarding_flows.get(user_role)
    
    def get_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """Get tutorial by ID."""
        return self.tutorials.get(tutorial_id)
    
    def start_tutorial(self, user_id: str, tutorial_id: str) -> UserProgress:
        """Start a tutorial for a user."""
        
        tutorial = self.get_tutorial(tutorial_id)
        if not tutorial:
            raise ValueError(f"Tutorial {tutorial_id} not found")
        
        # Check prerequisites
        for prereq in tutorial.prerequisites:
            if not self.is_tutorial_completed(user_id, prereq):
                raise ValueError(f"Prerequisite tutorial {prereq} not completed")
        
        progress = UserProgress(
            user_id=user_id,
            tutorial_id=tutorial_id,
            current_step=0,
            started_at=datetime.utcnow(),
            progress_data={}
        )
        
        # Store progress (in real implementation, this would be in database)
        self._store_progress(progress)
        
        return progress
    
    def get_user_progress(self, user_id: str, tutorial_id: str) -> Optional[UserProgress]:
        """Get user's progress for a tutorial."""
        # In real implementation, this would query the database
        return self._get_stored_progress(user_id, tutorial_id)
    
    def update_progress(self, user_id: str, tutorial_id: str, step_data: Dict[str, Any]) -> UserProgress:
        """Update user's tutorial progress."""
        
        progress = self.get_user_progress(user_id, tutorial_id)
        if not progress:
            raise ValueError("Tutorial not started")
        
        tutorial = self.get_tutorial(tutorial_id)
        current_step = tutorial.steps[progress.current_step]
        
        # Validate step completion if required
        if current_step.action_required and current_step.validation:
            if not self._validate_step_completion(step_data, current_step.validation):
                raise ValueError("Step validation failed")
        
        # Update progress
        progress.progress_data[f"step_{progress.current_step}"] = step_data
        progress.current_step += 1
        
        # Check if tutorial is completed
        if progress.current_step >= len(tutorial.steps):
            if self._validate_completion(progress, tutorial.completion_criteria):
                progress.completed = True
                progress.completed_at = datetime.utcnow()
        
        self._store_progress(progress)
        return progress
    
    def is_tutorial_completed(self, user_id: str, tutorial_id: str) -> bool:
        """Check if user has completed a tutorial."""
        progress = self.get_user_progress(user_id, tutorial_id)
        return progress and progress.completed
    
    def get_user_onboarding_status(self, user_id: str, user_role: str) -> Dict[str, Any]:
        """Get user's onboarding completion status."""
        
        flow = self.get_user_onboarding_flow(user_role)
        if not flow:
            return {"completed": True, "progress": 100}
        
        total_tutorials = len(flow.tutorials)
        completed_tutorials = 0
        tutorial_progress = []
        
        for tutorial_id in flow.tutorials:
            progress = self.get_user_progress(user_id, tutorial_id)
            tutorial = self.get_tutorial(tutorial_id)
            
            if progress and progress.completed:
                completed_tutorials += 1
                status = "completed"
                progress_percent = 100
            elif progress:
                status = "in_progress"
                progress_percent = int((progress.current_step / len(tutorial.steps)) * 100)
            else:
                status = "not_started"
                progress_percent = 0
            
            tutorial_progress.append({
                "tutorial_id": tutorial_id,
                "name": tutorial.name,
                "status": status,
                "progress": progress_percent,
                "estimated_time": tutorial.estimated_time
            })
        
        overall_progress = int((completed_tutorials / total_tutorials) * 100)
        
        return {
            "completed": completed_tutorials == total_tutorials,
            "progress": overall_progress,
            "tutorials": tutorial_progress,
            "flow_name": flow.name
        }
    
    def search_help_articles(self, query: str, category: Optional[str] = None) -> List[HelpArticle]:
        """Search help articles."""
        
        results = []
        query_lower = query.lower()
        
        for article in self.help_articles.values():
            # Check category filter
            if category and article.category != category:
                continue
            
            # Search in title, content, and tags
            if (query_lower in article.title.lower() or 
                query_lower in article.content.lower() or 
                any(query_lower in tag.lower() for tag in article.tags)):
                results.append(article)
        
        # Sort by relevance (simple implementation)
        results.sort(key=lambda x: (
            query_lower in x.title.lower(),
            len([tag for tag in x.tags if query_lower in tag.lower()]),
            x.helpful_votes
        ), reverse=True)
        
        return results
    
    def get_help_article(self, article_id: str) -> Optional[HelpArticle]:
        """Get help article by ID."""
        article = self.help_articles.get(article_id)
        if article:
            # Increment view count
            article.views += 1
        return article
    
    def rate_help_article(self, article_id: str, helpful: bool) -> bool:
        """Rate a help article as helpful or not."""
        
        article = self.help_articles.get(article_id)
        if not article:
            return False
        
        article.total_votes += 1
        if helpful:
            article.helpful_votes += 1
        
        return True
    
    def get_contextual_help(self, page: str, user_role: str) -> List[Dict[str, Any]]:
        """Get contextual help for a specific page."""
        
        help_suggestions = {
            "dashboard": [
                {"type": "tutorial", "id": "getting_started", "title": "Getting Started Tour"},
                {"type": "article", "id": "dashboard_overview", "title": "Understanding Your Dashboard"}
            ],
            "properties": [
                {"type": "tutorial", "id": "property_analysis", "title": "Property Analysis Tutorial"},
                {"type": "article", "id": "property_analysis_guide", "title": "Analysis Metrics Guide"}
            ],
            "leads": [
                {"type": "tutorial", "id": "lead_management", "title": "Lead Management Tutorial"},
                {"type": "article", "id": "lead_scoring", "title": "Understanding Lead Scores"}
            ],
            "security": [
                {"type": "tutorial", "id": "security_setup", "title": "Security Setup Tutorial"},
                {"type": "article", "id": "mfa_setup", "title": "Multi-Factor Authentication"}
            ]
        }
        
        return help_suggestions.get(page, [])
    
    def _validate_step_completion(self, step_data: Dict[str, Any], validation: Dict[str, Any]) -> bool:
        """Validate step completion criteria."""
        
        if "required_fields" in validation:
            for field in validation["required_fields"]:
                if field not in step_data or not step_data[field]:
                    return False
        
        if "min_value" in validation:
            value = step_data.get("value", 0)
            if value < validation["min_value"]:
                return False
        
        return True
    
    def _validate_completion(self, progress: UserProgress, criteria: Dict[str, Any]) -> bool:
        """Validate tutorial completion criteria."""
        
        if "steps_completed" in criteria:
            if progress.current_step < criteria["steps_completed"]:
                return False
        
        if "property_analyzed" in criteria:
            if not progress.progress_data.get("property_analyzed"):
                return False
        
        if "lead_contacted" in criteria:
            if not progress.progress_data.get("lead_contacted"):
                return False
        
        if "mfa_enabled" in criteria:
            if not progress.progress_data.get("mfa_enabled"):
                return False
        
        return True
    
    def _store_progress(self, progress: UserProgress):
        """Store user progress (placeholder for database storage)."""
        # In real implementation, this would store in database
        pass
    
    def _get_stored_progress(self, user_id: str, tutorial_id: str) -> Optional[UserProgress]:
        """Get stored user progress (placeholder for database retrieval)."""
        # In real implementation, this would query database
        return None