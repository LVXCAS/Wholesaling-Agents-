"""
Portfolio Management Service for the Real Estate Empire platform.

This service handles portfolio CRUD operations, property management within portfolios,
and coordination with the performance tracking service.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging

from app.models.portfolio import (
    PortfolioDB, PortfolioPropertyDB, PropertyPerformanceDB, PortfolioPerformanceDB,
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioPropertyCreate, PortfolioPropertyUpdate, PortfolioPropertyResponse,
    PropertyPerformanceCreate, PropertyPerformanceResponse,
    PortfolioSummary, PropertyInvestmentStatusEnum
)
from app.models.property import PropertyDB
from app.core.database import get_db
from app.services.portfolio_performance_service import PortfolioPerformanceService

logger = logging.getLogger(__name__)


class PortfolioManagementService:
    """Service for managing portfolios and their properties."""
    
    def __init__(self, db: Session):
        self.db = db
        self.performance_service = PortfolioPerformanceService(db)
    
    # Portfolio CRUD Operations
    
    def create_portfolio(self, portfolio_data: PortfolioCreate) -> PortfolioResponse:
        """Create a new portfolio."""
        try:
            # Create portfolio record
            portfolio = PortfolioDB(
                name=portfolio_data.name,
                description=portfolio_data.description,
                investment_strategy=portfolio_data.investment_strategy,
                target_markets=portfolio_data.target_markets,
                investment_criteria=portfolio_data.investment_criteria
            )
            
            self.db.add(portfolio)
            self.db.commit()
            self.db.refresh(portfolio)
            
            logger.info(f"Created portfolio: {portfolio.name} (ID: {portfolio.id})")
            return PortfolioResponse.from_orm(portfolio)
            
        except Exception as e:
            logger.error(f"Error creating portfolio: {str(e)}")
            self.db.rollback()
            raise
    
    def get_portfolio(self, portfolio_id: uuid.UUID) -> Optional[PortfolioResponse]:
        """Get a portfolio by ID."""
        try:
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if portfolio:
                return PortfolioResponse.from_orm(portfolio)
            return None
            
        except Exception as e:
            logger.error(f"Error getting portfolio {portfolio_id}: {str(e)}")
            raise
    
    def get_portfolios(self, skip: int = 0, limit: int = 100) -> List[PortfolioResponse]:
        """Get all portfolios with pagination."""
        try:
            portfolios = self.db.query(PortfolioDB).offset(skip).limit(limit).all()
            return [PortfolioResponse.from_orm(portfolio) for portfolio in portfolios]
            
        except Exception as e:
            logger.error(f"Error getting portfolios: {str(e)}")
            raise
    
    def update_portfolio(self, portfolio_id: uuid.UUID, portfolio_data: PortfolioUpdate) -> Optional[PortfolioResponse]:
        """Update a portfolio."""
        try:
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not portfolio:
                return None
            
            # Update fields
            update_data = portfolio_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(portfolio, field, value)
            
            portfolio.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(portfolio)
            
            logger.info(f"Updated portfolio: {portfolio.name} (ID: {portfolio.id})")
            return PortfolioResponse.from_orm(portfolio)
            
        except Exception as e:
            logger.error(f"Error updating portfolio {portfolio_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def delete_portfolio(self, portfolio_id: uuid.UUID) -> bool:
        """Delete a portfolio and all its properties."""
        try:
            # First delete all portfolio properties
            self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).delete()
            
            # Delete performance records
            self.db.query(PortfolioPerformanceDB).filter(
                PortfolioPerformanceDB.portfolio_id == portfolio_id
            ).delete()
            
            # Delete the portfolio
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if portfolio:
                self.db.delete(portfolio)
                self.db.commit()
                logger.info(f"Deleted portfolio: {portfolio.name} (ID: {portfolio.id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting portfolio {portfolio_id}: {str(e)}")
            self.db.rollback()
            raise
    
    # Portfolio Property Management
    
    def add_property_to_portfolio(self, portfolio_id: uuid.UUID, 
                                 property_data: PortfolioPropertyCreate) -> PortfolioPropertyResponse:
        """Add a property to a portfolio."""
        try:
            # Verify portfolio exists
            portfolio = self.db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
            if not portfolio:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            # Verify property exists
            property_obj = self.db.query(PropertyDB).filter(PropertyDB.id == property_data.property_id).first()
            if not property_obj:
                raise ValueError(f"Property {property_data.property_id} not found")
            
            # Check if property is already in portfolio
            existing = self.db.query(PortfolioPropertyDB).filter(
                and_(
                    PortfolioPropertyDB.portfolio_id == portfolio_id,
                    PortfolioPropertyDB.property_id == property_data.property_id
                )
            ).first()
            
            if existing:
                raise ValueError(f"Property {property_data.property_id} is already in portfolio {portfolio_id}")
            
            # Calculate total investment
            total_investment = property_data.acquisition_price + property_data.closing_costs + property_data.rehab_costs
            
            # Calculate initial metrics
            monthly_cash_flow = property_data.monthly_rent - property_data.monthly_expenses
            current_value = property_obj.current_value or property_data.acquisition_price
            current_equity = current_value - 0  # Assuming no debt initially
            
            # Create portfolio property record
            portfolio_property = PortfolioPropertyDB(
                portfolio_id=portfolio_id,
                property_id=property_data.property_id,
                acquisition_date=property_data.acquisition_date,
                acquisition_price=property_data.acquisition_price,
                closing_costs=property_data.closing_costs,
                rehab_costs=property_data.rehab_costs,
                total_investment=total_investment,
                current_value=current_value,
                current_equity=current_equity,
                monthly_rent=property_data.monthly_rent,
                monthly_expenses=property_data.monthly_expenses,
                monthly_cash_flow=monthly_cash_flow,
                property_manager=property_data.property_manager,
                management_fee_percent=property_data.management_fee_percent,
                exit_strategy=property_data.exit_strategy,
                target_exit_date=property_data.target_exit_date,
                target_exit_value=property_data.target_exit_value,
                notes=property_data.notes
            )
            
            # Calculate initial performance metrics
            if current_value > 0:
                annual_cash_flow = monthly_cash_flow * 12
                portfolio_property.cap_rate = (annual_cash_flow / current_value) * 100
                
                cash_invested = total_investment
                if cash_invested > 0:
                    portfolio_property.coc_return = (annual_cash_flow / cash_invested) * 100
                
                if total_investment > 0:
                    portfolio_property.roi = ((current_value - total_investment) / total_investment) * 100
            
            self.db.add(portfolio_property)
            self.db.commit()
            self.db.refresh(portfolio_property)
            
            # Update portfolio metrics
            self.performance_service.update_portfolio_metrics(portfolio_id)
            
            logger.info(f"Added property {property_data.property_id} to portfolio {portfolio_id}")
            return PortfolioPropertyResponse.from_orm(portfolio_property)
            
        except Exception as e:
            logger.error(f"Error adding property to portfolio: {str(e)}")
            self.db.rollback()
            raise
    
    def get_portfolio_properties(self, portfolio_id: uuid.UUID) -> List[PortfolioPropertyResponse]:
        """Get all properties in a portfolio."""
        try:
            properties = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.portfolio_id == portfolio_id
            ).all()
            
            return [PortfolioPropertyResponse.from_orm(prop) for prop in properties]
            
        except Exception as e:
            logger.error(f"Error getting portfolio properties: {str(e)}")
            raise
    
    def get_portfolio_property(self, portfolio_property_id: uuid.UUID) -> Optional[PortfolioPropertyResponse]:
        """Get a specific portfolio property."""
        try:
            portfolio_property = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.id == portfolio_property_id
            ).first()
            
            if portfolio_property:
                return PortfolioPropertyResponse.from_orm(portfolio_property)
            return None
            
        except Exception as e:
            logger.error(f"Error getting portfolio property {portfolio_property_id}: {str(e)}")
            raise
    
    def update_portfolio_property(self, portfolio_property_id: uuid.UUID, 
                                 property_data: PortfolioPropertyUpdate) -> Optional[PortfolioPropertyResponse]:
        """Update a portfolio property."""
        try:
            portfolio_property = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.id == portfolio_property_id
            ).first()
            
            if not portfolio_property:
                return None
            
            # Update fields
            update_data = property_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(portfolio_property, field, value)
            
            # Recalculate metrics if financial data changed
            if any(field in update_data for field in ['monthly_rent', 'monthly_expenses', 'current_value', 'current_debt']):
                self._recalculate_property_metrics(portfolio_property)
            
            portfolio_property.updated_at = datetime.now()
            portfolio_property.last_performance_update = datetime.now()
            
            self.db.commit()
            self.db.refresh(portfolio_property)
            
            # Update portfolio-level metrics
            self.performance_service.update_portfolio_metrics(portfolio_property.portfolio_id)
            
            logger.info(f"Updated portfolio property {portfolio_property_id}")
            return PortfolioPropertyResponse.from_orm(portfolio_property)
            
        except Exception as e:
            logger.error(f"Error updating portfolio property {portfolio_property_id}: {str(e)}")
            self.db.rollback()
            raise
    
    def remove_property_from_portfolio(self, portfolio_property_id: uuid.UUID) -> bool:
        """Remove a property from a portfolio."""
        try:
            # Get the portfolio property
            portfolio_property = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.id == portfolio_property_id
            ).first()
            
            if not portfolio_property:
                return False
            
            portfolio_id = portfolio_property.portfolio_id
            
            # Delete performance records
            self.db.query(PropertyPerformanceDB).filter(
                PropertyPerformanceDB.portfolio_property_id == portfolio_property_id
            ).delete()
            
            # Delete the portfolio property
            self.db.delete(portfolio_property)
            self.db.commit()
            
            # Update portfolio metrics
            self.performance_service.update_portfolio_metrics(portfolio_id)
            
            logger.info(f"Removed property from portfolio: {portfolio_property_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing property from portfolio: {str(e)}")
            self.db.rollback()
            raise
    
    def _recalculate_property_metrics(self, portfolio_property: PortfolioPropertyDB):
        """Recalculate performance metrics for a portfolio property."""
        try:
            # Calculate monthly cash flow
            portfolio_property.monthly_cash_flow = portfolio_property.monthly_rent - portfolio_property.monthly_expenses
            
            # Calculate current equity
            portfolio_property.current_equity = (portfolio_property.current_value or 0) - portfolio_property.current_debt
            
            # Calculate performance metrics
            current_value = portfolio_property.current_value or portfolio_property.total_investment
            annual_cash_flow = portfolio_property.monthly_cash_flow * 12
            
            # Cap Rate
            if current_value > 0:
                portfolio_property.cap_rate = (annual_cash_flow / current_value) * 100
            
            # Cash-on-Cash Return
            cash_invested = portfolio_property.total_investment - portfolio_property.current_debt
            if cash_invested > 0:
                portfolio_property.coc_return = (annual_cash_flow / cash_invested) * 100
            
            # ROI
            if portfolio_property.total_investment > 0:
                portfolio_property.roi = ((current_value - portfolio_property.total_investment) / 
                                        portfolio_property.total_investment) * 100
            
            # Appreciation Rate (annualized)
            if portfolio_property.acquisition_price > 0:
                years_held = (datetime.now() - portfolio_property.acquisition_date).days / 365.25
                if years_held > 0:
                    portfolio_property.appreciation_rate = (((current_value / portfolio_property.acquisition_price) ** 
                                                           (1 / years_held)) - 1) * 100
            
        except Exception as e:
            logger.error(f"Error recalculating property metrics: {str(e)}")
    
    # Performance Data Management
    
    def record_property_performance(self, performance_data: PropertyPerformanceCreate) -> PropertyPerformanceResponse:
        """Record performance data for a property."""
        try:
            # Calculate totals
            total_income = performance_data.rental_income + performance_data.other_income
            total_expenses = (performance_data.mortgage_payment + performance_data.property_taxes + 
                            performance_data.insurance + performance_data.maintenance_repairs + 
                            performance_data.property_management + performance_data.utilities + 
                            performance_data.other_expenses)
            net_cash_flow = total_income - total_expenses
            
            # Create performance record
            performance = PropertyPerformanceDB(
                portfolio_property_id=performance_data.portfolio_property_id,
                period_start=performance_data.period_start,
                period_end=performance_data.period_end,
                period_type=performance_data.period_type,
                rental_income=performance_data.rental_income,
                other_income=performance_data.other_income,
                total_income=total_income,
                mortgage_payment=performance_data.mortgage_payment,
                property_taxes=performance_data.property_taxes,
                insurance=performance_data.insurance,
                maintenance_repairs=performance_data.maintenance_repairs,
                property_management=performance_data.property_management,
                utilities=performance_data.utilities,
                other_expenses=performance_data.other_expenses,
                total_expenses=total_expenses,
                net_cash_flow=net_cash_flow,
                estimated_value=performance_data.estimated_value,
                occupancy_rate=performance_data.occupancy_rate,
                vacancy_days=performance_data.vacancy_days
            )
            
            # Calculate performance metrics
            if performance_data.estimated_value and performance_data.estimated_value > 0:
                # Annualize the cash flow for cap rate calculation
                period_days = (performance_data.period_end - performance_data.period_start).days
                annual_cash_flow = net_cash_flow * (365 / period_days) if period_days > 0 else 0
                performance.cap_rate = (annual_cash_flow / performance_data.estimated_value) * 100
            
            self.db.add(performance)
            self.db.commit()
            self.db.refresh(performance)
            
            # Update portfolio property's last performance update
            portfolio_property = self.db.query(PortfolioPropertyDB).filter(
                PortfolioPropertyDB.id == performance_data.portfolio_property_id
            ).first()
            
            if portfolio_property:
                portfolio_property.last_performance_update = datetime.now()
                # Update portfolio metrics
                self.performance_service.update_portfolio_metrics(portfolio_property.portfolio_id)
            
            self.db.commit()
            
            logger.info(f"Recorded performance for portfolio property {performance_data.portfolio_property_id}")
            return PropertyPerformanceResponse.from_orm(performance)
            
        except Exception as e:
            logger.error(f"Error recording property performance: {str(e)}")
            self.db.rollback()
            raise
    
    def get_property_performance_history(self, portfolio_property_id: uuid.UUID, 
                                       limit: int = 12) -> List[PropertyPerformanceResponse]:
        """Get performance history for a portfolio property."""
        try:
            performance_records = self.db.query(PropertyPerformanceDB).filter(
                PropertyPerformanceDB.portfolio_property_id == portfolio_property_id
            ).order_by(PropertyPerformanceDB.period_start.desc()).limit(limit).all()
            
            return [PropertyPerformanceResponse.from_orm(record) for record in performance_records]
            
        except Exception as e:
            logger.error(f"Error getting property performance history: {str(e)}")
            raise
    
    # Portfolio Summary and Analytics
    
    def get_portfolio_summary(self, portfolio_id: uuid.UUID) -> Optional[PortfolioSummary]:
        """Get a comprehensive portfolio summary."""
        try:
            # Get portfolio
            portfolio = self.get_portfolio(portfolio_id)
            if not portfolio:
                return None
            
            # Get properties
            properties = self.get_portfolio_properties(portfolio_id)
            
            # Get performance metrics
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            performance_metrics = self.performance_service.calculate_portfolio_performance(
                portfolio_id, start_date, end_date
            )
            
            # Get recent performance data
            recent_performance = []
            for prop in properties:
                prop_performance = self.get_property_performance_history(prop.id, limit=3)
                recent_performance.extend(prop_performance)
            
            return PortfolioSummary(
                portfolio=portfolio,
                properties=properties,
                performance_metrics=performance_metrics,
                recent_performance=recent_performance
            )
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {str(e)}")
            raise
    
    def get_portfolio_dashboard_data(self, portfolio_id: uuid.UUID) -> Dict[str, Any]:
        """Get dashboard data for a portfolio."""
        try:
            # Get portfolio summary
            summary = self.get_portfolio_summary(portfolio_id)
            if not summary:
                return {}
            
            # Get analytics
            analytics = self.performance_service.get_portfolio_analytics(portfolio_id)
            
            # Get performance report
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # Last 30 days
            report = self.performance_service.generate_performance_report(portfolio_id, start_date, end_date)
            
            return {
                "summary": summary.dict(),
                "analytics": analytics.dict(),
                "recent_report": report,
                "last_updated": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio dashboard data: {str(e)}")
            raise
    
    def bulk_update_property_values(self, portfolio_id: uuid.UUID, 
                                   value_updates: Dict[uuid.UUID, float]) -> bool:
        """Bulk update property values in a portfolio."""
        try:
            updated_count = 0
            
            for property_id, new_value in value_updates.items():
                portfolio_property = self.db.query(PortfolioPropertyDB).filter(
                    and_(
                        PortfolioPropertyDB.portfolio_id == portfolio_id,
                        PortfolioPropertyDB.property_id == property_id
                    )
                ).first()
                
                if portfolio_property:
                    portfolio_property.current_value = new_value
                    portfolio_property.last_valuation_date = datetime.now()
                    self._recalculate_property_metrics(portfolio_property)
                    updated_count += 1
            
            if updated_count > 0:
                self.db.commit()
                # Update portfolio metrics
                self.performance_service.update_portfolio_metrics(portfolio_id)
                logger.info(f"Bulk updated {updated_count} property values in portfolio {portfolio_id}")
            
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Error bulk updating property values: {str(e)}")
            self.db.rollback()
            raise


def get_portfolio_management_service(db: Session = None) -> PortfolioManagementService:
    """Factory function to get PortfolioManagementService instance."""
    if db is None:
        db = next(get_db())
    return PortfolioManagementService(db)