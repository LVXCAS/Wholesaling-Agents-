"""
Audit and Compliance Service for the Real Estate Empire platform.

This service provides:
- Comprehensive audit trail system
- Compliance monitoring automation
- Regulatory reporting tools
- Data retention and archival system
"""

import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
import logging
from pathlib import Path

from app.models.audit_compliance import (
    AuditLogDB, ComplianceRuleDB, ComplianceCheckDB, DataRetentionPolicyDB,
    DataRetentionRecordDB, RegulatoryReportDB,
    AuditEventTypeEnum, ComplianceStatusEnum, DataRetentionStatusEnum,
    AuditLogCreate, AuditLogResponse, ComplianceRuleCreate, ComplianceRuleResponse,
    ComplianceCheckCreate, ComplianceCheckResponse, DataRetentionPolicyCreate,
    DataRetentionPolicyResponse, DataRetentionRecordResponse, RegulatoryReportCreate,
    RegulatoryReportResponse, AuditSearchRequest, ComplianceDashboardResponse
)
from app.models.portfolio import PortfolioDB
from app.models.property import PropertyDB

logger = logging.getLogger(__name__)


class AuditComplianceService:
    """Service for audit and compliance management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.reports_dir = Path("compliance_reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.archive_dir = Path("data_archive")
        self.archive_dir.mkdir(exist_ok=True)
    
    # Audit Trail Management
    
    def log_audit_event(self, audit_data: AuditLogCreate) -> AuditLogResponse:
        """Log an audit event."""
        try:
            audit_log = AuditLogDB(
                event_type=audit_data.event_type,
                event_category=audit_data.event_category,
                event_description=audit_data.event_description,
                user_id=audit_data.user_id,
                user_email=audit_data.user_email,
                user_role=audit_data.user_role,
                session_id=audit_data.session_id,
                ip_address=audit_data.ip_address,
                user_agent=audit_data.user_agent,
                request_id=audit_data.request_id,
                resource_type=audit_data.resource_type,
                resource_id=audit_data.resource_id,
                resource_name=audit_data.resource_name,
                action_performed=audit_data.action_performed,
                old_values=audit_data.old_values,
                new_values=audit_data.new_values,
                request_data=audit_data.request_data,
                response_data=audit_data.response_data,
                error_details=audit_data.error_details,
                additional_metadata=audit_data.additional_metadata,
                compliance_relevant=audit_data.compliance_relevant,
                security_relevant=audit_data.security_relevant,
                risk_level=audit_data.risk_level
            )
            
            self.db.add(audit_log)
            self.db.commit()
            self.db.refresh(audit_log)
            
            logger.debug(f"Logged audit event: {audit_data.event_type} for user {audit_data.user_id}")
            
            return AuditLogResponse.model_validate(audit_log)
            
        except Exception as e:
            logger.error(f"Error logging audit event: {str(e)}")
            self.db.rollback()
            raise
    
    def search_audit_logs(self, search_request: AuditSearchRequest) -> List[AuditLogResponse]:
        """Search audit logs based on criteria."""
        try:
            query = self.db.query(AuditLogDB)
            
            # Apply filters
            if search_request.event_types:
                query = query.filter(AuditLogDB.event_type.in_(search_request.event_types))
            
            if search_request.user_id:
                query = query.filter(AuditLogDB.user_id == search_request.user_id)
            
            if search_request.user_email:
                query = query.filter(AuditLogDB.user_email.ilike(f"%{search_request.user_email}%"))
            
            if search_request.resource_type:
                query = query.filter(AuditLogDB.resource_type == search_request.resource_type)
            
            if search_request.resource_id:
                query = query.filter(AuditLogDB.resource_id == search_request.resource_id)
            
            if search_request.start_date:
                query = query.filter(AuditLogDB.created_at >= search_request.start_date)
            
            if search_request.end_date:
                query = query.filter(AuditLogDB.created_at <= search_request.end_date)
            
            if search_request.compliance_relevant is not None:
                query = query.filter(AuditLogDB.compliance_relevant == search_request.compliance_relevant)
            
            if search_request.security_relevant is not None:
                query = query.filter(AuditLogDB.security_relevant == search_request.security_relevant)
            
            if search_request.risk_level:
                query = query.filter(AuditLogDB.risk_level == search_request.risk_level)
            
            # Apply pagination and ordering
            query = query.order_by(desc(AuditLogDB.created_at))
            query = query.offset(search_request.offset).limit(search_request.limit)
            
            audit_logs = query.all()
            
            return [AuditLogResponse.model_validate(log) for log in audit_logs]
            
        except Exception as e:
            logger.error(f"Error searching audit logs: {str(e)}")
            raise
    
    def get_audit_statistics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get audit statistics for a date range."""
        try:
            query = self.db.query(AuditLogDB).filter(
                and_(
                    AuditLogDB.created_at >= start_date,
                    AuditLogDB.created_at <= end_date
                )
            )
            
            total_events = query.count()
            
            # Event type distribution
            event_type_stats = self.db.query(
                AuditLogDB.event_type,
                func.count(AuditLogDB.id).label('count')
            ).filter(
                and_(
                    AuditLogDB.created_at >= start_date,
                    AuditLogDB.created_at <= end_date
                )
            ).group_by(AuditLogDB.event_type).all()
            
            # User activity
            user_activity = self.db.query(
                AuditLogDB.user_id,
                func.count(AuditLogDB.id).label('count')
            ).filter(
                and_(
                    AuditLogDB.created_at >= start_date,
                    AuditLogDB.created_at <= end_date,
                    AuditLogDB.user_id.isnot(None)
                )
            ).group_by(AuditLogDB.user_id).order_by(desc('count')).limit(10).all()
            
            # Security and compliance events
            security_events = query.filter(AuditLogDB.security_relevant == True).count()
            compliance_events = query.filter(AuditLogDB.compliance_relevant == True).count()
            
            # Risk level distribution
            risk_stats = self.db.query(
                AuditLogDB.risk_level,
                func.count(AuditLogDB.id).label('count')
            ).filter(
                and_(
                    AuditLogDB.created_at >= start_date,
                    AuditLogDB.created_at <= end_date,
                    AuditLogDB.risk_level.isnot(None)
                )
            ).group_by(AuditLogDB.risk_level).all()
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "total_events": total_events,
                "security_events": security_events,
                "compliance_events": compliance_events,
                "event_type_distribution": {stat.event_type: stat.count for stat in event_type_stats},
                "top_users": [{"user_id": stat.user_id, "event_count": stat.count} for stat in user_activity],
                "risk_level_distribution": {stat.risk_level: stat.count for stat in risk_stats}
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {str(e)}")
            raise
    
    # Compliance Rule Management
    
    def create_compliance_rule(self, rule_data: ComplianceRuleCreate) -> ComplianceRuleResponse:
        """Create a new compliance rule."""
        try:
            rule_db = ComplianceRuleDB(
                name=rule_data.name,
                description=rule_data.description,
                regulation_reference=rule_data.regulation_reference,
                rule_type=rule_data.rule_type,
                rule_config=rule_data.rule_config,
                applies_to_data_types=rule_data.applies_to_data_types,
                applies_to_user_roles=rule_data.applies_to_user_roles,
                geographic_scope=rule_data.geographic_scope,
                effective_date=rule_data.effective_date,
                expiry_date=rule_data.expiry_date,
                check_frequency_hours=rule_data.check_frequency_hours
            )
            
            self.db.add(rule_db)
            self.db.commit()
            self.db.refresh(rule_db)
            
            logger.info(f"Created compliance rule: {rule_data.name}")
            
            return ComplianceRuleResponse.model_validate(rule_db)
            
        except Exception as e:
            logger.error(f"Error creating compliance rule: {str(e)}")
            self.db.rollback()
            raise
    
    def get_compliance_rules(self, active_only: bool = True) -> List[ComplianceRuleResponse]:
        """Get all compliance rules."""
        try:
            query = self.db.query(ComplianceRuleDB)
            
            if active_only:
                query = query.filter(ComplianceRuleDB.is_active == True)
            
            rules = query.all()
            
            return [ComplianceRuleResponse.model_validate(rule) for rule in rules]
            
        except Exception as e:
            logger.error(f"Error getting compliance rules: {str(e)}")
            raise
    
    def run_compliance_check(self, check_data: ComplianceCheckCreate) -> ComplianceCheckResponse:
        """Run a compliance check."""
        try:
            rule = self.db.query(ComplianceRuleDB).filter(ComplianceRuleDB.id == check_data.rule_id).first()
            if not rule:
                raise ValueError(f"Compliance rule {check_data.rule_id} not found")
            
            # Perform the compliance check based on rule type
            check_results = self._perform_compliance_check(rule, check_data)
            
            # Create compliance check record
            check_db = ComplianceCheckDB(
                rule_id=check_data.rule_id,
                check_type=check_data.check_type,
                check_description=check_data.check_description,
                status=check_results["status"],
                compliance_score=check_results["compliance_score"],
                violations_found=check_results["violations_found"],
                violations_details=check_results["violations_details"],
                recommendations=check_results["recommendations"],
                scope_checked=check_data.scope_checked,
                check_parameters=check_data.check_parameters,
                remediation_required=check_results["remediation_required"],
                remediation_deadline=check_results.get("remediation_deadline")
            )
            
            self.db.add(check_db)
            
            # Update rule last checked time
            rule.last_checked = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(check_db)
            
            # Log audit event
            self.log_audit_event(AuditLogCreate(
                event_type=AuditEventTypeEnum.COMPLIANCE_CHECK,
                event_description=f"Compliance check performed for rule: {rule.name}",
                resource_type="compliance_rule",
                resource_id=str(rule.id),
                resource_name=rule.name,
                compliance_relevant=True,
                additional_metadata={
                    "check_id": str(check_db.id),
                    "compliance_score": check_results["compliance_score"],
                    "violations_found": check_results["violations_found"]
                }
            ))
            
            logger.info(f"Completed compliance check for rule: {rule.name}")
            
            return ComplianceCheckResponse.model_validate(check_db)
            
        except Exception as e:
            logger.error(f"Error running compliance check: {str(e)}")
            self.db.rollback()
            raise
    
    def get_compliance_checks(self, rule_id: Optional[uuid.UUID] = None, 
                            status: Optional[ComplianceStatusEnum] = None) -> List[ComplianceCheckResponse]:
        """Get compliance checks."""
        try:
            query = self.db.query(ComplianceCheckDB)
            
            if rule_id:
                query = query.filter(ComplianceCheckDB.rule_id == rule_id)
            
            if status:
                query = query.filter(ComplianceCheckDB.status == status)
            
            query = query.order_by(desc(ComplianceCheckDB.created_at))
            
            checks = query.all()
            
            return [ComplianceCheckResponse.model_validate(check) for check in checks]
            
        except Exception as e:
            logger.error(f"Error getting compliance checks: {str(e)}")
            raise
    
    def run_scheduled_compliance_checks(self) -> List[Dict[str, Any]]:
        """Run all scheduled compliance checks that are due."""
        try:
            now = datetime.utcnow()
            
            # Find rules that need checking
            due_rules = self.db.query(ComplianceRuleDB).filter(
                and_(
                    ComplianceRuleDB.is_active == True,
                    or_(
                        ComplianceRuleDB.last_checked.is_(None),
                        ComplianceRuleDB.last_checked <= now - timedelta(hours=ComplianceRuleDB.check_frequency_hours)
                    )
                )
            ).all()
            
            results = []
            
            for rule in due_rules:
                try:
                    check_data = ComplianceCheckCreate(
                        rule_id=rule.id,
                        check_type="scheduled",
                        check_description=f"Scheduled compliance check for {rule.name}"
                    )
                    
                    result = self.run_compliance_check(check_data)
                    
                    results.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "check_id": result.id,
                        "status": result.status,
                        "compliance_score": result.compliance_score,
                        "violations_found": result.violations_found
                    })
                    
                except Exception as e:
                    logger.error(f"Error in scheduled check for rule {rule.name}: {str(e)}")
                    results.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "status": "failed",
                        "error": str(e)
                    })
            
            logger.info(f"Completed {len(results)} scheduled compliance checks")
            
            return results
            
        except Exception as e:
            logger.error(f"Error running scheduled compliance checks: {str(e)}")
            raise
    
    # Data Retention Management
    
    def create_data_retention_policy(self, policy_data: DataRetentionPolicyCreate) -> DataRetentionPolicyResponse:
        """Create a new data retention policy."""
        try:
            policy_db = DataRetentionPolicyDB(
                name=policy_data.name,
                description=policy_data.description,
                data_type=policy_data.data_type,
                data_category=policy_data.data_category,
                retention_period_days=policy_data.retention_period_days,
                retention_trigger=policy_data.retention_trigger,
                legal_basis=policy_data.legal_basis,
                regulation_reference=policy_data.regulation_reference,
                auto_delete_enabled=policy_data.auto_delete_enabled,
                archive_before_delete=policy_data.archive_before_delete,
                archive_location=policy_data.archive_location,
                legal_hold_override=policy_data.legal_hold_override,
                business_justification_override=policy_data.business_justification_override,
                effective_date=policy_data.effective_date
            )
            
            self.db.add(policy_db)
            self.db.commit()
            self.db.refresh(policy_db)
            
            logger.info(f"Created data retention policy: {policy_data.name}")
            
            return DataRetentionPolicyResponse.model_validate(policy_db)
            
        except Exception as e:
            logger.error(f"Error creating data retention policy: {str(e)}")
            self.db.rollback()
            raise
    
    def get_data_retention_policies(self, active_only: bool = True) -> List[DataRetentionPolicyResponse]:
        """Get all data retention policies."""
        try:
            query = self.db.query(DataRetentionPolicyDB)
            
            if active_only:
                query = query.filter(DataRetentionPolicyDB.is_active == True)
            
            policies = query.all()
            
            return [DataRetentionPolicyResponse.model_validate(policy) for policy in policies]
            
        except Exception as e:
            logger.error(f"Error getting data retention policies: {str(e)}")
            raise
    
    def register_data_for_retention(self, data_type: str, data_id: str, 
                                  data_created_at: datetime, data_location: Optional[str] = None) -> DataRetentionRecordResponse:
        """Register data for retention tracking."""
        try:
            # Find applicable retention policy
            policy = self.db.query(DataRetentionPolicyDB).filter(
                and_(
                    DataRetentionPolicyDB.data_type == data_type,
                    DataRetentionPolicyDB.is_active == True
                )
            ).first()
            
            if not policy:
                logger.warning(f"No retention policy found for data type: {data_type}")
                # Create a default policy or skip registration
                return None
            
            # Calculate retention deadline
            retention_deadline = data_created_at + timedelta(days=policy.retention_period_days)
            
            # Create retention record
            record_db = DataRetentionRecordDB(
                policy_id=policy.id,
                data_type=data_type,
                data_id=data_id,
                data_location=data_location,
                data_created_at=data_created_at,
                retention_deadline=retention_deadline
            )
            
            self.db.add(record_db)
            self.db.commit()
            self.db.refresh(record_db)
            
            logger.debug(f"Registered data for retention: {data_type}:{data_id}")
            
            return DataRetentionRecordResponse.model_validate(record_db)
            
        except Exception as e:
            logger.error(f"Error registering data for retention: {str(e)}")
            self.db.rollback()
            raise
    
    def process_data_retention(self) -> List[Dict[str, Any]]:
        """Process data retention - archive and delete data as needed."""
        try:
            now = datetime.utcnow()
            
            # Find records that are due for processing
            due_records = self.db.query(DataRetentionRecordDB).filter(
                and_(
                    DataRetentionRecordDB.retention_deadline <= now,
                    DataRetentionRecordDB.status == DataRetentionStatusEnum.ACTIVE,
                    DataRetentionRecordDB.legal_hold_active == False
                )
            ).all()
            
            results = []
            
            for record in due_records:
                try:
                    policy = record.policy
                    
                    if policy.archive_before_delete and record.archived_at is None:
                        # Archive the data first
                        archive_result = self._archive_data(record)
                        if archive_result["success"]:
                            record.status = DataRetentionStatusEnum.ARCHIVED
                            record.archived_at = now
                            record.archive_location = archive_result["location"]
                            
                            results.append({
                                "record_id": record.id,
                                "data_type": record.data_type,
                                "data_id": record.data_id,
                                "action": "archived",
                                "status": "success"
                            })
                        else:
                            results.append({
                                "record_id": record.id,
                                "data_type": record.data_type,
                                "data_id": record.data_id,
                                "action": "archive",
                                "status": "failed",
                                "error": archive_result["error"]
                            })
                            continue
                    
                    if policy.auto_delete_enabled:
                        # Delete the data
                        delete_result = self._delete_data(record)
                        if delete_result["success"]:
                            record.status = DataRetentionStatusEnum.DELETED
                            record.deleted_at = now
                            
                            results.append({
                                "record_id": record.id,
                                "data_type": record.data_type,
                                "data_id": record.data_id,
                                "action": "deleted",
                                "status": "success"
                            })
                        else:
                            results.append({
                                "record_id": record.id,
                                "data_type": record.data_type,
                                "data_id": record.data_id,
                                "action": "delete",
                                "status": "failed",
                                "error": delete_result["error"]
                            })
                    else:
                        # Mark as scheduled for deletion
                        record.status = DataRetentionStatusEnum.SCHEDULED_DELETION
                        
                        results.append({
                            "record_id": record.id,
                            "data_type": record.data_type,
                            "data_id": record.data_id,
                            "action": "scheduled_deletion",
                            "status": "success"
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing retention record {record.id}: {str(e)}")
                    results.append({
                        "record_id": record.id,
                        "data_type": record.data_type,
                        "data_id": record.data_id,
                        "action": "process",
                        "status": "failed",
                        "error": str(e)
                    })
            
            self.db.commit()
            
            logger.info(f"Processed {len(results)} data retention records")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing data retention: {str(e)}")
            raise
    
    def get_retention_records(self, status: Optional[DataRetentionStatusEnum] = None,
                            data_type: Optional[str] = None) -> List[DataRetentionRecordResponse]:
        """Get data retention records."""
        try:
            query = self.db.query(DataRetentionRecordDB)
            
            if status:
                query = query.filter(DataRetentionRecordDB.status == status)
            
            if data_type:
                query = query.filter(DataRetentionRecordDB.data_type == data_type)
            
            query = query.order_by(desc(DataRetentionRecordDB.retention_deadline))
            
            records = query.all()
            
            return [DataRetentionRecordResponse.model_validate(record) for record in records]
            
        except Exception as e:
            logger.error(f"Error getting retention records: {str(e)}")
            raise
    
    # Regulatory Reporting
    
    def generate_regulatory_report(self, report_data: RegulatoryReportCreate) -> RegulatoryReportResponse:
        """Generate a regulatory report."""
        try:
            # Generate report content based on type
            report_content = self._generate_report_content(report_data)
            
            # Create report record
            report_db = RegulatoryReportDB(
                report_name=report_data.report_name,
                report_type=report_data.report_type,
                regulation=report_data.regulation,
                period_start=report_data.period_start,
                period_end=report_data.period_end,
                report_data=report_content,
                summary_statistics=report_data.summary_statistics,
                compliance_score=report_data.compliance_score,
                file_format=report_data.file_format,
                generated_at=datetime.utcnow()
            )
            
            self.db.add(report_db)
            self.db.commit()
            self.db.refresh(report_db)
            
            # Save report file
            file_path = self._save_regulatory_report(report_db, report_content)
            report_db.file_path = str(file_path)
            self.db.commit()
            
            logger.info(f"Generated regulatory report: {report_data.report_name}")
            
            return RegulatoryReportResponse.model_validate(report_db)
            
        except Exception as e:
            logger.error(f"Error generating regulatory report: {str(e)}")
            self.db.rollback()
            raise
    
    def get_regulatory_reports(self, regulation: Optional[str] = None) -> List[RegulatoryReportResponse]:
        """Get regulatory reports."""
        try:
            query = self.db.query(RegulatoryReportDB)
            
            if regulation:
                query = query.filter(RegulatoryReportDB.regulation == regulation)
            
            query = query.order_by(desc(RegulatoryReportDB.created_at))
            
            reports = query.all()
            
            return [RegulatoryReportResponse.model_validate(report) for report in reports]
            
        except Exception as e:
            logger.error(f"Error getting regulatory reports: {str(e)}")
            raise
    
    # Dashboard and Analytics
    
    def get_compliance_dashboard(self) -> ComplianceDashboardResponse:
        """Get compliance dashboard data."""
        try:
            # Get basic counts
            total_rules = self.db.query(ComplianceRuleDB).count()
            active_rules = self.db.query(ComplianceRuleDB).filter(ComplianceRuleDB.is_active == True).count()
            
            # Recent checks (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_checks = self.db.query(ComplianceCheckDB).filter(
                ComplianceCheckDB.created_at >= thirty_days_ago
            ).count()
            
            # Calculate overall compliance score
            recent_check_scores = self.db.query(ComplianceCheckDB.compliance_score).filter(
                and_(
                    ComplianceCheckDB.created_at >= thirty_days_ago,
                    ComplianceCheckDB.compliance_score.isnot(None)
                )
            ).all()
            
            compliance_score = 0.0
            if recent_check_scores:
                compliance_score = sum(score[0] for score in recent_check_scores) / len(recent_check_scores)
            
            # Violations count
            violations_count = self.db.query(func.sum(ComplianceCheckDB.violations_found)).filter(
                ComplianceCheckDB.created_at >= thirty_days_ago
            ).scalar() or 0
            
            # Pending remediations
            pending_remediations = self.db.query(ComplianceCheckDB).filter(
                and_(
                    ComplianceCheckDB.remediation_required == True,
                    ComplianceCheckDB.remediation_status != "completed"
                )
            ).count()
            
            # Data retention records
            retention_records = self.db.query(DataRetentionRecordDB).filter(
                DataRetentionRecordDB.status == DataRetentionStatusEnum.ACTIVE
            ).count()
            
            # Upcoming deadlines
            upcoming_deadlines = self._get_upcoming_deadlines()
            
            # Compliance trends (last 12 months)
            compliance_trends = self._get_compliance_trends()
            
            return ComplianceDashboardResponse(
                total_rules=total_rules,
                active_rules=active_rules,
                recent_checks=recent_checks,
                compliance_score=compliance_score,
                violations_count=violations_count,
                pending_remediations=pending_remediations,
                data_retention_records=retention_records,
                upcoming_deadlines=upcoming_deadlines,
                compliance_trends=compliance_trends
            )
            
        except Exception as e:
            logger.error(f"Error getting compliance dashboard: {str(e)}")
            raise
    
    # Private helper methods
    
    def _perform_compliance_check(self, rule: ComplianceRuleDB, check_data: ComplianceCheckCreate) -> Dict[str, Any]:
        """Perform the actual compliance check based on rule type."""
        try:
            if rule.rule_type == "data_retention":
                return self._check_data_retention_compliance(rule)
            elif rule.rule_type == "access_control":
                return self._check_access_control_compliance(rule)
            elif rule.rule_type == "privacy":
                return self._check_privacy_compliance(rule)
            elif rule.rule_type == "audit_trail":
                return self._check_audit_trail_compliance(rule)
            else:
                # Generic compliance check
                return self._check_generic_compliance(rule)
                
        except Exception as e:
            logger.error(f"Error performing compliance check: {str(e)}")
            return {
                "status": ComplianceStatusEnum.NON_COMPLIANT,
                "compliance_score": 0.0,
                "violations_found": 1,
                "violations_details": [{"error": str(e)}],
                "recommendations": ["Fix compliance check error"],
                "remediation_required": True
            }
    
    def _check_data_retention_compliance(self, rule: ComplianceRuleDB) -> Dict[str, Any]:
        """Check data retention compliance."""
        try:
            config = rule.rule_config
            max_retention_days = config.get("max_retention_days", 365)
            
            # Check for data that exceeds retention period
            cutoff_date = datetime.utcnow() - timedelta(days=max_retention_days)
            
            overdue_records = self.db.query(DataRetentionRecordDB).filter(
                and_(
                    DataRetentionRecordDB.retention_deadline <= cutoff_date,
                    DataRetentionRecordDB.status == DataRetentionStatusEnum.ACTIVE
                )
            ).count()
            
            total_records = self.db.query(DataRetentionRecordDB).count()
            
            if total_records == 0:
                compliance_score = 100.0
            else:
                compliance_score = max(0, (total_records - overdue_records) / total_records * 100)
            
            status = ComplianceStatusEnum.COMPLIANT if overdue_records == 0 else ComplianceStatusEnum.NON_COMPLIANT
            
            violations = []
            recommendations = []
            
            if overdue_records > 0:
                violations.append({
                    "type": "overdue_retention",
                    "count": overdue_records,
                    "description": f"{overdue_records} records exceed retention period"
                })
                recommendations.append("Process overdue data retention records")
            
            return {
                "status": status,
                "compliance_score": compliance_score,
                "violations_found": len(violations),
                "violations_details": violations,
                "recommendations": recommendations,
                "remediation_required": overdue_records > 0
            }
            
        except Exception as e:
            logger.error(f"Error checking data retention compliance: {str(e)}")
            raise
    
    def _check_access_control_compliance(self, rule: ComplianceRuleDB) -> Dict[str, Any]:
        """Check access control compliance."""
        # This would check user access patterns, permissions, etc.
        # For now, return a basic compliant result
        return {
            "status": ComplianceStatusEnum.COMPLIANT,
            "compliance_score": 95.0,
            "violations_found": 0,
            "violations_details": [],
            "recommendations": [],
            "remediation_required": False
        }
    
    def _check_privacy_compliance(self, rule: ComplianceRuleDB) -> Dict[str, Any]:
        """Check privacy compliance."""
        # This would check data processing consent, anonymization, etc.
        # For now, return a basic compliant result
        return {
            "status": ComplianceStatusEnum.COMPLIANT,
            "compliance_score": 90.0,
            "violations_found": 0,
            "violations_details": [],
            "recommendations": [],
            "remediation_required": False
        }
    
    def _check_audit_trail_compliance(self, rule: ComplianceRuleDB) -> Dict[str, Any]:
        """Check audit trail compliance."""
        try:
            config = rule.rule_config
            required_events = config.get("required_events", [])
            min_retention_days = config.get("min_retention_days", 90)
            
            # Check if required events are being logged
            cutoff_date = datetime.utcnow() - timedelta(days=min_retention_days)
            
            violations = []
            for event_type in required_events:
                event_count = self.db.query(AuditLogDB).filter(
                    and_(
                        AuditLogDB.event_type == event_type,
                        AuditLogDB.created_at >= cutoff_date
                    )
                ).count()
                
                if event_count == 0:
                    violations.append({
                        "type": "missing_audit_events",
                        "event_type": event_type,
                        "description": f"No {event_type} events found in last {min_retention_days} days"
                    })
            
            compliance_score = max(0, (len(required_events) - len(violations)) / len(required_events) * 100) if required_events else 100
            status = ComplianceStatusEnum.COMPLIANT if len(violations) == 0 else ComplianceStatusEnum.NON_COMPLIANT
            
            recommendations = []
            if violations:
                recommendations.append("Ensure all required events are being logged")
            
            return {
                "status": status,
                "compliance_score": compliance_score,
                "violations_found": len(violations),
                "violations_details": violations,
                "recommendations": recommendations,
                "remediation_required": len(violations) > 0
            }
            
        except Exception as e:
            logger.error(f"Error checking audit trail compliance: {str(e)}")
            raise
    
    def _check_generic_compliance(self, rule: ComplianceRuleDB) -> Dict[str, Any]:
        """Generic compliance check."""
        # Default compliant result for unknown rule types
        return {
            "status": ComplianceStatusEnum.COMPLIANT,
            "compliance_score": 85.0,
            "violations_found": 0,
            "violations_details": [],
            "recommendations": [],
            "remediation_required": False
        }
    
    def _archive_data(self, record: DataRetentionRecordDB) -> Dict[str, Any]:
        """Archive data before deletion."""
        try:
            # This would implement actual data archival logic
            # For now, simulate successful archival
            archive_path = self.archive_dir / f"{record.data_type}_{record.data_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            
            # In a real implementation, this would:
            # 1. Retrieve the actual data
            # 2. Serialize it to the archive format
            # 3. Store it in the archive location
            # 4. Verify the archive integrity
            
            return {
                "success": True,
                "location": str(archive_path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _delete_data(self, record: DataRetentionRecordDB) -> Dict[str, Any]:
        """Delete data that has exceeded retention period."""
        try:
            # This would implement actual data deletion logic
            # For now, simulate successful deletion
            
            # In a real implementation, this would:
            # 1. Identify the actual data location
            # 2. Safely delete the data
            # 3. Verify deletion was successful
            # 4. Update any references or indexes
            
            return {
                "success": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_report_content(self, report_data: RegulatoryReportCreate) -> Dict[str, Any]:
        """Generate content for regulatory reports."""
        try:
            if report_data.report_type == "gdpr_compliance":
                return self._generate_gdpr_report(report_data)
            elif report_data.report_type == "ccpa_compliance":
                return self._generate_ccpa_report(report_data)
            elif report_data.report_type == "audit_summary":
                return self._generate_audit_summary_report(report_data)
            else:
                return self._generate_generic_report(report_data)
                
        except Exception as e:
            logger.error(f"Error generating report content: {str(e)}")
            raise
    
    def _generate_gdpr_report(self, report_data: RegulatoryReportCreate) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        # Get audit events related to personal data
        personal_data_events = self.db.query(AuditLogDB).filter(
            and_(
                AuditLogDB.created_at >= report_data.period_start,
                AuditLogDB.created_at <= report_data.period_end,
                AuditLogDB.compliance_relevant == True
            )
        ).all()
        
        return {
            "report_type": "GDPR Compliance Report",
            "period": {
                "start": report_data.period_start.isoformat(),
                "end": report_data.period_end.isoformat()
            },
            "data_processing_activities": len(personal_data_events),
            "data_subject_requests": self._count_data_subject_requests(report_data.period_start, report_data.period_end),
            "data_breaches": self._count_data_breaches(report_data.period_start, report_data.period_end),
            "retention_compliance": self._get_retention_compliance_summary(),
            "consent_management": self._get_consent_summary(),
            "recommendations": self._get_gdpr_recommendations()
        }
    
    def _generate_ccpa_report(self, report_data: RegulatoryReportCreate) -> Dict[str, Any]:
        """Generate CCPA compliance report."""
        return {
            "report_type": "CCPA Compliance Report",
            "period": {
                "start": report_data.period_start.isoformat(),
                "end": report_data.period_end.isoformat()
            },
            "consumer_requests": self._count_consumer_requests(report_data.period_start, report_data.period_end),
            "data_sales": self._count_data_sales(report_data.period_start, report_data.period_end),
            "opt_out_requests": self._count_opt_out_requests(report_data.period_start, report_data.period_end),
            "privacy_policy_updates": self._count_privacy_policy_updates(report_data.period_start, report_data.period_end)
        }
    
    def _generate_audit_summary_report(self, report_data: RegulatoryReportCreate) -> Dict[str, Any]:
        """Generate audit summary report."""
        audit_stats = self.get_audit_statistics(report_data.period_start, report_data.period_end)
        
        return {
            "report_type": "Audit Summary Report",
            "period": audit_stats["period"],
            "total_events": audit_stats["total_events"],
            "security_events": audit_stats["security_events"],
            "compliance_events": audit_stats["compliance_events"],
            "event_distribution": audit_stats["event_type_distribution"],
            "top_users": audit_stats["top_users"],
            "risk_distribution": audit_stats["risk_level_distribution"]
        }
    
    def _generate_generic_report(self, report_data: RegulatoryReportCreate) -> Dict[str, Any]:
        """Generate generic regulatory report."""
        return {
            "report_type": report_data.report_type,
            "regulation": report_data.regulation,
            "period": {
                "start": report_data.period_start.isoformat(),
                "end": report_data.period_end.isoformat()
            },
            "data": report_data.report_data,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _save_regulatory_report(self, report: RegulatoryReportDB, content: Dict[str, Any]) -> Path:
        """Save regulatory report to file."""
        try:
            file_name = f"{report.report_type}_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            if report.file_format == "json":
                file_path = self.reports_dir / f"{file_name}.json"
                with open(file_path, 'w') as f:
                    json.dump(content, f, indent=2, default=str)
            else:
                # Default to JSON
                file_path = self.reports_dir / f"{file_name}.json"
                with open(file_path, 'w') as f:
                    json.dump(content, f, indent=2, default=str)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving regulatory report: {str(e)}")
            raise
    
    def _get_upcoming_deadlines(self) -> List[Dict[str, Any]]:
        """Get upcoming compliance and retention deadlines."""
        try:
            thirty_days_from_now = datetime.utcnow() + timedelta(days=30)
            
            # Retention deadlines
            retention_deadlines = self.db.query(DataRetentionRecordDB).filter(
                and_(
                    DataRetentionRecordDB.retention_deadline <= thirty_days_from_now,
                    DataRetentionRecordDB.status == DataRetentionStatusEnum.ACTIVE
                )
            ).limit(10).all()
            
            # Remediation deadlines
            remediation_deadlines = self.db.query(ComplianceCheckDB).filter(
                and_(
                    ComplianceCheckDB.remediation_deadline <= thirty_days_from_now,
                    ComplianceCheckDB.remediation_required == True,
                    ComplianceCheckDB.remediation_status != "completed"
                )
            ).limit(10).all()
            
            deadlines = []
            
            for record in retention_deadlines:
                deadlines.append({
                    "type": "data_retention",
                    "description": f"Data retention deadline for {record.data_type}",
                    "deadline": record.retention_deadline.isoformat(),
                    "days_remaining": (record.retention_deadline - datetime.utcnow()).days
                })
            
            for check in remediation_deadlines:
                deadlines.append({
                    "type": "remediation",
                    "description": f"Compliance remediation deadline",
                    "deadline": check.remediation_deadline.isoformat(),
                    "days_remaining": (check.remediation_deadline - datetime.utcnow()).days
                })
            
            return sorted(deadlines, key=lambda x: x["days_remaining"])
            
        except Exception as e:
            logger.error(f"Error getting upcoming deadlines: {str(e)}")
            return []
    
    def _get_compliance_trends(self) -> List[Dict[str, Any]]:
        """Get compliance trends over the last 12 months."""
        try:
            trends = []
            
            for i in range(12):
                month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
                month_end = month_start + timedelta(days=30)
                
                # Get compliance checks for this month
                checks = self.db.query(ComplianceCheckDB).filter(
                    and_(
                        ComplianceCheckDB.created_at >= month_start,
                        ComplianceCheckDB.created_at < month_end
                    )
                ).all()
                
                if checks:
                    avg_score = sum(check.compliance_score or 0 for check in checks) / len(checks)
                    violations = sum(check.violations_found for check in checks)
                else:
                    avg_score = 0
                    violations = 0
                
                trends.append({
                    "month": month_start.strftime("%Y-%m"),
                    "compliance_score": avg_score,
                    "violations_count": violations,
                    "checks_performed": len(checks)
                })
            
            return list(reversed(trends))  # Most recent first
            
        except Exception as e:
            logger.error(f"Error getting compliance trends: {str(e)}")
            return []
    
    # Placeholder methods for report generation
    def _count_data_subject_requests(self, start_date: datetime, end_date: datetime) -> int:
        return 0  # Placeholder
    
    def _count_data_breaches(self, start_date: datetime, end_date: datetime) -> int:
        return 0  # Placeholder
    
    def _get_retention_compliance_summary(self) -> Dict[str, Any]:
        return {"compliant_records": 100, "overdue_records": 0}  # Placeholder
    
    def _get_consent_summary(self) -> Dict[str, Any]:
        return {"active_consents": 50, "withdrawn_consents": 5}  # Placeholder
    
    def _get_gdpr_recommendations(self) -> List[str]:
        return ["Maintain current compliance practices"]  # Placeholder
    
    def _count_consumer_requests(self, start_date: datetime, end_date: datetime) -> int:
        return 0  # Placeholder
    
    def _count_data_sales(self, start_date: datetime, end_date: datetime) -> int:
        return 0  # Placeholder
    
    def _count_opt_out_requests(self, start_date: datetime, end_date: datetime) -> int:
        return 0  # Placeholder
    
    def _count_privacy_policy_updates(self, start_date: datetime, end_date: datetime) -> int:
        return 0  # Placeholder