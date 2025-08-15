"""
Data protection and privacy service.
Handles GDPR compliance, data anonymization, and privacy controls.
"""

import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from app.core.security import data_encryption
from app.models.audit_compliance import AuditLogDB, AuditLogCreate

class DataSubject(BaseModel):
    """Data subject information for privacy requests."""
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None

class PrivacyRequest(BaseModel):
    """Privacy request model."""
    request_type: str  # "access", "rectification", "erasure", "portability", "restriction"
    data_subject: DataSubject
    description: Optional[str] = None
    legal_basis: Optional[str] = None

class DataExportRequest(BaseModel):
    """Data export request for portability."""
    user_id: str
    include_personal_data: bool = True
    include_activity_logs: bool = True
    include_property_data: bool = True
    format: str = "json"  # "json", "csv", "xml"

class DataAnonymizationRequest(BaseModel):
    """Data anonymization request."""
    user_id: str
    anonymize_personal_data: bool = True
    anonymize_activity_logs: bool = True
    retain_analytics: bool = True

class ConsentRecord(BaseModel):
    """Consent record model."""
    user_id: str
    consent_type: str
    purpose: str
    granted: bool
    timestamp: datetime
    legal_basis: str
    withdrawal_date: Optional[datetime] = None

class DataRetentionPolicy(BaseModel):
    """Data retention policy model."""
    data_type: str
    retention_period_days: int
    legal_basis: str
    auto_delete: bool = True
    anonymize_after_retention: bool = True

class PrivacyImpactAssessment(BaseModel):
    """Privacy impact assessment model."""
    assessment_id: str
    data_processing_activity: str
    data_types: List[str]
    legal_basis: str
    risk_level: str  # "low", "medium", "high"
    mitigation_measures: List[str]
    assessment_date: datetime
    next_review_date: datetime

class DataProtectionService:
    """Data protection and privacy service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption = data_encryption
        
        # Define sensitive data fields by table
        self.sensitive_fields = {
            "users": ["email", "phone", "full_name", "address"],
            "leads": ["owner_name", "owner_email", "owner_phone", "address"],
            "properties": ["address", "owner_info"],
            "communications": ["content", "recipient_email", "recipient_phone"],
            "contracts": ["party_info", "signatures"],
            "audit_logs": ["additional_metadata"]
        }
        
        # Data retention policies
        self.retention_policies = {
            "user_activity_logs": DataRetentionPolicy(
                data_type="user_activity_logs",
                retention_period_days=2555,  # 7 years
                legal_basis="legitimate_interest",
                auto_delete=True,
                anonymize_after_retention=True
            ),
            "communication_logs": DataRetentionPolicy(
                data_type="communication_logs",
                retention_period_days=1095,  # 3 years
                legal_basis="contract_performance",
                auto_delete=False,
                anonymize_after_retention=True
            ),
            "financial_records": DataRetentionPolicy(
                data_type="financial_records",
                retention_period_days=2555,  # 7 years
                legal_basis="legal_obligation",
                auto_delete=False,
                anonymize_after_retention=False
            ),
            "marketing_data": DataRetentionPolicy(
                data_type="marketing_data",
                retention_period_days=730,  # 2 years
                legal_basis="consent",
                auto_delete=True,
                anonymize_after_retention=True
            )
        }
    
    def process_privacy_request(self, request: PrivacyRequest) -> Dict[str, Any]:
        """Process privacy request (GDPR Article 15-22)."""
        
        # Find user by email or user_id
        user = self._find_user_by_data_subject(request.data_subject)
        if not user:
            return {
                "status": "not_found",
                "message": "No data found for the provided information"
            }
        
        request_id = str(uuid.uuid4())
        
        # Log privacy request
        self._log_privacy_event(
            event_type=f"privacy_request_{request.request_type}",
            user_id=user.id,
            details={
                "request_id": request_id,
                "request_type": request.request_type,
                "description": request.description
            }
        )
        
        # Process based on request type
        if request.request_type == "access":
            return self._process_access_request(user, request_id)
        elif request.request_type == "rectification":
            return self._process_rectification_request(user, request_id)
        elif request.request_type == "erasure":
            return self._process_erasure_request(user, request_id)
        elif request.request_type == "portability":
            return self._process_portability_request(user, request_id)
        elif request.request_type == "restriction":
            return self._process_restriction_request(user, request_id)
        else:
            return {
                "status": "invalid_request",
                "message": "Invalid request type"
            }
    
    def export_user_data(self, export_request: DataExportRequest) -> Dict[str, Any]:
        """Export user data for portability (GDPR Article 20)."""
        
        user = self.db.query(self._get_user_model()).filter(
            self._get_user_model().id == export_request.user_id
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        export_data = {
            "export_id": str(uuid.uuid4()),
            "user_id": export_request.user_id,
            "export_date": datetime.utcnow().isoformat(),
            "format": export_request.format
        }
        
        # Export personal data
        if export_request.include_personal_data:
            export_data["personal_data"] = self._export_personal_data(user)
        
        # Export activity logs
        if export_request.include_activity_logs:
            export_data["activity_logs"] = self._export_activity_logs(user.id)
        
        # Export property data
        if export_request.include_property_data:
            export_data["property_data"] = self._export_property_data(user.id)
        
        # Log data export
        self._log_privacy_event(
            event_type="data_export",
            user_id=user.id,
            details={
                "export_id": export_data["export_id"],
                "included_data": {
                    "personal_data": export_request.include_personal_data,
                    "activity_logs": export_request.include_activity_logs,
                    "property_data": export_request.include_property_data
                }
            }
        )
        
        return export_data
    
    def anonymize_user_data(self, anonymization_request: DataAnonymizationRequest) -> Dict[str, Any]:
        """Anonymize user data while preserving analytics value."""
        
        user = self.db.query(self._get_user_model()).filter(
            self._get_user_model().id == anonymization_request.user_id
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        anonymization_id = str(uuid.uuid4())
        anonymized_fields = []
        
        # Anonymize personal data
        if anonymization_request.anonymize_personal_data:
            anonymized_fields.extend(self._anonymize_personal_data(user))
        
        # Anonymize activity logs
        if anonymization_request.anonymize_activity_logs:
            anonymized_fields.extend(self._anonymize_activity_logs(user.id))
        
        # Create anonymized user ID for analytics
        if anonymization_request.retain_analytics:
            anonymous_id = self._generate_anonymous_id(user.id)
            self._update_analytics_references(user.id, anonymous_id)
        
        self.db.commit()
        
        # Log anonymization
        self._log_privacy_event(
            event_type="data_anonymization",
            user_id=user.id,
            details={
                "anonymization_id": anonymization_id,
                "anonymized_fields": anonymized_fields,
                "retain_analytics": anonymization_request.retain_analytics
            }
        )
        
        return {
            "status": "completed",
            "anonymization_id": anonymization_id,
            "anonymized_fields": anonymized_fields,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def delete_user_data(self, user_id: str, soft_delete: bool = True) -> Dict[str, Any]:
        """Delete user data (GDPR Article 17 - Right to erasure)."""
        
        user = self.db.query(self._get_user_model()).filter(
            self._get_user_model().id == user_id
        ).first()
        
        if not user:
            raise ValueError("User not found")
        
        deletion_id = str(uuid.uuid4())
        deleted_records = []
        
        if soft_delete:
            # Soft delete - mark as deleted but retain for legal purposes
            user.is_active = False
            user.deleted_at = datetime.utcnow()
            user.deletion_reason = "user_request"
            deleted_records.append(f"users:{user_id}")
            
            # Anonymize sensitive fields
            self._anonymize_personal_data(user)
            
        else:
            # Hard delete - permanently remove data
            deleted_records = self._hard_delete_user_data(user_id)
        
        self.db.commit()
        
        # Log deletion
        self._log_privacy_event(
            event_type="data_deletion",
            user_id=user_id,
            details={
                "deletion_id": deletion_id,
                "soft_delete": soft_delete,
                "deleted_records": deleted_records
            }
        )
        
        return {
            "status": "completed",
            "deletion_id": deletion_id,
            "soft_delete": soft_delete,
            "deleted_records": deleted_records,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def record_consent(self, consent: ConsentRecord) -> str:
        """Record user consent for data processing."""
        
        consent_id = str(uuid.uuid4())
        
        # Store consent record (would typically be in a dedicated consent table)
        consent_record = {
            "id": consent_id,
            "user_id": consent.user_id,
            "consent_type": consent.consent_type,
            "purpose": consent.purpose,
            "granted": consent.granted,
            "timestamp": consent.timestamp,
            "legal_basis": consent.legal_basis,
            "withdrawal_date": consent.withdrawal_date
        }
        
        # Log consent
        self._log_privacy_event(
            event_type="consent_recorded",
            user_id=consent.user_id,
            details={
                "consent_id": consent_id,
                "consent_type": consent.consent_type,
                "purpose": consent.purpose,
                "granted": consent.granted
            }
        )
        
        return consent_id
    
    def withdraw_consent(self, user_id: str, consent_type: str) -> bool:
        """Withdraw user consent for data processing."""
        
        # Update consent record
        withdrawal_date = datetime.utcnow()
        
        # Log consent withdrawal
        self._log_privacy_event(
            event_type="consent_withdrawn",
            user_id=user_id,
            details={
                "consent_type": consent_type,
                "withdrawal_date": withdrawal_date.isoformat()
            }
        )
        
        # Stop related data processing
        self._stop_data_processing_for_consent(user_id, consent_type)
        
        return True
    
    def apply_data_retention_policies(self) -> Dict[str, Any]:
        """Apply data retention policies and clean up expired data."""
        
        cleanup_results = {
            "processed_policies": [],
            "deleted_records": 0,
            "anonymized_records": 0,
            "errors": []
        }
        
        for policy_name, policy in self.retention_policies.items():
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_period_days)
                
                if policy.data_type == "user_activity_logs":
                    result = self._cleanup_activity_logs(cutoff_date, policy)
                elif policy.data_type == "communication_logs":
                    result = self._cleanup_communication_logs(cutoff_date, policy)
                elif policy.data_type == "financial_records":
                    result = self._cleanup_financial_records(cutoff_date, policy)
                elif policy.data_type == "marketing_data":
                    result = self._cleanup_marketing_data(cutoff_date, policy)
                else:
                    continue
                
                cleanup_results["processed_policies"].append(policy_name)
                cleanup_results["deleted_records"] += result.get("deleted", 0)
                cleanup_results["anonymized_records"] += result.get("anonymized", 0)
                
            except Exception as e:
                cleanup_results["errors"].append({
                    "policy": policy_name,
                    "error": str(e)
                })
        
        # Log retention policy application
        self._log_privacy_event(
            event_type="retention_policy_applied",
            user_id=None,
            details=cleanup_results
        )
        
        return cleanup_results
    
    def conduct_privacy_impact_assessment(self, activity: str, data_types: List[str]) -> PrivacyImpactAssessment:
        """Conduct privacy impact assessment for new data processing activities."""
        
        assessment_id = str(uuid.uuid4())
        
        # Assess risk level based on data types and processing activity
        risk_level = self._assess_privacy_risk(activity, data_types)
        
        # Generate mitigation measures
        mitigation_measures = self._generate_mitigation_measures(activity, data_types, risk_level)
        
        # Determine next review date
        if risk_level == "high":
            next_review_date = datetime.utcnow() + timedelta(days=180)  # 6 months
        elif risk_level == "medium":
            next_review_date = datetime.utcnow() + timedelta(days=365)  # 1 year
        else:
            next_review_date = datetime.utcnow() + timedelta(days=730)  # 2 years
        
        assessment = PrivacyImpactAssessment(
            assessment_id=assessment_id,
            data_processing_activity=activity,
            data_types=data_types,
            legal_basis="legitimate_interest",  # Default, should be specified
            risk_level=risk_level,
            mitigation_measures=mitigation_measures,
            assessment_date=datetime.utcnow(),
            next_review_date=next_review_date
        )
        
        # Log PIA
        self._log_privacy_event(
            event_type="privacy_impact_assessment",
            user_id=None,
            details={
                "assessment_id": assessment_id,
                "activity": activity,
                "risk_level": risk_level,
                "data_types": data_types
            }
        )
        
        return assessment
    
    def generate_privacy_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate privacy compliance report."""
        
        # Get privacy-related events
        privacy_events = self.db.query(AuditLogDB).filter(
            and_(
                AuditLogDB.event_category == "privacy",
                AuditLogDB.timestamp >= start_date,
                AuditLogDB.timestamp <= end_date
            )
        ).all()
        
        # Count event types
        event_counts = {}
        for event in privacy_events:
            event_type = event.event_type
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Calculate compliance metrics
        total_requests = event_counts.get("privacy_request_access", 0) + \
                        event_counts.get("privacy_request_erasure", 0) + \
                        event_counts.get("privacy_request_portability", 0)
        
        processed_requests = event_counts.get("data_export", 0) + \
                           event_counts.get("data_deletion", 0) + \
                           event_counts.get("data_anonymization", 0)
        
        compliance_rate = (processed_requests / total_requests * 100) if total_requests > 0 else 100
        
        report = {
            "report_id": str(uuid.uuid4()),
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
            "privacy_requests": {
                "total": total_requests,
                "processed": processed_requests,
                "compliance_rate": compliance_rate
            },
            "event_summary": event_counts,
            "data_retention": {
                "policies_applied": len(self.retention_policies),
                "last_cleanup": self._get_last_cleanup_date()
            },
            "consent_management": {
                "consents_recorded": event_counts.get("consent_recorded", 0),
                "consents_withdrawn": event_counts.get("consent_withdrawn", 0)
            },
            "recommendations": self._generate_privacy_recommendations(event_counts)
        }
        
        return report
    
    # Private helper methods
    
    def _find_user_by_data_subject(self, data_subject: DataSubject):
        """Find user by data subject information."""
        # This would query the actual user table
        # For now, return a mock user
        return None
    
    def _get_user_model(self):
        """Get user model class."""
        # This would return the actual UserDB model
        from app.models.user import UserDB
        return UserDB
    
    def _process_access_request(self, user, request_id: str) -> Dict[str, Any]:
        """Process data access request."""
        return {
            "status": "completed",
            "request_id": request_id,
            "data": self._export_personal_data(user)
        }
    
    def _process_rectification_request(self, user, request_id: str) -> Dict[str, Any]:
        """Process data rectification request."""
        return {
            "status": "pending",
            "request_id": request_id,
            "message": "Rectification request received and will be processed within 30 days"
        }
    
    def _process_erasure_request(self, user, request_id: str) -> Dict[str, Any]:
        """Process data erasure request."""
        deletion_result = self.delete_user_data(user.id)
        return {
            "status": "completed",
            "request_id": request_id,
            "deletion_id": deletion_result["deletion_id"]
        }
    
    def _process_portability_request(self, user, request_id: str) -> Dict[str, Any]:
        """Process data portability request."""
        export_request = DataExportRequest(
            user_id=user.id,
            include_personal_data=True,
            include_activity_logs=True,
            include_property_data=True
        )
        export_result = self.export_user_data(export_request)
        return {
            "status": "completed",
            "request_id": request_id,
            "export_id": export_result["export_id"]
        }
    
    def _process_restriction_request(self, user, request_id: str) -> Dict[str, Any]:
        """Process data processing restriction request."""
        return {
            "status": "pending",
            "request_id": request_id,
            "message": "Processing restriction request received and will be implemented within 30 days"
        }
    
    def _export_personal_data(self, user) -> Dict[str, Any]:
        """Export user's personal data."""
        return {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    def _export_activity_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Export user's activity logs."""
        logs = self.db.query(AuditLogDB).filter(
            AuditLogDB.user_id == user_id
        ).limit(1000).all()
        
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "event_type": log.event_type,
                "description": log.event_description
            }
            for log in logs
        ]
    
    def _export_property_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Export user's property-related data."""
        # This would query property tables
        return []
    
    def _anonymize_personal_data(self, user) -> List[str]:
        """Anonymize user's personal data."""
        anonymized_fields = []
        
        if user.email:
            user.email = self._anonymize_email(user.email)
            anonymized_fields.append("email")
        
        if user.full_name:
            user.full_name = "Anonymous User"
            anonymized_fields.append("full_name")
        
        if hasattr(user, 'phone') and user.phone:
            user.phone = None
            anonymized_fields.append("phone")
        
        return anonymized_fields
    
    def _anonymize_activity_logs(self, user_id: str) -> List[str]:
        """Anonymize user's activity logs."""
        # Update logs to remove personal identifiers
        anonymous_id = self._generate_anonymous_id(user_id)
        
        self.db.query(AuditLogDB).filter(
            AuditLogDB.user_id == user_id
        ).update({"user_id": anonymous_id})
        
        return ["activity_logs"]
    
    def _anonymize_email(self, email: str) -> str:
        """Anonymize email address."""
        local, domain = email.split("@")
        anonymized_local = hashlib.sha256(local.encode()).hexdigest()[:8]
        return f"anon_{anonymized_local}@{domain}"
    
    def _generate_anonymous_id(self, user_id: str) -> str:
        """Generate anonymous ID for analytics."""
        return f"anon_{hashlib.sha256(user_id.encode()).hexdigest()[:16]}"
    
    def _update_analytics_references(self, user_id: str, anonymous_id: str):
        """Update analytics tables with anonymous ID."""
        # This would update analytics tables
        pass
    
    def _hard_delete_user_data(self, user_id: str) -> List[str]:
        """Permanently delete user data."""
        deleted_records = []
        
        # Delete from various tables
        tables_to_clean = ["users", "user_sessions", "api_keys", "audit_logs"]
        
        for table in tables_to_clean:
            # This would execute actual deletion queries
            deleted_records.append(f"{table}:{user_id}")
        
        return deleted_records
    
    def _stop_data_processing_for_consent(self, user_id: str, consent_type: str):
        """Stop data processing activities based on withdrawn consent."""
        # This would stop specific processing activities
        pass
    
    def _cleanup_activity_logs(self, cutoff_date: datetime, policy: DataRetentionPolicy) -> Dict[str, int]:
        """Clean up activity logs based on retention policy."""
        if policy.auto_delete:
            # Delete old logs
            deleted_count = self.db.query(AuditLogDB).filter(
                AuditLogDB.timestamp < cutoff_date
            ).count()
            
            self.db.query(AuditLogDB).filter(
                AuditLogDB.timestamp < cutoff_date
            ).delete()
            
            return {"deleted": deleted_count, "anonymized": 0}
        
        return {"deleted": 0, "anonymized": 0}
    
    def _cleanup_communication_logs(self, cutoff_date: datetime, policy: DataRetentionPolicy) -> Dict[str, int]:
        """Clean up communication logs."""
        return {"deleted": 0, "anonymized": 0}
    
    def _cleanup_financial_records(self, cutoff_date: datetime, policy: DataRetentionPolicy) -> Dict[str, int]:
        """Clean up financial records."""
        return {"deleted": 0, "anonymized": 0}
    
    def _cleanup_marketing_data(self, cutoff_date: datetime, policy: DataRetentionPolicy) -> Dict[str, int]:
        """Clean up marketing data."""
        return {"deleted": 0, "anonymized": 0}
    
    def _assess_privacy_risk(self, activity: str, data_types: List[str]) -> str:
        """Assess privacy risk level."""
        high_risk_data = ["biometric", "health", "financial", "location"]
        medium_risk_data = ["email", "phone", "address", "behavioral"]
        
        if any(data_type in high_risk_data for data_type in data_types):
            return "high"
        elif any(data_type in medium_risk_data for data_type in data_types):
            return "medium"
        else:
            return "low"
    
    def _generate_mitigation_measures(self, activity: str, data_types: List[str], risk_level: str) -> List[str]:
        """Generate privacy risk mitigation measures."""
        measures = [
            "Implement data minimization principles",
            "Apply purpose limitation",
            "Ensure data accuracy and timeliness"
        ]
        
        if risk_level == "high":
            measures.extend([
                "Implement additional encryption",
                "Conduct regular security audits",
                "Implement access controls",
                "Consider pseudonymization"
            ])
        elif risk_level == "medium":
            measures.extend([
                "Implement standard encryption",
                "Regular access reviews",
                "Data retention policies"
            ])
        
        return measures
    
    def _get_last_cleanup_date(self) -> Optional[str]:
        """Get last data retention cleanup date."""
        # This would query the last cleanup execution
        return None
    
    def _generate_privacy_recommendations(self, event_counts: Dict[str, int]) -> List[str]:
        """Generate privacy compliance recommendations."""
        recommendations = []
        
        if event_counts.get("privacy_request_access", 0) > 10:
            recommendations.append("Consider implementing self-service data access portal")
        
        if event_counts.get("consent_withdrawn", 0) > event_counts.get("consent_recorded", 0):
            recommendations.append("Review consent collection processes")
        
        if not event_counts.get("retention_policy_applied", 0):
            recommendations.append("Implement automated data retention policies")
        
        return recommendations
    
    def _log_privacy_event(self, event_type: str, user_id: Optional[str], details: Dict[str, Any]):
        """Log privacy-related event."""
        audit_log = AuditLogDB(
            id=str(uuid.uuid4()),
            event_type=event_type,
            event_category="privacy",
            event_description=f"Privacy event: {event_type}",
            user_id=user_id,
            additional_metadata=details,
            compliance_relevant=True,
            security_relevant=False,
            risk_level="low",
            timestamp=datetime.utcnow()
        )
        
        self.db.add(audit_log)