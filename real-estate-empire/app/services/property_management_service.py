"""
Property Management Service for the Real Estate Empire platform.

This service handles maintenance tracking automation, expense management and categorization,
tenant management integration, and property inspection scheduling.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging
from enum import Enum
from dataclasses import dataclass

from app.models.portfolio import PortfolioPropertyDB
from app.models.property import PropertyDB
from app.core.database import get_db

logger = logging.getLogger(__name__)


class MaintenanceStatusEnum(str, Enum):
    """Enum for maintenance request status."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenancePriorityEnum(str, Enum):
    """Enum for maintenance priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class ExpenseCategoryEnum(str, Enum):
    """Enum for expense categories."""
    MAINTENANCE = "maintenance"
    REPAIRS = "repairs"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    PROPERTY_TAXES = "property_taxes"
    PROPERTY_MANAGEMENT = "property_management"
    MARKETING = "marketing"
    LEGAL = "legal"
    ACCOUNTING = "accounting"
    SUPPLIES = "supplies"
    LANDSCAPING = "landscaping"
    CLEANING = "cleaning"
    OTHER = "other"


class TenantStatusEnum(str, Enum):
    """Enum for tenant status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EVICTED = "evicted"


class InspectionTypeEnum(str, Enum):
    """Enum for inspection types."""
    MOVE_IN = "move_in"
    MOVE_OUT = "move_out"
    ROUTINE = "routine"
    MAINTENANCE = "maintenance"
    ANNUAL = "annual"
    EMERGENCY = "emergency"


@dataclass
class MaintenanceRequest:
    """Data class for maintenance requests."""
    id: uuid.UUID
    property_id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    title: str
    description: str
    category: str
    priority: MaintenancePriorityEnum
    status: MaintenanceStatusEnum
    requested_date: datetime
    scheduled_date: Optional[datetime]
    completed_date: Optional[datetime]
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    vendor_id: Optional[uuid.UUID]
    vendor_name: Optional[str]
    notes: Optional[str]
    photos: List[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class ExpenseRecord:
    """Data class for expense records."""
    id: uuid.UUID
    property_id: uuid.UUID
    category: ExpenseCategoryEnum
    subcategory: Optional[str]
    description: str
    amount: float
    date: datetime
    vendor_name: Optional[str]
    receipt_url: Optional[str]
    maintenance_request_id: Optional[uuid.UUID]
    is_recurring: bool
    recurring_frequency: Optional[str]
    tax_deductible: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class TenantRecord:
    """Data class for tenant records."""
    id: uuid.UUID
    property_id: uuid.UUID
    first_name: str
    last_name: str
    email: Optional[str]
    phone: Optional[str]
    emergency_contact: Optional[Dict[str, str]]
    lease_start_date: datetime
    lease_end_date: datetime
    monthly_rent: float
    security_deposit: float
    status: TenantStatusEnum
    move_in_date: Optional[datetime]
    move_out_date: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class PropertyInspection:
    """Data class for property inspections."""
    id: uuid.UUID
    property_id: uuid.UUID
    inspector_name: str
    inspection_type: InspectionTypeEnum
    scheduled_date: datetime
    completed_date: Optional[datetime]
    status: str
    findings: List[Dict[str, Any]]
    photos: List[str]
    report_url: Optional[str]
    follow_up_required: bool
    follow_up_items: List[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class PropertyManagementService:
    """Service for property management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Maintenance Tracking Methods
    
    def create_maintenance_request(self, property_id: uuid.UUID, request_data: Dict[str, Any]) -> MaintenanceRequest:
        """Create a new maintenance request."""
        try:
            # Validate property exists
            property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
            if not property_obj:
                raise ValueError(f"Property {property_id} not found")
            
            # Determine priority based on category and description
            priority = self._determine_maintenance_priority(
                request_data.get('category', ''),
                request_data.get('description', '')
            )
            
            maintenance_request = MaintenanceRequest(
                id=uuid.uuid4(),
                property_id=property_id,
                tenant_id=request_data.get('tenant_id'),
                title=request_data['title'],
                description=request_data['description'],
                category=request_data.get('category', 'general'),
                priority=priority,
                status=MaintenanceStatusEnum.PENDING,
                requested_date=datetime.now(),
                scheduled_date=request_data.get('scheduled_date'),
                completed_date=None,
                estimated_cost=request_data.get('estimated_cost'),
                actual_cost=None,
                vendor_id=request_data.get('vendor_id'),
                vendor_name=request_data.get('vendor_name'),
                notes=request_data.get('notes'),
                photos=request_data.get('photos', []),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store in database (simplified - would use actual DB model)
            logger.info(f"Created maintenance request {maintenance_request.id} for property {property_id}")
            return maintenance_request
            
        except Exception as e:
            logger.error(f"Error creating maintenance request: {str(e)}")
            raise
    
    def _determine_maintenance_priority(self, category: str, description: str) -> MaintenancePriorityEnum:
        """Determine maintenance priority based on category and description."""
        emergency_keywords = ['leak', 'flood', 'fire', 'gas', 'electrical', 'emergency', 'urgent']
        high_keywords = ['hvac', 'heating', 'cooling', 'plumbing', 'security']
        
        description_lower = description.lower()
        category_lower = category.lower()
        
        # Check for emergency keywords
        if any(keyword in description_lower or keyword in category_lower for keyword in emergency_keywords):
            return MaintenancePriorityEnum.EMERGENCY
        
        # Check for high priority keywords
        if any(keyword in description_lower or keyword in category_lower for keyword in high_keywords):
            return MaintenancePriorityEnum.HIGH
        
        # Default to medium priority
        return MaintenancePriorityEnum.MEDIUM
    
    def update_maintenance_request(self, request_id: uuid.UUID, update_data: Dict[str, Any]) -> MaintenanceRequest:
        """Update a maintenance request."""
        try:
            # In a real implementation, this would fetch from database
            # For now, create a mock updated request
            maintenance_request = MaintenanceRequest(
                id=request_id,
                property_id=update_data.get('property_id', uuid.uuid4()),
                tenant_id=update_data.get('tenant_id'),
                title=update_data.get('title', 'Updated Request'),
                description=update_data.get('description', 'Updated description'),
                category=update_data.get('category', 'general'),
                priority=MaintenancePriorityEnum(update_data.get('priority', 'medium')),
                status=MaintenanceStatusEnum(update_data.get('status', 'pending')),
                requested_date=update_data.get('requested_date', datetime.now()),
                scheduled_date=update_data.get('scheduled_date'),
                completed_date=update_data.get('completed_date'),
                estimated_cost=update_data.get('estimated_cost'),
                actual_cost=update_data.get('actual_cost'),
                vendor_id=update_data.get('vendor_id'),
                vendor_name=update_data.get('vendor_name'),
                notes=update_data.get('notes'),
                photos=update_data.get('photos', []),
                created_at=update_data.get('created_at', datetime.now()),
                updated_at=datetime.now()
            )
            
            logger.info(f"Updated maintenance request {request_id}")
            return maintenance_request
            
        except Exception as e:
            logger.error(f"Error updating maintenance request {request_id}: {str(e)}")
            raise
    
    def get_maintenance_requests(self, property_id: Optional[uuid.UUID] = None, 
                               status: Optional[MaintenanceStatusEnum] = None) -> List[MaintenanceRequest]:
        """Get maintenance requests with optional filters."""
        try:
            # Mock data for demonstration
            requests = []
            
            # In a real implementation, this would query the database
            if property_id:
                # Filter by property
                pass
            
            if status:
                # Filter by status
                pass
            
            logger.info(f"Retrieved {len(requests)} maintenance requests")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting maintenance requests: {str(e)}")
            raise
    
    def schedule_maintenance(self, request_id: uuid.UUID, scheduled_date: datetime, 
                           vendor_id: Optional[uuid.UUID] = None) -> MaintenanceRequest:
        """Schedule a maintenance request."""
        try:
            update_data = {
                'status': MaintenanceStatusEnum.SCHEDULED.value,
                'scheduled_date': scheduled_date,
                'vendor_id': vendor_id
            }
            
            return self.update_maintenance_request(request_id, update_data)
            
        except Exception as e:
            logger.error(f"Error scheduling maintenance request {request_id}: {str(e)}")
            raise
    
    # Expense Management Methods
    
    def record_expense(self, property_id: uuid.UUID, expense_data: Dict[str, Any]) -> ExpenseRecord:
        """Record a property expense."""
        try:
            # Validate property exists
            property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
            if not property_obj:
                raise ValueError(f"Property {property_id} not found")
            
            # Auto-categorize expense if not provided
            category = expense_data.get('category')
            if not category:
                category = self._auto_categorize_expense(
                    expense_data.get('description', ''),
                    expense_data.get('vendor_name', '')
                )
            
            expense_record = ExpenseRecord(
                id=uuid.uuid4(),
                property_id=property_id,
                category=ExpenseCategoryEnum(category),
                subcategory=expense_data.get('subcategory'),
                description=expense_data['description'],
                amount=expense_data['amount'],
                date=expense_data.get('date', datetime.now()),
                vendor_name=expense_data.get('vendor_name'),
                receipt_url=expense_data.get('receipt_url'),
                maintenance_request_id=expense_data.get('maintenance_request_id'),
                is_recurring=expense_data.get('is_recurring', False),
                recurring_frequency=expense_data.get('recurring_frequency'),
                tax_deductible=expense_data.get('tax_deductible', True),
                notes=expense_data.get('notes'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"Recorded expense {expense_record.id} for property {property_id}")
            return expense_record
            
        except Exception as e:
            logger.error(f"Error recording expense: {str(e)}")
            raise
    
    def _auto_categorize_expense(self, description: str, vendor_name: str) -> str:
        """Auto-categorize expense based on description and vendor."""
        description_lower = description.lower()
        vendor_lower = vendor_name.lower() if vendor_name else ''
        
        # Maintenance and repairs
        if any(keyword in description_lower for keyword in ['repair', 'fix', 'maintenance', 'plumbing', 'electrical']):
            return ExpenseCategoryEnum.MAINTENANCE.value
        
        # Utilities
        if any(keyword in description_lower or keyword in vendor_lower 
               for keyword in ['electric', 'gas', 'water', 'utility', 'power']):
            return ExpenseCategoryEnum.UTILITIES.value
        
        # Insurance
        if any(keyword in description_lower or keyword in vendor_lower 
               for keyword in ['insurance', 'policy', 'premium']):
            return ExpenseCategoryEnum.INSURANCE.value
        
        # Property taxes
        if any(keyword in description_lower for keyword in ['tax', 'assessment', 'county', 'city']):
            return ExpenseCategoryEnum.PROPERTY_TAXES.value
        
        # Landscaping
        if any(keyword in description_lower for keyword in ['lawn', 'landscape', 'garden', 'tree', 'grass']):
            return ExpenseCategoryEnum.LANDSCAPING.value
        
        # Default to other
        return ExpenseCategoryEnum.OTHER.value
    
    def get_expenses(self, property_id: Optional[uuid.UUID] = None, 
                    category: Optional[ExpenseCategoryEnum] = None,
                    start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> List[ExpenseRecord]:
        """Get expense records with optional filters."""
        try:
            # Mock implementation
            expenses = []
            
            logger.info(f"Retrieved {len(expenses)} expense records")
            return expenses
            
        except Exception as e:
            logger.error(f"Error getting expenses: {str(e)}")
            raise
    
    def categorize_expenses_bulk(self, property_id: uuid.UUID) -> Dict[str, Any]:
        """Bulk categorize uncategorized expenses for a property."""
        try:
            # Get uncategorized expenses
            expenses = self.get_expenses(property_id=property_id)
            
            categorized_count = 0
            for expense in expenses:
                if expense.category == ExpenseCategoryEnum.OTHER:
                    new_category = self._auto_categorize_expense(expense.description, expense.vendor_name or '')
                    if new_category != ExpenseCategoryEnum.OTHER.value:
                        # Update expense category
                        categorized_count += 1
            
            logger.info(f"Bulk categorized {categorized_count} expenses for property {property_id}")
            return {
                'total_expenses': len(expenses),
                'categorized_count': categorized_count,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error bulk categorizing expenses: {str(e)}")
            raise
    
    # Tenant Management Methods
    
    def add_tenant(self, property_id: uuid.UUID, tenant_data: Dict[str, Any]) -> TenantRecord:
        """Add a new tenant to a property."""
        try:
            # Validate property exists
            property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
            if not property_obj:
                raise ValueError(f"Property {property_id} not found")
            
            tenant_record = TenantRecord(
                id=uuid.uuid4(),
                property_id=property_id,
                first_name=tenant_data['first_name'],
                last_name=tenant_data['last_name'],
                email=tenant_data.get('email'),
                phone=tenant_data.get('phone'),
                emergency_contact=tenant_data.get('emergency_contact'),
                lease_start_date=tenant_data['lease_start_date'],
                lease_end_date=tenant_data['lease_end_date'],
                monthly_rent=tenant_data['monthly_rent'],
                security_deposit=tenant_data.get('security_deposit', 0.0),
                status=TenantStatusEnum.PENDING,
                move_in_date=tenant_data.get('move_in_date'),
                move_out_date=None,
                notes=tenant_data.get('notes'),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"Added tenant {tenant_record.id} to property {property_id}")
            return tenant_record
            
        except Exception as e:
            logger.error(f"Error adding tenant: {str(e)}")
            raise
    
    def update_tenant(self, tenant_id: uuid.UUID, update_data: Dict[str, Any]) -> TenantRecord:
        """Update tenant information."""
        try:
            # Mock implementation - would fetch and update from database
            tenant_record = TenantRecord(
                id=tenant_id,
                property_id=update_data.get('property_id', uuid.uuid4()),
                first_name=update_data.get('first_name', 'John'),
                last_name=update_data.get('last_name', 'Doe'),
                email=update_data.get('email'),
                phone=update_data.get('phone'),
                emergency_contact=update_data.get('emergency_contact'),
                lease_start_date=update_data.get('lease_start_date', datetime.now()),
                lease_end_date=update_data.get('lease_end_date', datetime.now() + timedelta(days=365)),
                monthly_rent=update_data.get('monthly_rent', 1000.0),
                security_deposit=update_data.get('security_deposit', 1000.0),
                status=TenantStatusEnum(update_data.get('status', 'active')),
                move_in_date=update_data.get('move_in_date'),
                move_out_date=update_data.get('move_out_date'),
                notes=update_data.get('notes'),
                created_at=update_data.get('created_at', datetime.now()),
                updated_at=datetime.now()
            )
            
            logger.info(f"Updated tenant {tenant_id}")
            return tenant_record
            
        except Exception as e:
            logger.error(f"Error updating tenant {tenant_id}: {str(e)}")
            raise
    
    def get_tenants(self, property_id: Optional[uuid.UUID] = None, 
                   status: Optional[TenantStatusEnum] = None) -> List[TenantRecord]:
        """Get tenant records with optional filters."""
        try:
            # Mock implementation
            tenants = []
            
            logger.info(f"Retrieved {len(tenants)} tenant records")
            return tenants
            
        except Exception as e:
            logger.error(f"Error getting tenants: {str(e)}")
            raise
    
    def process_tenant_move_in(self, tenant_id: uuid.UUID, move_in_date: datetime) -> Dict[str, Any]:
        """Process tenant move-in."""
        try:
            # Update tenant status
            update_data = {
                'status': TenantStatusEnum.ACTIVE.value,
                'move_in_date': move_in_date
            }
            tenant = self.update_tenant(tenant_id, update_data)
            
            # Schedule move-in inspection
            inspection = self.schedule_inspection(
                property_id=tenant.property_id,
                inspection_type=InspectionTypeEnum.MOVE_IN,
                scheduled_date=move_in_date,
                inspector_name="Property Manager"
            )
            
            logger.info(f"Processed move-in for tenant {tenant_id}")
            return {
                'tenant': tenant,
                'inspection': inspection,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error processing tenant move-in: {str(e)}")
            raise
    
    def process_tenant_move_out(self, tenant_id: uuid.UUID, move_out_date: datetime) -> Dict[str, Any]:
        """Process tenant move-out."""
        try:
            # Update tenant status
            update_data = {
                'status': TenantStatusEnum.INACTIVE.value,
                'move_out_date': move_out_date
            }
            tenant = self.update_tenant(tenant_id, update_data)
            
            # Schedule move-out inspection
            inspection = self.schedule_inspection(
                property_id=tenant.property_id,
                inspection_type=InspectionTypeEnum.MOVE_OUT,
                scheduled_date=move_out_date,
                inspector_name="Property Manager"
            )
            
            logger.info(f"Processed move-out for tenant {tenant_id}")
            return {
                'tenant': tenant,
                'inspection': inspection,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error processing tenant move-out: {str(e)}")
            raise
    
    # Property Inspection Methods
    
    def schedule_inspection(self, property_id: uuid.UUID, inspection_type: InspectionTypeEnum,
                          scheduled_date: datetime, inspector_name: str) -> PropertyInspection:
        """Schedule a property inspection."""
        try:
            # Validate property exists
            property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == property_id).first()
            if not property_obj:
                raise ValueError(f"Property {property_id} not found")
            
            inspection = PropertyInspection(
                id=uuid.uuid4(),
                property_id=property_id,
                inspector_name=inspector_name,
                inspection_type=inspection_type,
                scheduled_date=scheduled_date,
                completed_date=None,
                status="scheduled",
                findings=[],
                photos=[],
                report_url=None,
                follow_up_required=False,
                follow_up_items=[],
                notes=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"Scheduled {inspection_type.value} inspection {inspection.id} for property {property_id}")
            return inspection
            
        except Exception as e:
            logger.error(f"Error scheduling inspection: {str(e)}")
            raise
    
    def complete_inspection(self, inspection_id: uuid.UUID, 
                          findings: List[Dict[str, Any]], photos: List[str]) -> PropertyInspection:
        """Complete a property inspection."""
        try:
            # Mock implementation - would fetch and update from database
            inspection = PropertyInspection(
                id=inspection_id,
                property_id=uuid.uuid4(),
                inspector_name="Property Manager",
                inspection_type=InspectionTypeEnum.ROUTINE,
                scheduled_date=datetime.now(),
                completed_date=datetime.now(),
                status="completed",
                findings=findings,
                photos=photos,
                report_url=None,
                follow_up_required=len(findings) > 0,
                follow_up_items=[finding.get('description', '') for finding in findings if finding.get('severity') == 'high'],
                notes=None,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Create maintenance requests for high-priority findings
            for finding in findings:
                if finding.get('severity') == 'high':
                    self.create_maintenance_request(
                        property_id=inspection.property_id,
                        request_data={
                            'title': f"Inspection Finding: {finding.get('title', 'Issue')}",
                            'description': finding.get('description', ''),
                            'category': finding.get('category', 'general'),
                            'priority': 'high'
                        }
                    )
            
            logger.info(f"Completed inspection {inspection_id}")
            return inspection
            
        except Exception as e:
            logger.error(f"Error completing inspection {inspection_id}: {str(e)}")
            raise
    
    def get_inspections(self, property_id: Optional[uuid.UUID] = None,
                       inspection_type: Optional[InspectionTypeEnum] = None) -> List[PropertyInspection]:
        """Get property inspections with optional filters."""
        try:
            # Mock implementation
            inspections = []
            
            logger.info(f"Retrieved {len(inspections)} inspection records")
            return inspections
            
        except Exception as e:
            logger.error(f"Error getting inspections: {str(e)}")
            raise
    
    def schedule_routine_inspections(self, property_id: uuid.UUID) -> List[PropertyInspection]:
        """Schedule routine inspections for a property."""
        try:
            inspections = []
            
            # Schedule quarterly routine inspection
            next_inspection_date = datetime.now() + timedelta(days=90)
            routine_inspection = self.schedule_inspection(
                property_id=property_id,
                inspection_type=InspectionTypeEnum.ROUTINE,
                scheduled_date=next_inspection_date,
                inspector_name="Property Manager"
            )
            inspections.append(routine_inspection)
            
            # Schedule annual inspection
            annual_inspection_date = datetime.now() + timedelta(days=365)
            annual_inspection = self.schedule_inspection(
                property_id=property_id,
                inspection_type=InspectionTypeEnum.ANNUAL,
                scheduled_date=annual_inspection_date,
                inspector_name="Property Manager"
            )
            inspections.append(annual_inspection)
            
            logger.info(f"Scheduled {len(inspections)} routine inspections for property {property_id}")
            return inspections
            
        except Exception as e:
            logger.error(f"Error scheduling routine inspections: {str(e)}")
            raise
    
    # Analytics and Reporting Methods
    
    def get_property_management_dashboard(self, property_id: uuid.UUID) -> Dict[str, Any]:
        """Get property management dashboard data."""
        try:
            # Get maintenance requests
            maintenance_requests = self.get_maintenance_requests(property_id=property_id)
            
            # Get expenses
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            expenses = self.get_expenses(
                property_id=property_id,
                start_date=current_month_start
            )
            
            # Get tenants
            tenants = self.get_tenants(property_id=property_id)
            
            # Get inspections
            inspections = self.get_inspections(property_id=property_id)
            
            # Calculate metrics
            total_expenses = sum(expense.amount for expense in expenses)
            pending_maintenance = len([req for req in maintenance_requests if req.status == MaintenanceStatusEnum.PENDING])
            active_tenants = len([tenant for tenant in tenants if tenant.status == TenantStatusEnum.ACTIVE])
            
            dashboard_data = {
                'property_id': property_id,
                'summary': {
                    'total_monthly_expenses': total_expenses,
                    'pending_maintenance_requests': pending_maintenance,
                    'active_tenants': active_tenants,
                    'upcoming_inspections': len([insp for insp in inspections if insp.scheduled_date > datetime.now()])
                },
                'maintenance_requests': maintenance_requests,
                'recent_expenses': expenses[-10:],  # Last 10 expenses
                'tenants': tenants,
                'upcoming_inspections': [insp for insp in inspections if insp.scheduled_date > datetime.now()][:5]
            }
            
            logger.info(f"Generated property management dashboard for property {property_id}")
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating property management dashboard: {str(e)}")
            raise
    
    def generate_expense_report(self, property_id: uuid.UUID, 
                              start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate expense report for a property."""
        try:
            expenses = self.get_expenses(
                property_id=property_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Group expenses by category
            expenses_by_category = {}
            for expense in expenses:
                category = expense.category.value
                if category not in expenses_by_category:
                    expenses_by_category[category] = []
                expenses_by_category[category].append(expense)
            
            # Calculate totals
            category_totals = {
                category: sum(exp.amount for exp in exps)
                for category, exps in expenses_by_category.items()
            }
            
            total_expenses = sum(category_totals.values())
            
            report = {
                'property_id': property_id,
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'total_expenses': total_expenses,
                'expenses_by_category': expenses_by_category,
                'category_totals': category_totals,
                'expense_count': len(expenses),
                'generated_at': datetime.now()
            }
            
            logger.info(f"Generated expense report for property {property_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating expense report: {str(e)}")
            raise


def get_property_management_service(db: Session = None) -> PropertyManagementService:
    """Factory function to get PropertyManagementService instance."""
    if db is None:
        db = next(get_db())
    return PropertyManagementService(db)