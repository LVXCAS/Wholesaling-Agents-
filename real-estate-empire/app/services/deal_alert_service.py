"""
Deal Alert Service

This service handles real-time notifications, email alerts, mobile push notifications,
and alert preference management for the real estate deal sourcing engine.
"""

from typing import List, Dict, Optional, Any, Tuple
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from twilio.rest import Client as TwilioClient

from app.models.deal_alerts import (
    AlertTypeEnum, AlertPriorityEnum, AlertChannelEnum, AlertStatusEnum,
    NotificationFrequencyEnum, AlertPreference, AlertRule, DealAlert,
    AlertDelivery, AlertTemplate, AlertBatch, AlertAnalytics,
    AlertSubscription, AlertQueue, WebhookEndpoint
)
from app.core.database import get_db


class DealAlertService:
    """Service for managing deal alerts and notifications"""
    
    def __init__(self, db: Session = None):
        self.db = db
        
        # Configuration (would be loaded from environment variables)
        self.smtp_server = "smtp.gmail.com"  # os.getenv('SMTP_SERVER')
        self.smtp_port = 587  # int(os.getenv('SMTP_PORT', 587))
        self.smtp_username = None  # os.getenv('SMTP_USERNAME')
        self.smtp_password = None  # os.getenv('SMTP_PASSWORD')
        
        # Twilio configuration
        self.twilio_account_sid = None  # os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = None  # os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = None  # os.getenv('TWILIO_PHONE_NUMBER')
        
        # Push notification configuration
        self.firebase_server_key = None  # os.getenv('FIREBASE_SERVER_KEY')
        
        # Initialize clients
        self.twilio_client = None
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = TwilioClient(self.twilio_account_sid, self.twilio_auth_token)
        
        # Alert queue for processing
        self.alert_queue = []
        self.processing_queue = False
    
    def create_alert_rule(self, user_id: uuid.UUID, name: str, alert_type: AlertTypeEnum,
                         conditions: Dict[str, Any], **kwargs) -> AlertRule:
        """Create a new alert rule"""
        rule = AlertRule(
            user_id=user_id,
            name=name,
            alert_type=alert_type,
            conditions=conditions,
            **kwargs
        )
        
        # In a real implementation, this would save to database
        # self.db.add(rule)
        # self.db.commit()
        
        return rule
    
    def create_deal_alert(self, user_id: uuid.UUID, alert_type: AlertTypeEnum,
                         title: str, message: str, **kwargs) -> DealAlert:
        """Create a new deal alert"""
        alert = DealAlert(
            user_id=user_id,
            alert_type=alert_type,
            title=title,
            message=message,
            **kwargs
        )
        
        # Add to processing queue
        self.alert_queue.append(alert)
        
        # In a real implementation, this would save to database
        # self.db.add(alert)
        # self.db.commit()
        
        return alert
    
    def get_user_alert_preferences(self, user_id: uuid.UUID) -> List[AlertPreference]:
        """Get user's alert preferences"""
        # In a real implementation, this would query the database
        # For now, return default preferences
        default_preferences = []
        
        for alert_type in AlertTypeEnum:
            preference = AlertPreference(
                user_id=user_id,
                alert_type=alert_type,
                enabled=True,
                email_enabled=True,
                sms_enabled=False,
                push_enabled=True,
                in_app_enabled=True
            )
            default_preferences.append(preference)
        
        return default_preferences
    
    def update_alert_preference(self, user_id: uuid.UUID, alert_type: AlertTypeEnum,
                              **updates) -> AlertPreference:
        """Update user's alert preference for a specific alert type"""
        # In a real implementation, this would update the database
        preference = AlertPreference(
            user_id=user_id,
            alert_type=alert_type,
            **updates
        )
        
        return preference
    
    def check_alert_rules(self, deal_data: Dict[str, Any]) -> List[AlertRule]:
        """Check which alert rules are triggered by deal data"""
        triggered_rules = []
        
        # In a real implementation, this would query active rules from database
        # and evaluate conditions against deal_data
        
        # Mock rule evaluation
        mock_rule = AlertRule(
            user_id=uuid.uuid4(),
            name="High Score Deal Alert",
            alert_type=AlertTypeEnum.HIGH_SCORE,
            conditions={"min_score": 80},
            priority=AlertPriorityEnum.HIGH,
            channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.PUSH]
        )
        
        # Check if deal meets rule conditions
        if deal_data.get("score", 0) >= mock_rule.conditions.get("min_score", 0):
            triggered_rules.append(mock_rule)
        
        return triggered_rules
    
    def process_triggered_rules(self, rules: List[AlertRule], deal_data: Dict[str, Any]):
        """Process triggered alert rules and create alerts"""
        for rule in rules:
            # Create alert based on rule
            alert = self.create_deal_alert(
                user_id=rule.user_id,
                alert_type=rule.alert_type,
                title=f"Deal Alert: {rule.name}",
                message=self._generate_alert_message(rule, deal_data),
                priority=rule.priority,
                channels=rule.channels,
                rule_id=rule.id,
                deal_id=deal_data.get("deal_id"),
                property_id=deal_data.get("property_id"),
                alert_data=deal_data
            )
            
            # Update rule statistics
            rule.last_triggered = datetime.now()
            rule.trigger_count += 1
    
    def _generate_alert_message(self, rule: AlertRule, deal_data: Dict[str, Any]) -> str:
        """Generate alert message based on rule and deal data"""
        if rule.alert_type == AlertTypeEnum.HIGH_SCORE:
            return f"High-scoring deal found! Score: {deal_data.get('score', 'N/A')}"
        elif rule.alert_type == AlertTypeEnum.NEW_DEAL:
            return f"New deal matching your criteria: {deal_data.get('address', 'Unknown address')}"
        elif rule.alert_type == AlertTypeEnum.PRICE_DROP:
            return f"Price drop alert: {deal_data.get('address', 'Property')} - New price: ${deal_data.get('price', 'N/A')}"
        else:
            return f"Deal alert: {rule.name}"
    
    async def process_alert_queue(self):
        """Process alerts in the queue"""
        if self.processing_queue or not self.alert_queue:
            return
        
        self.processing_queue = True
        
        try:
            # Process alerts in batches
            batch_size = 10
            while self.alert_queue:
                batch = self.alert_queue[:batch_size]
                self.alert_queue = self.alert_queue[batch_size:]
                
                # Process batch
                await self._process_alert_batch(batch)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
        
        finally:
            self.processing_queue = False
    
    async def _process_alert_batch(self, alerts: List[DealAlert]):
        """Process a batch of alerts"""
        for alert in alerts:
            try:
                # Get user preferences
                preferences = self.get_user_alert_preferences(alert.user_id)
                alert_pref = next(
                    (p for p in preferences if p.alert_type == alert.alert_type),
                    None
                )
                
                if not alert_pref or not alert_pref.enabled:
                    alert.status = AlertStatusEnum.CANCELLED
                    continue
                
                # Check if alert should be sent based on frequency and timing
                if not self._should_send_alert(alert, alert_pref):
                    continue
                
                # Send alert through enabled channels
                await self._send_alert(alert, alert_pref)
                
            except Exception as e:
                alert.status = AlertStatusEnum.FAILED
                alert.last_error = str(e)
                alert.delivery_attempts += 1
    
    def _should_send_alert(self, alert: DealAlert, preference: AlertPreference) -> bool:
        """Check if alert should be sent based on preferences and timing"""
        # Check priority threshold
        priority_order = {
            AlertPriorityEnum.LOW: 1,
            AlertPriorityEnum.MEDIUM: 2,
            AlertPriorityEnum.HIGH: 3,
            AlertPriorityEnum.URGENT: 4
        }
        
        if priority_order[alert.priority] < priority_order[preference.min_priority]:
            return False
        
        # Check quiet hours
        if preference.quiet_hours_start and preference.quiet_hours_end:
            current_time = datetime.now().time()
            quiet_start = datetime.strptime(preference.quiet_hours_start, "%H:%M").time()
            quiet_end = datetime.strptime(preference.quiet_hours_end, "%H:%M").time()
            
            if quiet_start <= current_time <= quiet_end:
                return False
        
        # Check frequency (simplified - would need more complex logic for batching)
        if preference.frequency == NotificationFrequencyEnum.NEVER:
            return False
        
        return True
    
    async def _send_alert(self, alert: DealAlert, preference: AlertPreference):
        """Send alert through enabled channels"""
        deliveries = []
        
        for channel in alert.channels:
            if channel == AlertChannelEnum.EMAIL and preference.email_enabled:
                delivery = await self._send_email_alert(alert)
                deliveries.append(delivery)
            
            elif channel == AlertChannelEnum.SMS and preference.sms_enabled:
                delivery = await self._send_sms_alert(alert)
                deliveries.append(delivery)
            
            elif channel == AlertChannelEnum.PUSH and preference.push_enabled:
                delivery = await self._send_push_alert(alert)
                deliveries.append(delivery)
            
            elif channel == AlertChannelEnum.IN_APP and preference.in_app_enabled:
                delivery = await self._send_in_app_alert(alert)
                deliveries.append(delivery)
        
        # Update alert status based on deliveries
        if all(d.status == AlertStatusEnum.SENT for d in deliveries):
            alert.status = AlertStatusEnum.SENT
            alert.sent_at = datetime.now()
        elif any(d.status == AlertStatusEnum.SENT for d in deliveries):
            alert.status = AlertStatusEnum.SENT
            alert.sent_at = datetime.now()
        else:
            alert.status = AlertStatusEnum.FAILED
    
    async def _send_email_alert(self, alert: DealAlert) -> AlertDelivery:
        """Send email alert"""
        delivery = AlertDelivery(
            alert_id=alert.id,
            channel=AlertChannelEnum.EMAIL,
            recipient="user@example.com",  # Would get from user profile
            status=AlertStatusEnum.PENDING
        )
        
        try:
            if not self.smtp_username or not self.smtp_password:
                # Mock successful delivery for testing
                delivery.status = AlertStatusEnum.SENT
                delivery.sent_at = datetime.now()
                return delivery
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = delivery.recipient
            msg['Subject'] = alert.title
            
            # Get or create email template
            template = self._get_email_template(alert.alert_type)
            rendered = template.render({
                'title': alert.title,
                'message': alert.message,
                'user_name': 'User',  # Would get from user profile
                'deal_data': alert.alert_data or {}
            })
            
            msg.attach(MIMEText(rendered['message'], 'html'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            delivery.status = AlertStatusEnum.SENT
            delivery.sent_at = datetime.now()
            
        except Exception as e:
            delivery.status = AlertStatusEnum.FAILED
            delivery.error_message = str(e)
        
        return delivery
    
    async def _send_sms_alert(self, alert: DealAlert) -> AlertDelivery:
        """Send SMS alert"""
        delivery = AlertDelivery(
            alert_id=alert.id,
            channel=AlertChannelEnum.SMS,
            recipient="+1234567890",  # Would get from user profile
            status=AlertStatusEnum.PENDING
        )
        
        try:
            if not self.twilio_client:
                # Mock successful delivery for testing
                delivery.status = AlertStatusEnum.SENT
                delivery.sent_at = datetime.now()
                return delivery
            
            # Get SMS template
            template = self._get_sms_template(alert.alert_type)
            rendered = template.render({
                'title': alert.title,
                'message': alert.message,
                'deal_data': alert.alert_data or {}
            })
            
            # Send SMS
            message = self.twilio_client.messages.create(
                body=rendered['message'],
                from_=self.twilio_phone_number,
                to=delivery.recipient
            )
            
            delivery.status = AlertStatusEnum.SENT
            delivery.sent_at = datetime.now()
            delivery.provider_message_id = message.sid
            
        except Exception as e:
            delivery.status = AlertStatusEnum.FAILED
            delivery.error_message = str(e)
        
        return delivery
    
    async def _send_push_alert(self, alert: DealAlert) -> AlertDelivery:
        """Send push notification"""
        delivery = AlertDelivery(
            alert_id=alert.id,
            channel=AlertChannelEnum.PUSH,
            recipient="device_token_123",  # Would get from user profile
            status=AlertStatusEnum.PENDING
        )
        
        try:
            if not self.firebase_server_key:
                # Mock successful delivery for testing
                delivery.status = AlertStatusEnum.SENT
                delivery.sent_at = datetime.now()
                return delivery
            
            # Prepare push notification payload
            payload = {
                "to": delivery.recipient,
                "notification": {
                    "title": alert.title,
                    "body": alert.message,
                    "icon": "deal_icon",
                    "click_action": "OPEN_DEAL"
                },
                "data": {
                    "alert_id": str(alert.id),
                    "alert_type": alert.alert_type,
                    "deal_id": str(alert.deal_id) if alert.deal_id else None
                }
            }
            
            # Send push notification
            headers = {
                "Authorization": f"key={self.firebase_server_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://fcm.googleapis.com/fcm/send",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                delivery.status = AlertStatusEnum.SENT
                delivery.sent_at = datetime.now()
            else:
                delivery.status = AlertStatusEnum.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text}"
            
        except Exception as e:
            delivery.status = AlertStatusEnum.FAILED
            delivery.error_message = str(e)
        
        return delivery
    
    async def _send_in_app_alert(self, alert: DealAlert) -> AlertDelivery:
        """Send in-app notification"""
        delivery = AlertDelivery(
            alert_id=alert.id,
            channel=AlertChannelEnum.IN_APP,
            recipient=str(alert.user_id),
            status=AlertStatusEnum.SENT,  # In-app notifications are always "sent"
            sent_at=datetime.now()
        )
        
        # In-app notifications are stored in database for user to see
        # This would typically update a notifications table
        
        return delivery
    
    def _get_email_template(self, alert_type: AlertTypeEnum) -> AlertTemplate:
        """Get email template for alert type"""
        # In a real implementation, this would query the database
        return AlertTemplate(
            name=f"Email template for {alert_type}",
            alert_type=alert_type,
            channel=AlertChannelEnum.EMAIL,
            subject_template="Real Estate Alert: {title}",
            message_template="""
            <html>
            <body>
                <h2>{title}</h2>
                <p>{message}</p>
                <p>Best regards,<br>Real Estate Empire Team</p>
            </body>
            </html>
            """
        )
    
    def _get_sms_template(self, alert_type: AlertTypeEnum) -> AlertTemplate:
        """Get SMS template for alert type"""
        return AlertTemplate(
            name=f"SMS template for {alert_type}",
            alert_type=alert_type,
            channel=AlertChannelEnum.SMS,
            message_template="Real Estate Alert: {title} - {message}"
        )
    
    def create_alert_subscription(self, user_id: uuid.UUID, name: str,
                                criteria: Dict[str, Any], **kwargs) -> AlertSubscription:
        """Create a new alert subscription"""
        subscription = AlertSubscription(
            user_id=user_id,
            name=name,
            criteria=criteria,
            **kwargs
        )
        
        # In a real implementation, this would save to database
        return subscription
    
    def check_subscriptions_for_deal(self, deal_data: Dict[str, Any]) -> List[AlertSubscription]:
        """Check which subscriptions match a deal"""
        matching_subscriptions = []
        
        # In a real implementation, this would query active subscriptions
        # and evaluate criteria against deal_data
        
        # Mock subscription matching
        mock_subscription = AlertSubscription(
            user_id=uuid.uuid4(),
            name="High Value Deals",
            criteria={"min_price": 200000, "max_price": 500000},
            alert_types=[AlertTypeEnum.NEW_DEAL, AlertTypeEnum.CRITERIA_MATCH]
        )
        
        # Check if deal matches subscription criteria
        deal_price = deal_data.get("price", 0)
        if (mock_subscription.criteria.get("min_price", 0) <= deal_price <= 
            mock_subscription.criteria.get("max_price", float('inf'))):
            matching_subscriptions.append(mock_subscription)
        
        return matching_subscriptions
    
    def process_deal_for_alerts(self, deal_data: Dict[str, Any]):
        """Process a deal and trigger appropriate alerts"""
        # Check alert rules
        triggered_rules = self.check_alert_rules(deal_data)
        if triggered_rules:
            self.process_triggered_rules(triggered_rules, deal_data)
        
        # Check subscriptions
        matching_subscriptions = self.check_subscriptions_for_deal(deal_data)
        for subscription in matching_subscriptions:
            for alert_type in subscription.alert_types:
                self.create_deal_alert(
                    user_id=subscription.user_id,
                    alert_type=alert_type,
                    title=f"Subscription Alert: {subscription.name}",
                    message=f"New deal matching your subscription: {deal_data.get('address', 'Unknown')}",
                    channels=subscription.channels,
                    deal_id=deal_data.get("deal_id"),
                    property_id=deal_data.get("property_id"),
                    alert_data=deal_data
                )
    
    def get_user_alerts(self, user_id: uuid.UUID, limit: int = 50,
                       status: Optional[AlertStatusEnum] = None) -> List[DealAlert]:
        """Get alerts for a user"""
        # In a real implementation, this would query the database
        # For now, return mock alerts
        mock_alerts = []
        
        for i in range(min(limit, 5)):  # Return up to 5 mock alerts
            alert = DealAlert(
                user_id=user_id,
                alert_type=AlertTypeEnum.NEW_DEAL,
                priority=AlertPriorityEnum.MEDIUM,
                title=f"Mock Alert {i+1}",
                message=f"This is mock alert number {i+1}",
                channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.IN_APP],
                status=status or AlertStatusEnum.SENT,
                created_at=datetime.now() - timedelta(hours=i)
            )
            mock_alerts.append(alert)
        
        return mock_alerts
    
    def mark_alert_as_read(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Mark an alert as read"""
        # In a real implementation, this would update the database
        # For now, just return success
        return True
    
    def get_alert_analytics(self, user_id: Optional[uuid.UUID] = None,
                          period_start: Optional[datetime] = None,
                          period_end: Optional[datetime] = None) -> AlertAnalytics:
        """Get alert analytics"""
        if period_end is None:
            period_end = datetime.now()
        if period_start is None:
            period_start = period_end - timedelta(days=30)
        
        # In a real implementation, this would query the database
        # For now, return mock analytics
        return AlertAnalytics(
            period_start=period_start,
            period_end=period_end,
            total_alerts_created=150,
            total_alerts_sent=145,
            total_alerts_delivered=140,
            total_alerts_read=85,
            delivery_rate=0.97,
            read_rate=0.61,
            average_delivery_time_seconds=2.5,
            channel_stats={
                AlertChannelEnum.EMAIL: {"sent": 100, "delivered": 98, "read": 60},
                AlertChannelEnum.SMS: {"sent": 25, "delivered": 24, "read": 15},
                AlertChannelEnum.PUSH: {"sent": 20, "delivered": 18, "read": 10}
            },
            type_stats={
                AlertTypeEnum.NEW_DEAL: {"created": 80, "sent": 78, "read": 45},
                AlertTypeEnum.HIGH_SCORE: {"created": 40, "sent": 39, "read": 25},
                AlertTypeEnum.PRICE_DROP: {"created": 30, "sent": 28, "read": 15}
            },
            priority_stats={
                AlertPriorityEnum.HIGH: {"created": 20, "sent": 20, "read": 18},
                AlertPriorityEnum.MEDIUM: {"created": 80, "sent": 78, "read": 45},
                AlertPriorityEnum.LOW: {"created": 50, "sent": 47, "read": 22}
            },
            active_users=25,
            engaged_users=18,
            top_errors=[]
        )
    
    def create_webhook_endpoint(self, user_id: uuid.UUID, name: str, url: str,
                              **kwargs) -> WebhookEndpoint:
        """Create a webhook endpoint for alert delivery"""
        endpoint = WebhookEndpoint(
            user_id=user_id,
            name=name,
            url=url,
            **kwargs
        )
        
        # In a real implementation, this would save to database
        return endpoint
    
    async def send_webhook_alert(self, alert: DealAlert, endpoint: WebhookEndpoint) -> AlertDelivery:
        """Send alert to webhook endpoint"""
        delivery = AlertDelivery(
            alert_id=alert.id,
            channel=AlertChannelEnum.WEBHOOK,
            recipient=endpoint.url,
            status=AlertStatusEnum.PENDING
        )
        
        try:
            # Prepare webhook payload
            payload = {
                "alert_id": str(alert.id),
                "alert_type": alert.alert_type,
                "priority": alert.priority,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "deal_id": str(alert.deal_id) if alert.deal_id else None,
                "property_id": str(alert.property_id) if alert.property_id else None,
                "alert_data": alert.alert_data
            }
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if endpoint.headers:
                headers.update(endpoint.headers)
            
            # Add signature if secret is configured
            if endpoint.secret:
                import hmac
                import hashlib
                
                signature = hmac.new(
                    endpoint.secret.encode(),
                    json.dumps(payload).encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Send webhook
            response = requests.request(
                method=endpoint.method,
                url=endpoint.url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if 200 <= response.status_code < 300:
                delivery.status = AlertStatusEnum.SENT
                delivery.sent_at = datetime.now()
                endpoint.last_success = datetime.now()
                endpoint.failure_count = 0
            else:
                delivery.status = AlertStatusEnum.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text}"
                endpoint.last_failure = datetime.now()
                endpoint.failure_count += 1
            
        except Exception as e:
            delivery.status = AlertStatusEnum.FAILED
            delivery.error_message = str(e)
            endpoint.last_failure = datetime.now()
            endpoint.failure_count += 1
        
        return delivery
    
    def cleanup_old_alerts(self, days_old: int = 30):
        """Clean up old alerts to manage storage"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # In a real implementation, this would delete old alerts from database
        # For now, just return the count that would be deleted
        return 0  # Mock return
    
    async def start_alert_processor(self):
        """Start the background alert processor"""
        while True:
            try:
                await self.process_alert_queue()
                await asyncio.sleep(5)  # Process every 5 seconds
            except Exception as e:
                print(f"Error in alert processor: {e}")
                await asyncio.sleep(10)  # Wait longer on error