"""
Tests for Negotiator Agent Tools - Communication and Analysis Tools
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.agents.negotiator_tools import (
    EmailCommunicationTool, SMSCommunicationTool, VoiceCommunicationTool,
    ResponseAnalysisTool, NegotiationStrategyTool, CommunicationChannel,
    MessageStatus, CommunicationResult
)


class TestEmailCommunicationTool:
    """Test cases for EmailCommunicationTool"""
    
    @pytest.fixture
    def email_tool(self):
        """Create email communication tool for testing"""
        return EmailCommunicationTool()
    
    def test_tool_initialization(self, email_tool):
        """Test email tool initialization"""
        assert email_tool.metadata.name == "email_communication"
        assert email_tool.metadata.category.value == "communication"
        assert email_tool.metadata.access_level.value == "restricted"
        assert "negotiator" in email_tool.metadata.allowed_agents
        assert email_tool.smtp_server == "smtp.gmail.com"
        assert email_tool.smtp_port == 587
    
    @pytest.mark.asyncio
    async def test_execute_email_success(self, email_tool):
        """Test successful email execution"""
        result = await email_tool.execute(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test email content",
            tracking_enabled=True
        )
        
        assert "message_id" in result
        assert result["status"] == "sent"
        assert result["recipient"] == "test@example.com"
        assert result["tracking_enabled"] is True
        assert "sent_at" in result
    
    @pytest.mark.asyncio
    async def test_execute_email_missing_fields(self, email_tool):
        """Test email execution with missing required fields"""
        result = await email_tool.execute(
            recipient="test@example.com"
            # Missing subject and content
        )
        
        assert result["success"] is False
        assert "Missing required fields" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_email_with_html(self, email_tool):
        """Test email execution with HTML content"""
        result = await email_tool.execute(
            recipient="test@example.com",
            subject="Test Subject",
            content="Plain text content",
            html_content="<h1>HTML Content</h1>",
            reply_to="reply@example.com"
        )
        
        assert result is not None