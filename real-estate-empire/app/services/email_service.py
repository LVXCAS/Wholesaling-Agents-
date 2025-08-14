"""
Email service integration for sending emails, managing templates, and tracking analytics.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
from jinja2 import Template, Environment, BaseLoader
import re

from ..models.communication import (
    EmailMessage, EmailTemplate, MessageStatus, MessagePriority,
    CommunicationAnalytics, CommunicationChannel
)


logger = logging.getLogger(__name__)


class EmailServiceConfig:
    """Email service configuration."""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: str = "",
        smtp_password: str = "",
        use_tls: bool = True,
        default_from_email: str = "",
        default_from_name: str = "Real Estate Empire",
        bounce_email: str = "",
        reply_to_email: str = ""
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.default_from_email = default_from_email
        self.default_from_name = default_from_name
        self.bounce_email = bounce_email
        self.reply_to_email = reply_to_email


class EmailTemplateEngine:
    """Email template engine using Jinja2."""
    
    def __init__(self):
        self.env = Environment(loader=BaseLoader())
    
    def render_template(self, template: EmailTemplate, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render email template with variables."""
        try:
            subject_template = Template(template.subject)
            html_template = Template(template.body_html)
            text_template = Template(template.body_text)
            
            rendered_subject = subject_template.render(**variables)
            rendered_html = html_template.render(**variables)
            rendered_text = text_template.render(**variables)
            
            return {
                "subject": rendered_subject,
                "body_html": rendered_html,
                "body_text": rendered_text
            }
        except Exception as e:
            logger.error(f"Error rendering email template {template.id}: {e}")
            raise
    
    def validate_template(self, template: EmailTemplate) -> List[str]:
        """Validate email template for syntax errors."""
        errors = []
        
        try:
            Template(template.subject)
        except Exception as e:
            errors.append(f"Subject template error: {e}")
        
        try:
            Template(template.body_html)
        except Exception as e:
            errors.append(f"HTML body template error: {e}")
        
        try:
            Template(template.body_text)
        except Exception as e:
            errors.append(f"Text body template error: {e}")
        
        return errors


class EmailTracker:
    """Email tracking and analytics."""
    
    def __init__(self):
        self.tracking_data: Dict[str, Dict] = {}
    
    def generate_tracking_pixel(self, message_id: uuid.UUID) -> str:
        """Generate tracking pixel HTML for email opens."""
        tracking_url = f"https://your-domain.com/track/open/{message_id}"
        return f'<img src="{tracking_url}" width="1" height="1" style="display:none;" />'
    
    def generate_tracking_links(self, content: str, message_id: uuid.UUID) -> str:
        """Add tracking to links in email content."""
        def replace_link(match):
            original_url = match.group(1)
            tracking_url = f"https://your-domain.com/track/click/{message_id}?url={original_url}"
            return f'href="{tracking_url}"'
        
        # Replace href attributes with tracking URLs
        tracked_content = re.sub(r'href="([^"]*)"', replace_link, content)
        return tracked_content
    
    def track_open(self, message_id: uuid.UUID):
        """Track email open event."""
        if message_id not in self.tracking_data:
            self.tracking_data[message_id] = {}
        
        self.tracking_data[message_id]["opened_at"] = datetime.now()
        logger.info(f"Email {message_id} opened")
    
    def track_click(self, message_id: uuid.UUID, url: str):
        """Track email click event."""
        if message_id not in self.tracking_data:
            self.tracking_data[message_id] = {}
        
        if "clicks" not in self.tracking_data[message_id]:
            self.tracking_data[message_id]["clicks"] = []
        
        self.tracking_data[message_id]["clicks"].append({
            "url": url,
            "clicked_at": datetime.now()
        })
        logger.info(f"Email {message_id} link clicked: {url}")


class EmailService:
    """Email service for sending emails and managing templates."""
    
    def __init__(self, config: EmailServiceConfig):
        self.config = config
        self.template_engine = EmailTemplateEngine()
        self.tracker = EmailTracker()
        self.templates: Dict[uuid.UUID, EmailTemplate] = {}
        self.sent_messages: Dict[uuid.UUID, EmailMessage] = {}
    
    async def send_email(self, message: EmailMessage) -> bool:
        """Send an email message."""
        try:
            # Set defaults if not provided
            if not message.from_email:
                message.from_email = self.config.default_from_email
            if not message.from_name:
                message.from_name = self.config.default_from_name
            
            # Create MIME message
            mime_message = MIMEMultipart("alternative")
            mime_message["Subject"] = message.subject
            mime_message["From"] = f"{message.from_name} <{message.from_email}>"
            mime_message["To"] = f"{message.to_name or ''} <{message.to_email}>"
            
            if message.reply_to:
                mime_message["Reply-To"] = message.reply_to
            
            # Add tracking pixel to HTML content
            html_content = message.body_html
            if message.id:
                tracking_pixel = self.tracker.generate_tracking_pixel(message.id)
                html_content = html_content.replace("</body>", f"{tracking_pixel}</body>")
                html_content = self.tracker.generate_tracking_links(html_content, message.id)
            
            # Attach text and HTML parts
            text_part = MIMEText(message.body_text, "plain")
            html_part = MIMEText(html_content, "html")
            
            mime_message.attach(text_part)
            mime_message.attach(html_part)
            
            # Send email
            await self._send_smtp_email(mime_message, message.to_email)
            
            # Update message status
            message.status = MessageStatus.SENT
            message.sent_at = datetime.now()
            
            if message.id:
                self.sent_messages[message.id] = message
            
            logger.info(f"Email sent successfully to {message.to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {message.to_email}: {e}")
            message.status = MessageStatus.FAILED
            return False
    
    async def _send_smtp_email(self, mime_message: MIMEMultipart, to_email: str):
        """Send email via SMTP."""
        try:
            if self.config.use_tls:
                await aiosmtplib.send(
                    mime_message,
                    hostname=self.config.smtp_host,
                    port=self.config.smtp_port,
                    username=self.config.smtp_username,
                    password=self.config.smtp_password,
                    use_tls=True
                )
            else:
                await aiosmtplib.send(
                    mime_message,
                    hostname=self.config.smtp_host,
                    port=self.config.smtp_port,
                    username=self.config.smtp_username,
                    password=self.config.smtp_password
                )
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    async def send_template_email(
        self,
        template_id: uuid.UUID,
        to_email: str,
        variables: Dict[str, Any],
        to_name: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        scheduled_at: Optional[datetime] = None
    ) -> EmailMessage:
        """Send an email using a template."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Render template
        rendered = self.template_engine.render_template(template, variables)
        
        # Create message
        message = EmailMessage(
            id=uuid.uuid4(),
            to_email=to_email,
            to_name=to_name,
            subject=rendered["subject"],
            body_html=rendered["body_html"],
            body_text=rendered["body_text"],
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
            logger.info(f"Email scheduled for {scheduled_at}")
        else:
            await self.send_email(message)
        
        return message
    
    def create_template(self, template: EmailTemplate) -> EmailTemplate:
        """Create a new email template."""
        if not template.id:
            template.id = uuid.uuid4()
        
        template.created_at = datetime.now()
        template.updated_at = datetime.now()
        
        # Validate template
        errors = self.template_engine.validate_template(template)
        if errors:
            raise ValueError(f"Template validation errors: {errors}")
        
        self.templates[template.id] = template
        logger.info(f"Email template created: {template.name}")
        return template
    
    def update_template(self, template_id: uuid.UUID, updates: Dict[str, Any]) -> EmailTemplate:
        """Update an existing email template."""
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
        logger.info(f"Email template updated: {template.name}")
        return template
    
    def get_template(self, template_id: uuid.UUID) -> Optional[EmailTemplate]:
        """Get an email template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[EmailTemplate]:
        """List all email templates, optionally filtered by category."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return templates
    
    def delete_template(self, template_id: uuid.UUID) -> bool:
        """Delete an email template."""
        if template_id in self.templates:
            del self.templates[template_id]
            logger.info(f"Email template deleted: {template_id}")
            return True
        return False
    
    def handle_bounce(self, message_id: uuid.UUID, bounce_reason: str):
        """Handle email bounce notification."""
        if message_id in self.sent_messages:
            message = self.sent_messages[message_id]
            message.status = MessageStatus.BOUNCED
            message.bounced_at = datetime.now()
            message.bounce_reason = bounce_reason
            logger.warning(f"Email {message_id} bounced: {bounce_reason}")
    
    def handle_reply(self, message_id: uuid.UUID, reply_content: str):
        """Handle email reply."""
        if message_id in self.sent_messages:
            message = self.sent_messages[message_id]
            message.status = MessageStatus.REPLIED
            logger.info(f"Email {message_id} received reply")
            # In a real implementation, you'd store the reply content
    
    def get_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        category: Optional[str] = None
    ) -> CommunicationAnalytics:
        """Get email analytics for a date range."""
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
        total_opened = len([m for m in messages if m.status == MessageStatus.OPENED])
        total_clicked = len([m for m in messages if m.status == MessageStatus.CLICKED])
        total_replied = len([m for m in messages if m.status == MessageStatus.REPLIED])
        total_bounced = len([m for m in messages if m.status == MessageStatus.BOUNCED])
        
        return CommunicationAnalytics(
            channel=CommunicationChannel.EMAIL,
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_opened=total_opened,
            total_clicked=total_clicked,
            total_replied=total_replied,
            total_bounced=total_bounced,
            delivery_rate=total_delivered / total_sent if total_sent > 0 else 0.0,
            open_rate=total_opened / total_delivered if total_delivered > 0 else 0.0,
            click_rate=total_clicked / total_opened if total_opened > 0 else 0.0,
            reply_rate=total_replied / total_delivered if total_delivered > 0 else 0.0,
            bounce_rate=total_bounced / total_sent if total_sent > 0 else 0.0,
            period_start=start_date,
            period_end=end_date
        )
    
    async def send_bulk_emails(
        self,
        template_id: uuid.UUID,
        recipients: List[Dict[str, Any]],
        batch_size: int = 10,
        delay_seconds: float = 1.0
    ) -> List[EmailMessage]:
        """Send bulk emails with rate limiting."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        sent_messages = []
        
        # Process in batches
        for i in range(0, len(recipients), batch_size):
            batch = recipients[i:i + batch_size]
            batch_tasks = []
            
            for recipient in batch:
                message = await self.send_template_email(
                    template_id=template_id,
                    to_email=recipient["email"],
                    variables=recipient.get("variables", {}),
                    to_name=recipient.get("name"),
                    priority=recipient.get("priority", MessagePriority.NORMAL)
                )
                batch_tasks.append(message)
            
            sent_messages.extend(batch_tasks)
            
            # Delay between batches to avoid rate limiting
            if i + batch_size < len(recipients):
                await asyncio.sleep(delay_seconds)
        
        logger.info(f"Bulk email sent to {len(recipients)} recipients")
        return sent_messages