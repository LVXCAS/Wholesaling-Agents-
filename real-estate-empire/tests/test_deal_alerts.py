"""
Unit tests for the Deal Alert System

Tests the real-time notification system, email alerts, mobile push notifications,
and alert preference management functionality.
"""

import pytest
import uuid
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.deal_alert_service import DealAlertService
from app.models.deal_alerts import (
    AlertTypeEnum, AlertPriorityEnum, AlertChannelEnum, AlertStatusEnum,
    NotificationFrequencyEnum, AlertPreference, AlertRule, DealAlert,
    AlertDelivery, AlertTemplate, AlertSubscription, WebhookEndpoint
)


class TestDealAlertService:
    """Test cases for DealAlertService"""
    
    @pytest.fixture
    def alert_service(self):
        """Create a DealAlertService instance for testing"""
        return DealAlertService()
    
    @pytest.fixture
    def sample_user_id(self):
        """Create a sample user ID for testing"""
        return uuid.uuid4()
    
    @pytest.fixture
    def sample_deal_data(self):
        """Create sample deal data for testing"""
        return {
            "deal_id": uuid.uuid4(),
            "property_id": uuid.uuid4(),
            "address": "123 Test St, Test City, TS",
            "price": 350000,
            "score": 85,
            "bedrooms": 3,
            "bathrooms": 2,
            "square_feet": 1500
        }
    
    def test_create_alert_rule(self, alert_service, sample_user_id):
        """Test creating an alert rule"""
        conditions = {"min_score": 80, "max_price": 500000}
        
        rule = alert_service.create_alert_rule(
            user_id=sample_user_id,
            name="High Score Deals",
            alert_type=AlertTypeEnum.HIGH_SCORE,
            conditions=conditions,
            priority=AlertPriorityEnum.HIGH
        )
        
        assert isinstance(rule, AlertRule)
        assert rule.user_id == sample_user_id
        assert rule.name == "High Score Deals"
        assert rule.alert_type == AlertTypeEnum.HIGH_SCORE
        assert rule.conditions == conditions
        assert rule.priority == AlertPriorityEnum.HIGH
        assert rule.active == True
        assert rule.trigger_count == 0
    
    def test_create_deal_alert(self, alert_service, sample_user_id):
        """Test creating a deal alert"""
        alert = alert_service.create_deal_alert(
            user_id=sample_user_id,
            alert_type=AlertTypeEnum.NEW_DEAL,
            title="New Deal Alert",
            message="A new deal matching your criteria has been found",
            priority=AlertPriorityEnum.MEDIUM,
            channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.PUSH]
        )
        
        assert isinstance(alert, DealAlert)
        assert alert.user_id == sample_user_id
        assert alert.alert_type == AlertTypeEnum.NEW_DEAL
        assert alert.title == "New Deal Alert"
        assert alert.priority == AlertPriorityEnum.MEDIUM
        assert AlertChannelEnum.EMAIL in alert.channels
        assert AlertChannelEnum.PUSH in alert.channels
        assert alert.status == AlertStatusEnum.PENDING
        
        # Check that alert was added to queue
        assert alert in alert_service.alert_queue
    
    def test_get_user_alert_preferences(self, alert_service, sample_user_id):
        """Test getting user alert preferences"""
        preferences = alert_service.get_user_alert_preferences(sample_user_id)
        
        assert len(preferences) == len(AlertTypeEnum)
        assert all(isinstance(pref, AlertPreference) for pref in preferences)
        assert all(pref.user_id == sample_user_id for pref in preferences)
        
        # Check that all alert types are covered
        alert_types = set(pref.alert_type for pref in preferences)
        assert alert_types == set(AlertTypeEnum)
        
        # Check default settings
        for pref in preferences:
            assert pref.enabled == True
            assert pref.email_enabled == True
            assert pref.sms_enabled == False
            assert pref.push_enabled == True
            assert pref.in_app_enabled == True
    
    def test_update_alert_preference(self, alert_service, sample_user_id):
        """Test updating alert preferences"""
        updated_pref = alert_service.update_alert_preference(
            user_id=sample_user_id,
            alert_type=AlertTypeEnum.HIGH_SCORE,
            enabled=True,
            email_enabled=False,
            sms_enabled=True,
            frequency=NotificationFrequencyEnum.HOURLY
        )
        
        assert isinstance(updated_pref, AlertPreference)
        assert updated_pref.user_id == sample_user_id
        assert updated_pref.alert_type == AlertTypeEnum.HIGH_SCORE
        assert updated_pref.enabled == True
        assert updated_pref.email_enabled == False
        assert updated_pref.sms_enabled == True
        assert updated_pref.frequency == NotificationFrequencyEnum.HOURLY
    
    def test_check_alert_rules(self, alert_service, sample_deal_data):
        """Test checking which alert rules are triggered"""
        triggered_rules = alert_service.check_alert_rules(sample_deal_data)
        
        assert isinstance(triggered_rules, list)
        
        # With mock data, should trigger high score rule since score is 85
        assert len(triggered_rules) > 0
        
        high_score_rule = next(
            (rule for rule in triggered_rules if rule.alert_type == AlertTypeEnum.HIGH_SCORE),
            None
        )
        assert high_score_rule is not None
        assert high_score_rule.conditions["min_score"] <= sample_deal_data["score"]
    
    def test_check_alert_rules_no_match(self, alert_service):
        """Test alert rules with deal that doesn't match"""
        low_score_deal = {
            "deal_id": uuid.uuid4(),
            "score": 50,  # Below threshold
            "price": 300000
        }
        
        triggered_rules = alert_service.check_alert_rules(low_score_deal)
        
        # Should not trigger high score rule
        high_score_rules = [
            rule for rule in triggered_rules 
            if rule.alert_type == AlertTypeEnum.HIGH_SCORE
        ]
        assert len(high_score_rules) == 0
    
    def test_generate_alert_message(self, alert_service, sample_deal_data):
        """Test alert message generation"""
        # Test high score alert message
        high_score_rule = AlertRule(
            user_id=uuid.uuid4(),
            name="High Score Rule",
            alert_type=AlertTypeEnum.HIGH_SCORE,
            conditions={}
        )
        
        message = alert_service._generate_alert_message(high_score_rule, sample_deal_data)
        assert "High-scoring deal found" in message
        assert str(sample_deal_data["score"]) in message
        
        # Test new deal alert message
        new_deal_rule = AlertRule(
            user_id=uuid.uuid4(),
            name="New Deal Rule",
            alert_type=AlertTypeEnum.NEW_DEAL,
            conditions={}
        )
        
        message = alert_service._generate_alert_message(new_deal_rule, sample_deal_data)
        assert "New deal matching" in message
        assert sample_deal_data["address"] in message
        
        # Test price drop alert message
        price_drop_rule = AlertRule(
            user_id=uuid.uuid4(),
            name="Price Drop Rule",
            alert_type=AlertTypeEnum.PRICE_DROP,
            conditions={}
        )
        
        message = alert_service._generate_alert_message(price_drop_rule, sample_deal_data)
        assert "Price drop alert" in message
        assert str(sample_deal_data["price"]) in message
    
    def test_should_send_alert_priority_filtering(self, alert_service):
        """Test alert filtering based on priority"""
        # Create alert with medium priority
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.NEW_DEAL,
            title="Test Alert",
            message="Test message",
            priority=AlertPriorityEnum.MEDIUM,
            channels=[AlertChannelEnum.EMAIL]
        )
        
        # Create preference that only allows high priority alerts
        preference = AlertPreference(
            user_id=alert.user_id,
            alert_type=AlertTypeEnum.NEW_DEAL,
            enabled=True,
            min_priority=AlertPriorityEnum.HIGH
        )
        
        # Should not send medium priority alert with high priority threshold
        assert alert_service._should_send_alert(alert, preference) == False
        
        # Change alert to high priority
        alert.priority = AlertPriorityEnum.HIGH
        assert alert_service._should_send_alert(alert, preference) == True
    
    def test_should_send_alert_frequency_never(self, alert_service):
        """Test alert filtering with NEVER frequency"""
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.NEW_DEAL,
            title="Test Alert",
            message="Test message",
            priority=AlertPriorityEnum.HIGH,
            channels=[AlertChannelEnum.EMAIL]
        )
        
        preference = AlertPreference(
            user_id=alert.user_id,
            alert_type=AlertTypeEnum.NEW_DEAL,
            enabled=True,
            frequency=NotificationFrequencyEnum.NEVER
        )
        
        assert alert_service._should_send_alert(alert, preference) == False
    
    @pytest.mark.asyncio
    async def test_send_email_alert(self, alert_service):
        """Test sending email alert"""
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.NEW_DEAL,
            title="Test Email Alert",
            message="This is a test email alert",
            priority=AlertPriorityEnum.MEDIUM,
            channels=[AlertChannelEnum.EMAIL]
        )
        
        delivery = await alert_service._send_email_alert(alert)
        
        assert isinstance(delivery, AlertDelivery)
        assert delivery.alert_id == alert.id
        assert delivery.channel == AlertChannelEnum.EMAIL
        assert delivery.status == AlertStatusEnum.SENT  # Mock successful delivery
        assert delivery.sent_at is not None
    
    @pytest.mark.asyncio
    async def test_send_sms_alert(self, alert_service):
        """Test sending SMS alert"""
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.HIGH_SCORE,
            title="Test SMS Alert",
            message="This is a test SMS alert",
            priority=AlertPriorityEnum.HIGH,
            channels=[AlertChannelEnum.SMS]
        )
        
        delivery = await alert_service._send_sms_alert(alert)
        
        assert isinstance(delivery, AlertDelivery)
        assert delivery.alert_id == alert.id
        assert delivery.channel == AlertChannelEnum.SMS
        assert delivery.status == AlertStatusEnum.SENT  # Mock successful delivery
        assert delivery.sent_at is not None
    
    @pytest.mark.asyncio
    async def test_send_push_alert(self, alert_service):
        """Test sending push notification"""
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.PRICE_DROP,
            title="Test Push Alert",
            message="This is a test push notification",
            priority=AlertPriorityEnum.URGENT,
            channels=[AlertChannelEnum.PUSH]
        )
        
        delivery = await alert_service._send_push_alert(alert)
        
        assert isinstance(delivery, AlertDelivery)
        assert delivery.alert_id == alert.id
        assert delivery.channel == AlertChannelEnum.PUSH
        assert delivery.status == AlertStatusEnum.SENT  # Mock successful delivery
        assert delivery.sent_at is not None
    
    @pytest.mark.asyncio
    async def test_send_in_app_alert(self, alert_service):
        """Test sending in-app notification"""
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.DEADLINE_REMINDER,
            title="Test In-App Alert",
            message="This is a test in-app notification",
            priority=AlertPriorityEnum.MEDIUM,
            channels=[AlertChannelEnum.IN_APP]
        )
        
        delivery = await alert_service._send_in_app_alert(alert)
        
        assert isinstance(delivery, AlertDelivery)
        assert delivery.alert_id == alert.id
        assert delivery.channel == AlertChannelEnum.IN_APP
        assert delivery.status == AlertStatusEnum.SENT
        assert delivery.sent_at is not None
        assert delivery.recipient == str(alert.user_id)
    
    def test_get_email_template(self, alert_service):
        """Test getting email template"""
        template = alert_service._get_email_template(AlertTypeEnum.NEW_DEAL)
        
        assert isinstance(template, AlertTemplate)
        assert template.alert_type == AlertTypeEnum.NEW_DEAL
        assert template.channel == AlertChannelEnum.EMAIL
        assert template.subject_template is not None
        assert template.message_template is not None
        assert "{title}" in template.subject_template
        assert "{title}" in template.message_template
        assert "{message}" in template.message_template
    
    def test_get_sms_template(self, alert_service):
        """Test getting SMS template"""
        template = alert_service._get_sms_template(AlertTypeEnum.HIGH_SCORE)
        
        assert isinstance(template, AlertTemplate)
        assert template.alert_type == AlertTypeEnum.HIGH_SCORE
        assert template.channel == AlertChannelEnum.SMS
        assert template.message_template is not None
        assert "{title}" in template.message_template
        assert "{message}" in template.message_template
    
    def test_create_alert_subscription(self, alert_service, sample_user_id):
        """Test creating alert subscription"""
        criteria = {
            "min_price": 200000,
            "max_price": 500000,
            "min_bedrooms": 2,
            "neighborhoods": ["Downtown", "Midtown"]
        }
        
        subscription = alert_service.create_alert_subscription(
            user_id=sample_user_id,
            name="Mid-Range Properties",
            criteria=criteria,
            alert_types=[AlertTypeEnum.NEW_DEAL, AlertTypeEnum.PRICE_DROP],
            channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.PUSH]
        )
        
        assert isinstance(subscription, AlertSubscription)
        assert subscription.user_id == sample_user_id
        assert subscription.name == "Mid-Range Properties"
        assert subscription.criteria == criteria
        assert AlertTypeEnum.NEW_DEAL in subscription.alert_types
        assert AlertTypeEnum.PRICE_DROP in subscription.alert_types
        assert AlertChannelEnum.EMAIL in subscription.channels
        assert AlertChannelEnum.PUSH in subscription.channels
        assert subscription.active == True
    
    def test_check_subscriptions_for_deal(self, alert_service):
        """Test checking subscriptions for a deal"""
        deal_data = {
            "deal_id": uuid.uuid4(),
            "price": 350000,
            "bedrooms": 3,
            "neighborhood": "Downtown"
        }
        
        matching_subscriptions = alert_service.check_subscriptions_for_deal(deal_data)
        
        assert isinstance(matching_subscriptions, list)
        
        # With mock data, should match subscription for price range 200k-500k
        assert len(matching_subscriptions) > 0
        
        subscription = matching_subscriptions[0]
        assert subscription.criteria["min_price"] <= deal_data["price"] <= subscription.criteria["max_price"]
    
    def test_check_subscriptions_no_match(self, alert_service):
        """Test subscription checking with non-matching deal"""
        deal_data = {
            "deal_id": uuid.uuid4(),
            "price": 600000,  # Above max price in mock subscription
            "bedrooms": 3
        }
        
        matching_subscriptions = alert_service.check_subscriptions_for_deal(deal_data)
        
        # Should not match any subscriptions due to high price
        assert len(matching_subscriptions) == 0
    
    def test_process_deal_for_alerts(self, alert_service, sample_deal_data):
        """Test processing a deal for alerts"""
        initial_queue_size = len(alert_service.alert_queue)
        
        alert_service.process_deal_for_alerts(sample_deal_data)
        
        # Should have added alerts to queue
        assert len(alert_service.alert_queue) > initial_queue_size
        
        # Check that alerts were created for triggered rules and subscriptions
        new_alerts = alert_service.alert_queue[initial_queue_size:]
        
        # Should have alerts for both rules and subscriptions
        alert_types = set(alert.alert_type for alert in new_alerts)
        assert len(alert_types) > 0
    
    def test_get_user_alerts(self, alert_service, sample_user_id):
        """Test getting user alerts"""
        alerts = alert_service.get_user_alerts(sample_user_id, limit=10)
        
        assert isinstance(alerts, list)
        assert len(alerts) <= 10
        assert all(isinstance(alert, DealAlert) for alert in alerts)
        assert all(alert.user_id == sample_user_id for alert in alerts)
        
        # Check that alerts are ordered by creation time (most recent first)
        if len(alerts) > 1:
            for i in range(len(alerts) - 1):
                assert alerts[i].created_at >= alerts[i + 1].created_at
    
    def test_get_user_alerts_with_status_filter(self, alert_service, sample_user_id):
        """Test getting user alerts with status filter"""
        alerts = alert_service.get_user_alerts(
            sample_user_id, 
            limit=10, 
            status=AlertStatusEnum.SENT
        )
        
        assert all(alert.status == AlertStatusEnum.SENT for alert in alerts)
    
    def test_mark_alert_as_read(self, alert_service, sample_user_id):
        """Test marking alert as read"""
        alert_id = uuid.uuid4()
        
        result = alert_service.mark_alert_as_read(alert_id, sample_user_id)
        
        assert result == True  # Mock successful update
    
    def test_get_alert_analytics(self, alert_service, sample_user_id):
        """Test getting alert analytics"""
        analytics = alert_service.get_alert_analytics(user_id=sample_user_id)
        
        assert isinstance(analytics, AlertAnalytics)
        assert analytics.total_alerts_created >= 0
        assert analytics.total_alerts_sent >= 0
        assert analytics.total_alerts_delivered >= 0
        assert analytics.total_alerts_read >= 0
        assert 0 <= analytics.delivery_rate <= 1
        assert 0 <= analytics.read_rate <= 1
        assert analytics.active_users >= 0
        assert analytics.engaged_users >= 0
        
        # Check that channel stats are present
        assert isinstance(analytics.channel_stats, dict)
        assert len(analytics.channel_stats) > 0
        
        # Check that type stats are present
        assert isinstance(analytics.type_stats, dict)
        assert len(analytics.type_stats) > 0
        
        # Check that priority stats are present
        assert isinstance(analytics.priority_stats, dict)
        assert len(analytics.priority_stats) > 0
    
    def test_create_webhook_endpoint(self, alert_service, sample_user_id):
        """Test creating webhook endpoint"""
        endpoint = alert_service.create_webhook_endpoint(
            user_id=sample_user_id,
            name="Test Webhook",
            url="https://example.com/webhook",
            method="POST",
            secret="webhook_secret_123",
            alert_types=[AlertTypeEnum.HIGH_SCORE, AlertTypeEnum.NEW_DEAL]
        )
        
        assert isinstance(endpoint, WebhookEndpoint)
        assert endpoint.user_id == sample_user_id
        assert endpoint.name == "Test Webhook"
        assert endpoint.url == "https://example.com/webhook"
        assert endpoint.method == "POST"
        assert endpoint.secret == "webhook_secret_123"
        assert AlertTypeEnum.HIGH_SCORE in endpoint.alert_types
        assert AlertTypeEnum.NEW_DEAL in endpoint.alert_types
        assert endpoint.active == True
        assert endpoint.failure_count == 0
    
    @pytest.mark.asyncio
    @patch('requests.request')
    async def test_send_webhook_alert_success(self, mock_request, alert_service):
        """Test successful webhook alert delivery"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_request.return_value = mock_response
        
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.HIGH_SCORE,
            title="Test Webhook Alert",
            message="This is a test webhook alert",
            priority=AlertPriorityEnum.HIGH,
            channels=[AlertChannelEnum.WEBHOOK]
        )
        
        endpoint = WebhookEndpoint(
            user_id=alert.user_id,
            name="Test Endpoint",
            url="https://example.com/webhook",
            method="POST"
        )
        
        delivery = await alert_service.send_webhook_alert(alert, endpoint)
        
        assert isinstance(delivery, AlertDelivery)
        assert delivery.alert_id == alert.id
        assert delivery.channel == AlertChannelEnum.WEBHOOK
        assert delivery.status == AlertStatusEnum.SENT
        assert delivery.sent_at is not None
        assert endpoint.last_success is not None
        assert endpoint.failure_count == 0
        
        # Verify webhook was called with correct parameters
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == "POST"
        assert call_args[1]['url'] == "https://example.com/webhook"
        assert 'json' in call_args[1]
        
        # Check payload structure
        payload = call_args[1]['json']
        assert payload['alert_id'] == str(alert.id)
        assert payload['alert_type'] == alert.alert_type
        assert payload['title'] == alert.title
        assert payload['message'] == alert.message
    
    @pytest.mark.asyncio
    @patch('requests.request')
    async def test_send_webhook_alert_failure(self, mock_request, alert_service):
        """Test failed webhook alert delivery"""
        # Mock failed HTTP response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_request.return_value = mock_response
        
        alert = DealAlert(
            user_id=uuid.uuid4(),
            alert_type=AlertTypeEnum.NEW_DEAL,
            title="Test Webhook Alert",
            message="This is a test webhook alert",
            priority=AlertPriorityEnum.MEDIUM,
            channels=[AlertChannelEnum.WEBHOOK]
        )
        
        endpoint = WebhookEndpoint(
            user_id=alert.user_id,
            name="Test Endpoint",
            url="https://example.com/webhook"
        )
        
        delivery = await alert_service.send_webhook_alert(alert, endpoint)
        
        assert delivery.status == AlertStatusEnum.FAILED
        assert delivery.error_message is not None
        assert "500" in delivery.error_message
        assert endpoint.last_failure is not None
        assert endpoint.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_process_alert_batch(self, alert_service, sample_user_id):
        """Test processing a batch of alerts"""
        # Create test alerts
        alerts = []
        for i in range(3):
            alert = DealAlert(
                user_id=sample_user_id,
                alert_type=AlertTypeEnum.NEW_DEAL,
                title=f"Test Alert {i+1}",
                message=f"This is test alert {i+1}",
                priority=AlertPriorityEnum.MEDIUM,
                channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.IN_APP]
            )
            alerts.append(alert)
        
        # Process the batch
        await alert_service._process_alert_batch(alerts)
        
        # Check that alerts were processed (status should be updated)
        for alert in alerts:
            assert alert.status in [AlertStatusEnum.SENT, AlertStatusEnum.CANCELLED, AlertStatusEnum.FAILED]
    
    @pytest.mark.asyncio
    async def test_process_alert_queue(self, alert_service, sample_user_id):
        """Test processing the alert queue"""
        # Add alerts to queue
        for i in range(5):
            alert = alert_service.create_deal_alert(
                user_id=sample_user_id,
                alert_type=AlertTypeEnum.NEW_DEAL,
                title=f"Queue Test Alert {i+1}",
                message=f"This is queue test alert {i+1}",
                priority=AlertPriorityEnum.MEDIUM,
                channels=[AlertChannelEnum.EMAIL]
            )
        
        initial_queue_size = len(alert_service.alert_queue)
        assert initial_queue_size == 5
        
        # Process the queue
        await alert_service.process_alert_queue()
        
        # Queue should be empty or smaller after processing
        assert len(alert_service.alert_queue) <= initial_queue_size
    
    def test_cleanup_old_alerts(self, alert_service):
        """Test cleaning up old alerts"""
        # Test cleanup function
        deleted_count = alert_service.cleanup_old_alerts(days_old=30)
        
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0


class TestAlertTemplate:
    """Test cases for AlertTemplate model"""
    
    def test_template_render(self):
        """Test template rendering with variables"""
        template = AlertTemplate(
            name="Test Template",
            alert_type=AlertTypeEnum.NEW_DEAL,
            channel=AlertChannelEnum.EMAIL,
            subject_template="New Deal Alert: {property_address}",
            message_template="A new deal has been found at {property_address} for ${price}. Score: {score}"
        )
        
        variables = {
            "property_address": "123 Main St",
            "price": "350000",
            "score": "85"
        }
        
        rendered = template.render(variables)
        
        assert rendered["subject"] == "New Deal Alert: 123 Main St"
        assert rendered["message"] == "A new deal has been found at 123 Main St for $350000. Score: 85"
    
    def test_template_render_missing_variables(self):
        """Test template rendering with missing variables"""
        template = AlertTemplate(
            name="Test Template",
            alert_type=AlertTypeEnum.NEW_DEAL,
            channel=AlertChannelEnum.EMAIL,
            subject_template="Alert: {title}",
            message_template="Message: {message} - Missing: {missing_var}"
        )
        
        variables = {
            "title": "Test Title",
            "message": "Test Message"
            # missing_var is not provided
        }
        
        rendered = template.render(variables)
        
        assert rendered["subject"] == "Alert: Test Title"
        assert rendered["message"] == "Message: Test Message - Missing: {missing_var}"  # Placeholder remains


class TestAlertModels:
    """Test cases for alert data models"""
    
    def test_alert_preference_creation(self):
        """Test creating alert preference"""
        user_id = uuid.uuid4()
        
        preference = AlertPreference(
            user_id=user_id,
            alert_type=AlertTypeEnum.HIGH_SCORE,
            enabled=True,
            email_enabled=True,
            sms_enabled=False,
            frequency=NotificationFrequencyEnum.IMMEDIATE,
            min_priority=AlertPriorityEnum.MEDIUM
        )
        
        assert preference.user_id == user_id
        assert preference.alert_type == AlertTypeEnum.HIGH_SCORE
        assert preference.enabled == True
        assert preference.email_enabled == True
        assert preference.sms_enabled == False
        assert preference.frequency == NotificationFrequencyEnum.IMMEDIATE
        assert preference.min_priority == AlertPriorityEnum.MEDIUM
    
    def test_deal_alert_creation(self):
        """Test creating deal alert"""
        user_id = uuid.uuid4()
        deal_id = uuid.uuid4()
        
        alert = DealAlert(
            user_id=user_id,
            alert_type=AlertTypeEnum.PRICE_DROP,
            title="Price Drop Alert",
            message="Price has dropped on your watched property",
            priority=AlertPriorityEnum.HIGH,
            channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.PUSH],
            deal_id=deal_id
        )
        
        assert alert.user_id == user_id
        assert alert.alert_type == AlertTypeEnum.PRICE_DROP
        assert alert.title == "Price Drop Alert"
        assert alert.priority == AlertPriorityEnum.HIGH
        assert alert.deal_id == deal_id
        assert alert.status == AlertStatusEnum.PENDING
        assert alert.delivery_attempts == 0
        assert alert.max_delivery_attempts == 3
    
    def test_alert_rule_creation(self):
        """Test creating alert rule"""
        user_id = uuid.uuid4()
        
        rule = AlertRule(
            user_id=user_id,
            name="High Value Deals",
            alert_type=AlertTypeEnum.CRITERIA_MATCH,
            conditions={"min_price": 500000, "max_price": 1000000},
            priority=AlertPriorityEnum.HIGH,
            channels=[AlertChannelEnum.EMAIL, AlertChannelEnum.SMS],
            max_alerts_per_hour=5,
            max_alerts_per_day=20
        )
        
        assert rule.user_id == user_id
        assert rule.name == "High Value Deals"
        assert rule.alert_type == AlertTypeEnum.CRITERIA_MATCH
        assert rule.conditions["min_price"] == 500000
        assert rule.conditions["max_price"] == 1000000
        assert rule.priority == AlertPriorityEnum.HIGH
        assert rule.max_alerts_per_hour == 5
        assert rule.max_alerts_per_day == 20
        assert rule.active == True
        assert rule.trigger_count == 0
    
    def test_webhook_endpoint_creation(self):
        """Test creating webhook endpoint"""
        user_id = uuid.uuid4()
        
        endpoint = WebhookEndpoint(
            user_id=user_id,
            name="My Webhook",
            url="https://myapp.com/webhook",
            method="POST",
            secret="secret123",
            alert_types=[AlertTypeEnum.NEW_DEAL, AlertTypeEnum.HIGH_SCORE],
            rate_limit_per_minute=60
        )
        
        assert endpoint.user_id == user_id
        assert endpoint.name == "My Webhook"
        assert endpoint.url == "https://myapp.com/webhook"
        assert endpoint.method == "POST"
        assert endpoint.secret == "secret123"
        assert AlertTypeEnum.NEW_DEAL in endpoint.alert_types
        assert AlertTypeEnum.HIGH_SCORE in endpoint.alert_types
        assert endpoint.rate_limit_per_minute == 60
        assert endpoint.active == True
        assert endpoint.failure_count == 0