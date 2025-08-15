"""
Unit tests for the Audit Compliance Service.
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.services.audit_compliance_service import AuditComplianceService
from app.models.audit_compliance import (
    AuditLogDB, ComplianceRuleDB, ComplianceCheckDB, DataRetentionPolicyDB,
    DataRetentionRecordDB, RegulatoryReportDB,
    AuditEventTypeEnum, ComplianceStatusEnum, DataRetentionStatusEnum,
    AuditLogCreate, ComplianceRuleCreate, ComplianceCheckCreate,
    DataRetentionPolicyCreate, RegulatoryReportCreate, AuditSearchRequest
)


class TestAuditComplianceService:
    """Test cases for AuditComplianceService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create an AuditComplianceService instance with mocked dependencies."""
        return AuditComplianceService(mock_db)
    
    @pytest.fixture
    def sample_audit_log(self):
        """Create a sample audit log."""
        return AuditLogDB(
            id=uuid.uuid4(),
            event_type=AuditEventTypeEnum.DATA_CREATE,
            event_description="Created new property record",
            user_id="user123",
            user_email="test@example.com",
            resource_type="property",
            resource_id="prop123",
            compliance_relevant=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_compliance_rule(self):
        """Create a sample compliance rule."""
        return ComplianceRuleDB(
            id=uuid.uuid4(),
            name="Data Retention Rule",
            rule_type="data_retention",
            rule_config={"max_retention_days": 365},
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    @pytest.fixture
    def sample_retention_policy(self):
        """Create a sample data retention policy."""
        return DataRetentionPolicyDB(
            id=uuid.uuid4(),
            name="Property Data Retention",
            data_type="property_data",
            retention_period_days=365,
            retention_trigger="creation_date",
            auto_delete_enabled=True,
            is_active=True,
            created_at=datetime.utcnow()
        )
    
    def test_log_audit_event_success(self, service, mock_db):
        """Test successful audit event logging."""
        # Arrange
        audit_data = AuditLogCreate(
            event_type=AuditEventTypeEnum.DATA_CREATE,
            event_description="Test audit event",
            user_id="user123",
            user_email="test@example.com",
            resource_type="property",
            resource_id="prop123",
            compliance_relevant=True
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.log_audit_event(audit_data)
        
        # Assert
        assert result is not None
        assert result.event_type == AuditEventTypeEnum.DATA_CREATE
        assert result.event_description == "Test audit event"
        assert result.user_id == "user123"
        assert result.compliance_relevant == True
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_search_audit_logs_success(self, service, mock_db, sample_audit_log):
        """Test successful audit log search."""
        # Arrange
        search_request = AuditSearchRequest(
            event_types=[AuditEventTypeEnum.DATA_CREATE],
            user_id="user123",
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            limit=10
        )
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_audit_log]
        
        mock_db.query.return_value = mock_query
        
        # Act
        result = service.search_audit_logs(search_request)
        
        # Assert
        assert len(result) == 1
        assert result[0].event_type == AuditEventTypeEnum.DATA_CREATE
        assert result[0].user_id == "user123"
        
        mock_db.query.assert_called()
    
    def test_get_audit_statistics_success(self, service, mock_db):
        """Test successful audit statistics retrieval."""
        # Arrange
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 100
        mock_db.query.return_value = mock_query
        
        # Mock aggregation queries
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            Mock(event_type="DATA_CREATE", count=50),
            Mock(event_type="DATA_UPDATE", count=30)
        ]
        
        # Act
        result = service.get_audit_statistics(start_date, end_date)
        
        # Assert
        assert "total_events" in result
        assert "event_type_distribution" in result
        assert "security_events" in result
        assert "compliance_events" in result
        assert result["period"]["start_date"] == start_date.isoformat()
        assert result["period"]["end_date"] == end_date.isoformat()
    
    def test_create_compliance_rule_success(self, service, mock_db):
        """Test successful compliance rule creation."""
        # Arrange
        rule_data = ComplianceRuleCreate(
            name="Test Compliance Rule",
            description="Test rule description",
            rule_type="data_retention",
            rule_config={"max_retention_days": 365},
            regulation_reference="GDPR Article 5"
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
            obj.is_active = True
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_compliance_rule(rule_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Compliance Rule"
        assert result.rule_type == "data_retention"
        assert result.rule_config == {"max_retention_days": 365}
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_compliance_rules_success(self, service, mock_db, sample_compliance_rule):
        """Test successful compliance rules retrieval."""
        # Arrange
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_compliance_rule]
        
        # Act
        result = service.get_compliance_rules()
        
        # Assert
        assert len(result) == 1
        assert result[0].name == sample_compliance_rule.name
        assert result[0].rule_type == sample_compliance_rule.rule_type
        
        mock_db.query.assert_called()
    
    def test_run_compliance_check_success(self, service, mock_db, sample_compliance_rule):
        """Test successful compliance check execution."""
        # Arrange
        check_data = ComplianceCheckCreate(
            rule_id=sample_compliance_rule.id,
            check_type="automated",
            check_description="Automated compliance check"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_compliance_rule
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock the compliance check method
        service._perform_compliance_check = Mock(return_value={
            "status": ComplianceStatusEnum.COMPLIANT,
            "compliance_score": 95.0,
            "violations_found": 0,
            "violations_details": [],
            "recommendations": [],
            "remediation_required": False
        })
        
        # Mock log_audit_event
        service.log_audit_event = Mock()
        
        # Act
        result = service.run_compliance_check(check_data)
        
        # Assert
        assert result is not None
        assert result.rule_id == sample_compliance_rule.id
        assert result.status == ComplianceStatusEnum.COMPLIANT
        assert result.compliance_score == 95.0
        
        service._perform_compliance_check.assert_called_once()
        service.log_audit_event.assert_called_once()
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    def test_run_compliance_check_rule_not_found(self, service, mock_db):
        """Test compliance check when rule is not found."""
        # Arrange
        check_data = ComplianceCheckCreate(
            rule_id=uuid.uuid4(),
            check_type="automated"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Compliance rule .* not found"):
            service.run_compliance_check(check_data)
    
    def test_create_data_retention_policy_success(self, service, mock_db):
        """Test successful data retention policy creation."""
        # Arrange
        policy_data = DataRetentionPolicyCreate(
            name="Test Retention Policy",
            data_type="property_data",
            retention_period_days=365,
            retention_trigger="creation_date",
            legal_basis="Contract performance"
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
            obj.is_active = True
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.create_data_retention_policy(policy_data)
        
        # Assert
        assert result is not None
        assert result.name == "Test Retention Policy"
        assert result.data_type == "property_data"
        assert result.retention_period_days == 365
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_register_data_for_retention_success(self, service, mock_db, sample_retention_policy):
        """Test successful data registration for retention."""
        # Arrange
        data_type = "property_data"
        data_id = "prop123"
        data_created_at = datetime.utcnow() - timedelta(days=30)
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_retention_policy
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
            obj.status = DataRetentionStatusEnum.ACTIVE
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        result = service.register_data_for_retention(data_type, data_id, data_created_at)
        
        # Assert
        assert result is not None
        assert result.data_type == data_type
        assert result.data_id == data_id
        assert result.status == DataRetentionStatusEnum.ACTIVE
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_register_data_for_retention_no_policy(self, service, mock_db):
        """Test data registration when no retention policy exists."""
        # Arrange
        data_type = "unknown_data"
        data_id = "data123"
        data_created_at = datetime.utcnow()
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = service.register_data_for_retention(data_type, data_id, data_created_at)
        
        # Assert
        assert result is None
    
    def test_process_data_retention_success(self, service, mock_db):
        """Test successful data retention processing."""
        # Arrange
        retention_record = DataRetentionRecordDB(
            id=uuid.uuid4(),
            data_type="property_data",
            data_id="prop123",
            retention_deadline=datetime.utcnow() - timedelta(days=1),  # Overdue
            status=DataRetentionStatusEnum.ACTIVE,
            legal_hold_active=False
        )
        
        # Mock policy
        retention_record.policy = Mock()
        retention_record.policy.archive_before_delete = True
        retention_record.policy.auto_delete_enabled = True
        
        mock_db.query.return_value.filter.return_value.all.return_value = [retention_record]
        mock_db.commit = Mock()
        
        # Mock archive and delete methods
        service._archive_data = Mock(return_value={"success": True, "location": "/archive/path"})
        service._delete_data = Mock(return_value={"success": True})
        
        # Act
        results = service.process_data_retention()
        
        # Assert
        assert len(results) == 2  # Archive and delete actions
        assert results[0]["action"] == "archived"
        assert results[0]["status"] == "success"
        assert results[1]["action"] == "deleted"
        assert results[1]["status"] == "success"
        
        service._archive_data.assert_called_once()
        service._delete_data.assert_called_once()
        mock_db.commit.assert_called()
    
    def test_generate_regulatory_report_success(self, service, mock_db):
        """Test successful regulatory report generation."""
        # Arrange
        report_data = RegulatoryReportCreate(
            report_name="GDPR Compliance Report",
            report_type="gdpr_compliance",
            regulation="GDPR",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            report_data={"test": "data"}
        )
        
        def mock_add(obj):
            obj.id = uuid.uuid4()
            obj.created_at = datetime.utcnow()
            obj.updated_at = datetime.utcnow()
            obj.status = "draft"
            obj.generated_at = datetime.utcnow()
        
        mock_db.add = Mock(side_effect=mock_add)
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Mock report generation methods
        service._generate_report_content = Mock(return_value={"report": "content"})
        service._save_regulatory_report = Mock(return_value="/path/to/report.json")
        
        # Act
        result = service.generate_regulatory_report(report_data)
        
        # Assert
        assert result is not None
        assert result.report_name == "GDPR Compliance Report"
        assert result.report_type == "gdpr_compliance"
        assert result.regulation == "GDPR"
        
        service._generate_report_content.assert_called_once()
        service._save_regulatory_report.assert_called_once()
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
    
    def test_get_compliance_dashboard_success(self, service, mock_db):
        """Test successful compliance dashboard data retrieval."""
        # Arrange
        mock_db.query.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.count.return_value = 8
        
        # Mock scalar query for violations
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        
        # Mock upcoming deadlines and trends
        service._get_upcoming_deadlines = Mock(return_value=[])
        service._get_compliance_trends = Mock(return_value=[])
        
        # Act
        result = service.get_compliance_dashboard()
        
        # Assert
        assert result is not None
        assert result.total_rules >= 0
        assert result.active_rules >= 0
        assert result.violations_count >= 0
        assert isinstance(result.upcoming_deadlines, list)
        assert isinstance(result.compliance_trends, list)
    
    def test_check_data_retention_compliance(self, service, mock_db, sample_compliance_rule):
        """Test data retention compliance check."""
        # Arrange
        sample_compliance_rule.rule_config = {"max_retention_days": 365}
        
        # Mock overdue records query
        mock_db.query.return_value.filter.return_value.count.return_value = 2  # 2 overdue records
        mock_db.query.return_value.count.return_value = 10  # 10 total records
        
        # Act
        result = service._check_data_retention_compliance(sample_compliance_rule)
        
        # Assert
        assert result["status"] == ComplianceStatusEnum.NON_COMPLIANT
        assert result["compliance_score"] == 80.0  # (10-2)/10 * 100
        assert result["violations_found"] == 1
        assert result["remediation_required"] == True
        assert "overdue_retention" in result["violations_details"][0]["type"]
    
    def test_check_audit_trail_compliance(self, service, mock_db, sample_compliance_rule):
        """Test audit trail compliance check."""
        # Arrange
        sample_compliance_rule.rule_config = {
            "required_events": ["DATA_CREATE", "DATA_UPDATE"],
            "min_retention_days": 90
        }
        
        # Mock event count queries - no events found
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Act
        result = service._check_audit_trail_compliance(sample_compliance_rule)
        
        # Assert
        assert result["status"] == ComplianceStatusEnum.NON_COMPLIANT
        assert result["compliance_score"] == 0.0  # No required events found
        assert result["violations_found"] == 2  # 2 missing event types
        assert result["remediation_required"] == True
    
    def test_archive_data_success(self, service):
        """Test successful data archival."""
        # Arrange
        record = DataRetentionRecordDB(
            data_type="property_data",
            data_id="prop123"
        )
        
        # Act
        result = service._archive_data(record)
        
        # Assert
        assert result["success"] == True
        assert "location" in result
    
    def test_delete_data_success(self, service):
        """Test successful data deletion."""
        # Arrange
        record = DataRetentionRecordDB(
            data_type="property_data",
            data_id="prop123"
        )
        
        # Act
        result = service._delete_data(record)
        
        # Assert
        assert result["success"] == True
    
    def test_generate_gdpr_report(self, service, mock_db):
        """Test GDPR report generation."""
        # Arrange
        report_data = RegulatoryReportCreate(
            report_name="GDPR Report",
            report_type="gdpr_compliance",
            regulation="GDPR",
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            report_data={}
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # Mock helper methods
        service._count_data_subject_requests = Mock(return_value=5)
        service._count_data_breaches = Mock(return_value=0)
        service._get_retention_compliance_summary = Mock(return_value={"compliant": 100})
        service._get_consent_summary = Mock(return_value={"active": 50})
        service._get_gdpr_recommendations = Mock(return_value=["Maintain compliance"])
        
        # Act
        result = service._generate_gdpr_report(report_data)
        
        # Assert
        assert result["report_type"] == "GDPR Compliance Report"
        assert "data_processing_activities" in result
        assert "data_subject_requests" in result
        assert "data_breaches" in result
        assert result["data_subject_requests"] == 5
        assert result["data_breaches"] == 0
    
    def test_error_handling_audit_logging(self, service, mock_db):
        """Test error handling in audit logging."""
        # Arrange
        audit_data = AuditLogCreate(
            event_type=AuditEventTypeEnum.DATA_CREATE,
            event_description="Test event"
        )
        
        mock_db.add = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            service.log_audit_event(audit_data)
        
        mock_db.rollback.assert_called_once()
    
    def test_error_handling_compliance_rule_creation(self, service, mock_db):
        """Test error handling in compliance rule creation."""
        # Arrange
        rule_data = ComplianceRuleCreate(
            name="Test Rule",
            rule_type="data_retention",
            rule_config={}
        )
        
        mock_db.add = Mock(side_effect=Exception("Database error"))
        mock_db.rollback = Mock()
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            service.create_compliance_rule(rule_data)
        
        mock_db.rollback.assert_called_once()
    
    @pytest.mark.parametrize("rule_type,expected_method", [
        ("data_retention", "_check_data_retention_compliance"),
        ("access_control", "_check_access_control_compliance"),
        ("privacy", "_check_privacy_compliance"),
        ("audit_trail", "_check_audit_trail_compliance"),
        ("unknown", "_check_generic_compliance")
    ])
    def test_compliance_check_method_selection(self, service, rule_type, expected_method):
        """Test that the correct compliance check method is selected for each rule type."""
        # Arrange
        rule = Mock()
        rule.rule_type = rule_type
        check_data = Mock()
        
        # Mock all check methods
        service._check_data_retention_compliance = Mock(return_value={"status": "compliant"})
        service._check_access_control_compliance = Mock(return_value={"status": "compliant"})
        service._check_privacy_compliance = Mock(return_value={"status": "compliant"})
        service._check_audit_trail_compliance = Mock(return_value={"status": "compliant"})
        service._check_generic_compliance = Mock(return_value={"status": "compliant"})
        
        # Act
        service._perform_compliance_check(rule, check_data)
        
        # Assert
        if rule_type == "data_retention":
            service._check_data_retention_compliance.assert_called_once()
        elif rule_type == "access_control":
            service._check_access_control_compliance.assert_called_once()
        elif rule_type == "privacy":
            service._check_privacy_compliance.assert_called_once()
        elif rule_type == "audit_trail":
            service._check_audit_trail_compliance.assert_called_once()
        else:
            service._check_generic_compliance.assert_called_once()
    
    def test_run_scheduled_compliance_checks_success(self, service, mock_db, sample_compliance_rule):
        """Test successful scheduled compliance checks."""
        # Arrange
        sample_compliance_rule.last_checked = datetime.utcnow() - timedelta(hours=25)  # Due for check
        sample_compliance_rule.check_frequency_hours = 24
        
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_compliance_rule]
        
        # Mock run_compliance_check
        mock_result = Mock()
        mock_result.id = uuid.uuid4()
        mock_result.status = ComplianceStatusEnum.COMPLIANT
        mock_result.compliance_score = 95.0
        mock_result.violations_found = 0
        
        service.run_compliance_check = Mock(return_value=mock_result)
        
        # Act
        results = service.run_scheduled_compliance_checks()
        
        # Assert
        assert len(results) == 1
        assert results[0]["rule_id"] == sample_compliance_rule.id
        assert results[0]["status"] == ComplianceStatusEnum.COMPLIANT
        assert results[0]["compliance_score"] == 95.0
        
        service.run_compliance_check.assert_called_once()
    
    def test_get_upcoming_deadlines(self, service, mock_db):
        """Test getting upcoming deadlines."""
        # Arrange
        retention_record = Mock()
        retention_record.data_type = "property_data"
        retention_record.retention_deadline = datetime.utcnow() + timedelta(days=5)
        
        remediation_check = Mock()
        remediation_check.remediation_deadline = datetime.utcnow() + timedelta(days=3)
        
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [retention_record]
        
        # Act
        result = service._get_upcoming_deadlines()
        
        # Assert
        assert isinstance(result, list)
        # The method should return deadlines sorted by days remaining
    
    def test_get_compliance_trends(self, service, mock_db):
        """Test getting compliance trends."""
        # Arrange
        mock_check = Mock()
        mock_check.compliance_score = 90.0
        mock_check.violations_found = 1
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_check]
        
        # Act
        result = service._get_compliance_trends()
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 12  # 12 months of trends
        if result:
            assert "month" in result[0]
            assert "compliance_score" in result[0]
            assert "violations_count" in result[0]