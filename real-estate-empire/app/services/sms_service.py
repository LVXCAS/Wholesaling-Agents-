"""
SMS service integration for sending SMS messages, managing templates, and handling compliance.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import re
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
from jinja2 import Template

from ..models.communication import (
    SMSMessage, SMSTemplate, MessageStatus, MessagePriority,
    CommunicationAnalytics, CommunicationChannel
)


logger = logging.getLogger(__name__)


class SMSServiceConfig:
    """SMS service configuration."""
    
    def __init__(
        self,
        twilio_account_sid: str = "",
        twilio_auth_token: str = "",
        default_from_phone: str = "",
        webhook_url: str = "",
        enable_delivery_receipts: bool = True
    ):
        self.twilio_account_sid = twilio_account_sid
        self.twilio_auth_token = twilio_auth_token
        self.default_from_phone = default_from_phone
        self.webhook_url = webhook_url
        self.enable_delivery_receipts = enable_delivery_receipts


class SMSTemplateEngine:
    """SMS template engine using Jinja2."""
    
    def render_template(self, template: SMSTemplate, variables: Dict[str, Any]) -> str:
        """Render SMS template with variables."""
        try:
            message_template = Template(template.message)
            rendered_message = message_template.render(**variables)
            return rendered_message
        except Exception as e:
            logger.error(f"Error rendering SMS template {template.id}: {e}")
            raise
    
    def validate_template(self, template: SMSTemplate) -> List[str]:
        """Validate SMS template for syntax errors."""
        errors = []
        
        try:
            Template(template.message)
        except Exception as e:
            errors.append(f"Message template error: {e}")
        
        # Check message length (SMS limit is 160 characters for single message)
        if len(template.message) > 1600:  # Allow for 10 concatenated messages
            errors.append("Message template is too long (max 1600 characters)")
        
        return errors


class SMSComplianceManager:
    """SMS compliance management for opt-out handling and regulations."""
    
    def __init__(self):
        self.opt_out_keywords = [
            "STOP", "STOPALL", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"
        ]
        self.opt_in_keywords = [
            "START", "YES", "UNSTOP"
        ]
        self.opted_out_numbers: set = set()
    
    def is_opted_out(self, phone_number: str) -> bool:
        """Check if a phone number has opted out."""
        normalized_phone = self.normalize_phone_number(phone_number)
        return normalized_phone in self.opted_out_numbers
    
    def opt_out_number(self, phone_number: str):
        """Opt out a phone number."""
        normalized_phone = self.normalize_phone_number(phone_number)
        self.opted_out_numbers.add(normalized_phone)
        logger.info(f"Phone number opted out: {normalized_phone}")
    
    def opt_in_number(self, phone_number: str):
        """Opt in a phone number (remove from opt-out list)."""
        normalized_phone = self.normalize_phone_number(phone_number)
        self.opted_out_numbers.discard(normalized_phone)
        logger.info(f"Phone number opted in: {normalized_phone}")
    
    def process_incoming_message(self, phone_number: str, message: str) -> Optional[str]:
        """Process incoming SMS message for opt-out/opt-in keywords."""
        message_upper = message.strip().upper()
        
        if message_upper in self.opt_out_keywords:
            self.opt_out_number(phone_number)
            return "You have been unsubscribed from SMS messages. Reply START to opt back in."
        
        if message_upper in self.opt_in_keywords and self.is_opted_out(phone_number):
            self.opt_in_number(phone_number)
            return "You have been subscribed to SMS messages. Reply STOP to opt out."
        
        return None
    
    def normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number format."""
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_number)
        
        # Add country code if missing (assume US)
        if len(digits_only) == 10:
            digits_only = "1" + digits_only
        
        return digits_only
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format."""
        normalized = self.normalize_phone_number(phone_number)
        return len(normalized) >= 10 and len(normalized) <= 15


class SMSService:
    """SMS service for sending messages and managing templates."""
    
    def __init__(self, config: SMSServiceConfig):
        self.config = config
        self.template_engine = SMSTemplateEngine()
        self.compliance_manager = SMSComplianceManager()
        self.templates: Dict[uuid.UUID, SMSTemplate] = {}
        self.sent_messages: Dict[uuid.UUID, SMSMessage] = {}
        
        # Initialize Twilio client
        if config.twilio_account_sid and config.twilio_auth_token:
            self.twilio_client = Client(config.twilio_account_sid, config.twilio_auth_token)
        else:
            self.twilio_client = None
            logger.warning("Twilio credentials not provided, SMS sending will be mocked")
    
    async def send_sms(self, message: SMSMessage) -> bool:
        """Send an SMS message."""
        try:
            # Validate phone number
            if not self.compliance_manager.validate_phone_number(message.to_phone):
                logger.error(f"Invalid phone number: {message.to_phone}")
                message.status = MessageStatus.FAILED
                return False
            
            # Check opt-out status
            if self.compliance_manager.is_opted_out(message.to_phone):
                logger.warning(f"Phone number has opted out: {message.to_phone}")
                message.status = MessageStatus.FAILED
                return False
            
            # Set defaults if not provided
            if not message.from_phone:
                message.from_phone = self.config.default_from_phone
            
            # Send via Twilio
            if self.twilio_client:
                twilio_message = self.twilio_client.messages.create(
                    body=message.message,
                    from_=message.from_phone,
                    to=message.to_phone,
                    status_callback=self.config.webhook_url if self.config.enable_delivery_receipts else None
                )
                
                # Store Twilio message SID for tracking
                if not message.metadata:
                    message.metadata = {}
                message.metadata["twilio_sid"] = twilio_message.sid
            else:
                # Mock sending for testing
                logger.info(f"Mock SMS sent to {message.to_phone}: {message.message}")
            
            # Update message status
            message.status = MessageStatus.SENT
            message.sent_at = datetime.now()
            
            if message.id:
                self.sent_messages[message.id] = message
            
            logger.info(f"SMS sent successfully to {message.to_phone}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {message.to_phone}: {e}")
            message.status = MessageStatus.FAILED
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS to {message.to_phone}: {e}")
            message.status = MessageStatus.FAILED
            return False
    
    async def send_template_sms(
        self,
        template_id: uuid.UUID,
        to_phone: str,
        variables: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        scheduled_at: Optional[datetime] = None
    ) -> SMSMessage:
        """Send an SMS using a template."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Render template
        rendered_message = self.template_engine.render_template(template, variables)
        
        # Create message
        message = SMSMessage(
            id=uuid.uuid4(),
            to_phone=to_phone,
            message=rendered_message,
            template_id=template_id,
            template_variables=variables,
            priority=priority,
            scheduled_at=scheduled_at,
            created_at=datetime.now()
        )
        
        # Send immediately or schedule
        if scheduled_at and scheduled_at > datetime.now():
            message.status = MessageStatus.QUEUED
            # In a real implementation, you'd add this to a job queue
            logger.info(f"SMS scheduled for {scheduled_at}")
        else:
            await self.send_sms(message)
        
        return message
    
    def create_template(self, template: SMSTemplate) -> SMSTemplate:
        """Create a new SMS template."""
        if not template.id:
            template.id = uuid.uuid4()
        
        template.created_at = datetime.now()
        template.updated_at = datetime.now()
        
        # Validate template
        errors = self.template_engine.validate_template(template)
        if errors:
            raise ValueError(f"Template validation errors: {errors}")
        
        self.templates[template.id] = template
        logger.info(f"SMS template created: {template.name}")
        return template
    
    def update_template(self, template_id: uuid.UUID, updates: Dict[str, Any]) -> SMSTemplate:
        """Update an existing SMS template."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.now()
        
        # Validate updated template
        errors = self.template_engine.validate_template(template)
        if errors:
            raise ValueError(f"Template validation errors: {errors}")
        
        self.templates[template_id] = template
        logger.info(f"SMS template updated: {template.name}")
        return template
    
    def get_template(self, template_id: uuid.UUID) -> Optional[SMSTemplate]:
        """Get an SMS template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[SMSTemplate]:
        """List all SMS templates, optionally filtered by category."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def delete_template(self, template_id: uuid.UUID) -> bool:
        """Delete an SMS template."""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"SMS template deleted: {template_id}")
            return True
        return False
    
    def handle_delivery_status(self, message_id: uuid.UUID, status: str):
        """Handle SMS delivery status webhook from Twilio."""
        if message_id in self.sent_messages:
            message = self.sent_messages[message_id]
            
            if status == "delivered":
                message.status = MessageStatus.DELIVERED
                message.delivered_at = datetime.now()
            elif status == "failed" or status == "undelivered":
                message.status = MessageStatus.FAILED
            
            logger.info(f"SMS {message_id} status updated to {status}")
    
    def handle_incoming_message(self, from_phone: str, message_body: str) -> Optional[str]:
        """Handle incoming SMS message."""
        logger.info(f"Incoming SMS from {from_phone}: {message_body}")
        
        # Process for compliance (opt-out/opt-in)
        compliance_response = self.compliance_manager.process_incoming_message(from_phone, message_body)
        
        if compliance_response:
            # Send automatic compliance response
            response_message = SMSMessage(
                id=uuid.uuid4(),
                to_phone=from_phone,
                message=compliance_response,
                created_at=datetime.now()
            )
            asyncio.create_task(self.send_sms(response_message))
            return compliance_response
        
        return None
    
    def get_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        category: Optional[str] = None
    ) -> CommunicationAnalytics:
        """Get SMS analytics for a date range."""
        messages = [
            msg for msg in self.sent_messages.values()
            if msg.sent_at and start_date <= msg.sent_at <= end_date
        ]
        
        if category:
            template_ids = [
                t.id for t in self.templates.values()
                if t.category == category
            ]
            messages = [
                msg for msg in messages
                if msg.template_id in template_ids
            ]
        
        total_sent = len(messages)
        total_delivered = len([m for m in messages if m.status == MessageStatus.DELIVERED])
        total_failed = len([m for m in messages if m.status == MessageStatus.FAILED])
        
        return CommunicationAnalytics(
            channel=CommunicationChannel.SMS,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_opened=0,  # SMS doesn't have open tracking
            total_clicked=0,  # SMS doesn't have click tracking
            total_replied=0,  # Would need to track incoming messages
            total_bounced=total_failed,
            delivery_rate=total_delivered / total_sent if total_sent > 0 else 0.0,
            open_rate=0.0,  # Not applicable for SMS
            click_rate=0.0,  # Not applicable for SMS
            reply_rate=0.0,  # Would need to track incoming messages
            bounce_rate=total_failed / total_sent if total_sent > 0 else 0.0,
            period_start=start_date,
            period_end=end_date
        )
    
    async def send_bulk_sms(
        self,
        template_id: uuid.UUID,
        recipients: List[Dict[str, Any]],
        batch_size: int = 10,
        delay_seconds: float = 1.0
    ) -> List[SMSMessage]:
        """Send bulk SMS messages with rate limiting."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        sent_messages = []
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            batch_tasks = []
            
            for recipient in batch:
                message = await self.send_template_sms(
                    template_id=template_id,
                    to_phone=recipient["phone"],
                    variables=recipient.get("variables", {}),
                    priority=recipient.get("priority", MessagePriority.NORMAL)
                )
                batch_tasks.append(message)
            
            sent_messages.extend(batch_tasks)
            
            # Delay between batches to avoid rate limiting
            if i + batch_size < len(recipients):
                await asyncio.sleep(delay_seconds)
        
        logger.info(f"Bulk SMS sent to {len(recipients)} recipients")
        return sent_messages
    
    def get_opt_out_count(self) -> int:
        """Get the number of opted-out phone numbers."""
        return len(self.compliance_manager.opted_out_numbers)
    
    def export_opt_outs(self) -> List[str]:
        """Export list of opted-out phone numbers."""
        return list(self.compliance_manager.opted_out_numbers)
    
    def import_opt_outs(self, phone_numbers: List[str]):
        """Import list of opted-out phone numbers."""
        for phone in phone_numbers:
            self.compliance_manager.opt_out_number(phone)
        logger.info(f"Imported {len(phone_numbers)} opt-out numbers")