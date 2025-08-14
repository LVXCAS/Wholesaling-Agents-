"""
Agent Tool Integration Framework for Real Estate Empire
Provides a unified interface for agents to access various tools and services
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Union, Type
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import uuid

from pydantic import BaseModel, Field
from langchain.tools import Tool, BaseTool
from langchain.agents import AgentExecutor
from langchain_core.tools import StructuredTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categories of tools available to agents"""
    DATA_RETRIEVAL = "data_retrieval"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    DOCUMENT = "document"
    FINANCIAL = "financial"
    MARKET_DATA = "market_data"
    PROPERTY_SEARCH = "property_search"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    UTILITY = "utility"


class ToolAccessLevel(str, Enum):
    """Access levels for tools"""
    PUBLIC = "public"  # Available to all agents
    RESTRICTED = "restricted"  # Available to specific agent types
    PRIVATE = "private"  # Available to specific agent instances
    ADMIN = "admin"  # Available only to supervisor agents


@dataclass
class ToolMetadata:
    """Metadata for agent tools"""
    name: str
    description: str
    category: ToolCategory
    access_level: ToolAccessLevel
    allowed_agents: Optional[List[str]] = None
    rate_limit: Optional[int] = None  # calls per minute
    cost_per_call: float = 0.0
    timeout_seconds: int = 30
    requires_auth: bool = False
    version: str = "1.0.0"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class BaseAgentTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, metadata: ToolMetadata):
        self.metadata = metadata
        self.usage_count = 0
        self.last_used = None
        self.error_count = 0
        self.total_execution_time = 0.0
        
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    def can_access(self, agent_name: str, agent_type: str) -> bool:
        """Check if agent can access this tool"""
        if self.metadata.access_level == ToolAccessLevel.PUBLIC:
            return True
        elif self.metadata.access_level == ToolAccessLevel.RESTRICTED:
            return agent_type in (self.metadata.allowed_agents or [])
        elif self.metadata.access_level == ToolAccessLevel.PRIVATE:
            return agent_name in (self.metadata.allowed_agents or [])
        elif self.metadata.access_level == ToolAccessLevel.ADMIN:
            return agent_type == "supervisor"
        return False
    
    async def safe_execute(self, agent_name: str, **kwargs) -> Dict[str, Any]:
        """Execute tool with error handling and metrics tracking"""
        start_time = datetime.now()
        
        try:
            self.usage_count += 1
            self.last_used = start_time
            
            result = await self.execute(**kwargs)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.total_execution_time += execution_time
            
            logger.debug(f"Tool {self.metadata.name} executed successfully by {agent_name} in {execution_time:.2f}s")
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.error_count += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"Tool {self.metadata.name} failed for {agent_name}: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics"""
        avg_execution_time = (
            self.total_execution_time / self.usage_count 
            if self.usage_count > 0 else 0
        )
        
        return {
            "usage_count": self.usage_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.usage_count, 1),
            "average_execution_time": avg_execution_time,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "total_cost": self.usage_count * self.metadata.cost_per_call
        }


# Concrete tool implementations

class PropertySearchTool(BaseAgentTool):
    """Tool for searching properties from various sources"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="property_search",
            description="Search for properties from MLS, public records, and other sources",
            category=ToolCategory.PROPERTY_SEARCH,
            access_level=ToolAccessLevel.PUBLIC,
            rate_limit=100,
            cost_per_call=0.01
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute property search"""
        search_criteria = kwargs.get("criteria", {})
        location = kwargs.get("location", "")
        property_type = kwargs.get("property_type", "")
        max_results = kwargs.get("max_results", 50)
        
        # Simulate property search (would integrate with actual APIs)
        await asyncio.sleep(0.1)  # Simulate API call
        
        properties = [
            {
                "id": str(uuid.uuid4()),
                "address": f"123 Main St, {location}",
                "price": 250000,
                "bedrooms": 3,
                "bathrooms": 2,
                "square_feet": 1500,
                "property_type": property_type or "single_family",
                "days_on_market": 15,
                "source": "MLS"
            }
            for i in range(min(max_results, 10))  # Return up to 10 sample properties
        ]
        
        return {
            "properties": properties,
            "total_found": len(properties),
            "search_criteria": search_criteria,
            "timestamp": datetime.now().isoformat()
        }


class PropertyAnalysisTool(BaseAgentTool):
    """Tool for analyzing property financials and metrics"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="property_analysis",
            description="Analyze property financials, comparables, and investment metrics",
            category=ToolCategory.ANALYSIS,
            access_level=ToolAccessLevel.PUBLIC,
            rate_limit=50,
            cost_per_call=0.05
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute property analysis"""
        property_data = kwargs.get("property_data", {})
        analysis_type = kwargs.get("analysis_type", "comprehensive")
        
        # Simulate analysis (would integrate with actual analysis engine)
        await asyncio.sleep(0.5)  # Simulate analysis time
        
        analysis_result = {
            "property_id": property_data.get("id", str(uuid.uuid4())),
            "valuation": {
                "current_value": property_data.get("price", 0) * 0.95,
                "arv": property_data.get("price", 0) * 1.1,
                "confidence_score": 0.85
            },
            "financial_metrics": {
                "cap_rate": 0.08,
                "cash_flow": 450,
                "roi": 0.12,
                "cash_on_cash_return": 0.15
            },
            "repair_estimate": {
                "total_cost": 15000,
                "confidence_score": 0.75,
                "line_items": {
                    "kitchen": 8000,
                    "bathrooms": 4000,
                    "flooring": 3000
                }
            },
            "investment_strategies": [
                {
                    "strategy": "buy_and_hold",
                    "potential_profit": 50000,
                    "risk_level": 0.3,
                    "timeline_months": 12
                },
                {
                    "strategy": "flip",
                    "potential_profit": 35000,
                    "risk_level": 0.5,
                    "timeline_months": 6
                }
            ]
        }
        
        return analysis_result


class MarketDataTool(BaseAgentTool):
    """Tool for retrieving market data and trends"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="market_data",
            description="Retrieve market data, trends, and neighborhood information",
            category=ToolCategory.MARKET_DATA,
            access_level=ToolAccessLevel.PUBLIC,
            rate_limit=200,
            cost_per_call=0.02
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute market data retrieval"""
        location = kwargs.get("location", "")
        data_type = kwargs.get("data_type", "comprehensive")
        
        # Simulate market data retrieval
        await asyncio.sleep(0.2)
        
        market_data = {
            "location": location,
            "median_home_price": 275000,
            "price_trend_12m": 0.08,  # 8% increase
            "days_on_market_avg": 25,
            "inventory_level": "low",
            "neighborhood_score": 0.75,
            "school_rating": 8.5,
            "crime_index": 0.3,  # Lower is better
            "walkability_score": 65,
            "comparable_sales": [
                {
                    "address": "456 Oak St",
                    "sale_price": 265000,
                    "sale_date": "2024-01-15",
                    "square_feet": 1450
                }
            ]
        }
        
        return market_data


class CommunicationTool(BaseAgentTool):
    """Tool for sending communications (email, SMS, calls)"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="communication",
            description="Send emails, SMS, and make calls to leads and contacts",
            category=ToolCategory.COMMUNICATION,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["negotiator", "supervisor"],
            rate_limit=1000,
            cost_per_call=0.10
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute communication"""
        channel = kwargs.get("channel", "email")  # email, sms, call
        recipient = kwargs.get("recipient", "")
        message = kwargs.get("message", "")
        template = kwargs.get("template", None)
        
        # Simulate communication sending
        await asyncio.sleep(0.3)
        
        result = {
            "message_id": str(uuid.uuid4()),
            "channel": channel,
            "recipient": recipient,
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
            "estimated_delivery": datetime.now().isoformat()
        }
        
        return result


class DocumentGenerationTool(BaseAgentTool):
    """Tool for generating contracts and legal documents"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="document_generation",
            description="Generate contracts, offers, and legal documents",
            category=ToolCategory.DOCUMENT,
            access_level=ToolAccessLevel.RESTRICTED,
            allowed_agents=["contract", "supervisor"],
            rate_limit=20,
            cost_per_call=0.50
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute document generation"""
        document_type = kwargs.get("document_type", "purchase_agreement")
        deal_data = kwargs.get("deal_data", {})
        template_id = kwargs.get("template_id", None)
        
        # Simulate document generation
        await asyncio.sleep(1.0)
        
        result = {
            "document_id": str(uuid.uuid4()),
            "document_type": document_type,
            "status": "generated",
            "file_url": f"/documents/{uuid.uuid4()}.pdf",
            "generated_at": datetime.now().isoformat(),
            "requires_signature": True,
            "parties": deal_data.get("parties", [])
        }
        
        return result


class FinancialCalculatorTool(BaseAgentTool):
    """Tool for financial calculations and modeling"""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="financial_calculator",
            description="Perform financial calculations and modeling",
            category=ToolCategory.FINANCIAL,
            access_level=ToolAccessLevel.PUBLIC,
            rate_limit=500,
            cost_per_call=0.01
        )
        super().__init__(metadata)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute financial calculations"""
        calculation_type = kwargs.get("calculation_type", "cash_flow")
        parameters = kwargs.get("parameters", {})
        
        # Simulate financial calculations
        await asyncio.sleep(0.1)
        
        if calculation_type == "cash_flow":
            monthly_rent = parameters.get("monthly_rent", 0)
            monthly_expenses = parameters.get("monthly_expenses", 0)
            result = {
                "monthly_cash_flow": monthly_rent - monthly_expenses,
                "annual_cash_flow": (monthly_rent - monthly_expenses) * 12
            }
        elif calculation_type == "cap_rate":
            noi = parameters.get("net_operating_income", 0)
            property_value = parameters.get("property_value", 1)
            result = {
                "cap_rate": noi / property_value if property_value > 0 else 0
            }
        else:
            result = {"error": f"Unknown calculation type: {calculation_type}"}
        
        return result


class AgentToolRegistry:
    """Registry for managing all agent tools"""
    
    def __init__(self):
        self.tools: Dict[str, BaseAgentTool] = {}
        self.tool_usage_stats: Dict[str, Dict[str, Any]] = {}
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        
    def register_tool(self, tool: BaseAgentTool):
        """Register a new tool"""
        self.tools[tool.metadata.name] = tool
        self.tool_usage_stats[tool.metadata.name] = {}
        logger.info(f"Registered tool: {tool.metadata.name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseAgentTool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools_for_agent(self, agent_name: str, agent_type: str) -> List[str]:
        """List all tools available to a specific agent"""
        available_tools = []
        
        for tool_name, tool in self.tools.items():
            if tool.can_access(agent_name, agent_type):
                available_tools.append(tool_name)
        
        return available_tools
    
    def get_tools_by_category(self, category: ToolCategory) -> List[BaseAgentTool]:
        """Get all tools in a specific category"""
        return [
            tool for tool in self.tools.values()
            if tool.metadata.category == category
        ]
    
    async def execute_tool(self, tool_name: str, agent_name: str, agent_type: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with access control and rate limiting"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
        
        # Check access permissions
        if not tool.can_access(agent_name, agent_type):
            return {
                "success": False,
                "error": f"Access denied for agent {agent_name} to tool {tool_name}"
            }
        
        # Check rate limiting
        if not await self._check_rate_limit(tool_name, agent_name):
            return {
                "success": False,
                "error": f"Rate limit exceeded for tool {tool_name}"
            }
        
        # Execute tool
        result = await tool.safe_execute(agent_name, **kwargs)
        
        # Update usage statistics
        self._update_usage_stats(tool_name, agent_name, result)
        
        return result
    
    async def _check_rate_limit(self, tool_name: str, agent_name: str) -> bool:
        """Check if agent has exceeded rate limit for tool"""
        tool = self.tools[tool_name]
        if not tool.metadata.rate_limit:
            return True
        
        # Simple rate limiting implementation
        current_time = datetime.now()
        rate_limit_key = f"{tool_name}:{agent_name}"
        
        if rate_limit_key not in self.rate_limiters:
            self.rate_limiters[rate_limit_key] = {
                "calls": [],
                "window_start": current_time
            }
        
        rate_data = self.rate_limiters[rate_limit_key]
        
        # Clean old calls (older than 1 minute)
        rate_data["calls"] = [
            call_time for call_time in rate_data["calls"]
            if (current_time - call_time).total_seconds() < 60
        ]
        
        # Check if under limit
        if len(rate_data["calls"]) >= tool.metadata.rate_limit:
            return False
        
        # Add current call
        rate_data["calls"].append(current_time)
        return True
    
    def _update_usage_stats(self, tool_name: str, agent_name: str, result: Dict[str, Any]):
        """Update tool usage statistics"""
        if agent_name not in self.tool_usage_stats[tool_name]:
            self.tool_usage_stats[tool_name][agent_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_execution_time": 0.0
            }
        
        stats = self.tool_usage_stats[tool_name][agent_name]
        stats["total_calls"] += 1
        
        if result.get("success", False):
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
        
        stats["total_execution_time"] += result.get("execution_time", 0)
    
    def get_tool_stats(self, tool_name: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {}
        
        tool_stats = tool.get_stats()
        usage_stats = self.tool_usage_stats.get(tool_name, {})
        
        return {
            "tool_metadata": asdict(tool.metadata),
            "tool_stats": tool_stats,
            "agent_usage": usage_stats
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get overall registry statistics"""
        total_tools = len(self.tools)
        tools_by_category = {}
        tools_by_access_level = {}
        
        for tool in self.tools.values():
            category = tool.metadata.category.value
            access_level = tool.metadata.access_level.value
            
            tools_by_category[category] = tools_by_category.get(category, 0) + 1
            tools_by_access_level[access_level] = tools_by_access_level.get(access_level, 0) + 1
        
        return {
            "total_tools": total_tools,
            "tools_by_category": tools_by_category,
            "tools_by_access_level": tools_by_access_level,
            "registered_tools": list(self.tools.keys())
        }


class LangChainToolAdapter:
    """Adapter to convert agent tools to LangChain tools"""
    
    @staticmethod
    def create_langchain_tool(agent_tool: BaseAgentTool, agent_name: str, agent_type: str) -> Tool:
        """Convert an agent tool to a LangChain tool"""
        
        async def tool_func(**kwargs):
            """Wrapper function for LangChain tool"""
            result = await agent_tool.safe_execute(agent_name, **kwargs)
            if result.get("success", False):
                return result["result"]
            else:
                raise Exception(result.get("error", "Tool execution failed"))
        
        return Tool(
            name=agent_tool.metadata.name,
            description=agent_tool.metadata.description,
            func=tool_func,
            coroutine=tool_func
        )
    
    @staticmethod
    def create_structured_tool(agent_tool: BaseAgentTool, agent_name: str, agent_type: str, 
                             input_schema: Type[BaseModel]) -> StructuredTool:
        """Convert an agent tool to a LangChain StructuredTool"""
        
        async def tool_func(**kwargs):
            """Wrapper function for structured tool"""
            result = await agent_tool.safe_execute(agent_name, **kwargs)
            if result.get("success", False):
                return result["result"]
            else:
                raise Exception(result.get("error", "Tool execution failed"))
        
        return StructuredTool(
            name=agent_tool.metadata.name,
            description=agent_tool.metadata.description,
            func=tool_func,
            coroutine=tool_func,
            args_schema=input_schema
        )


# Initialize global tool registry and register default tools
tool_registry = AgentToolRegistry()

# Register default tools
default_tools = [
    PropertySearchTool(),
    PropertyAnalysisTool(),
    MarketDataTool(),
    CommunicationTool(),
    DocumentGenerationTool(),
    FinancialCalculatorTool()
]

for tool in default_tools:
    tool_registry.register_tool(tool)

logger.info(f"Agent tool registry initialized with {len(default_tools)} default tools")