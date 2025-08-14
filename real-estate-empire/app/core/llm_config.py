"""
LLM Configuration and Management for Real Estate Empire Agents
"""

import os
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import google.generativeai as genai


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class LLMModel(str, Enum):
    """Available LLM models"""
    # OpenAI Models
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # Anthropic Models
    CLAUDE_3_OPUS = "claude-3-opus-20240229"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    
    # Google Models
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"


@dataclass
class LLMConfig:
    """Configuration for a specific LLM instance"""
    model: LLMModel
    provider: LLMProvider
    temperature: float
    max_tokens: int
    system_prompt: str
    backup_model: Optional[LLMModel] = None
    cost_per_1k_tokens: float = 0.0
    rate_limit_rpm: int = 3000
    timeout_seconds: int = 30


class AgentLLMConfigs:
    """LLM configurations for each agent type"""
    
    SCOUT_AGENT = LLMConfig(
        model=LLMModel.GPT_4_TURBO,
        provider=LLMProvider.OPENAI,
        temperature=0.3,
        max_tokens=2000,
        backup_model=LLMModel.CLAUDE_3_SONNET,
        cost_per_1k_tokens=0.01,
        system_prompt="""You are an expert real estate scout agent operating in an autonomous AI hive system. 
        Your mission is to continuously discover high-potential investment opportunities.
        
        Your capabilities include:
        1. Scanning MLS listings, foreclosures, and off-market properties
        2. Applying investment criteria to filter opportunities
        3. Scoring leads based on potential profitability
        4. Identifying motivated sellers and distressed properties
        5. Gathering comprehensive property and owner information
        
        Always prioritize deals with the highest profit potential and lowest risk.
        Focus on properties that match the current portfolio strategy.
        Provide clear, actionable recommendations with confidence scores."""
    )
    
    ANALYST_AGENT = LLMConfig(
        model=LLMModel.GPT_4_TURBO,
        provider=LLMProvider.OPENAI,
        temperature=0.2,
        max_tokens=4000,
        backup_model=LLMModel.CLAUDE_3_OPUS,
        cost_per_1k_tokens=0.01,
        system_prompt="""You are an expert real estate financial analyst agent in an autonomous AI system.
        Your mission is to perform comprehensive property analysis and provide investment recommendations.
        
        Your capabilities include:
        1. Comparable property analysis (CMA) with statistical validation
        2. After Repair Value (ARV) estimation with confidence intervals
        3. Repair cost estimation using photos, descriptions, and market data
        4. Cash flow analysis and financial modeling for multiple scenarios
        5. Investment strategy comparison (flip, rental, wholesale, BRRRR)
        6. Risk assessment with quantified probability distributions
        
        Always provide detailed analysis with confidence scores and supporting data.
        Consider multiple exit strategies and recommend the optimal approach.
        Use conservative estimates and clearly state all assumptions."""
    )
    
    NEGOTIATOR_AGENT = LLMConfig(
        model=LLMModel.GPT_4_TURBO,
        provider=LLMProvider.OPENAI,
        temperature=0.7,
        max_tokens=1500,
        backup_model=LLMModel.CLAUDE_3_SONNET,
        cost_per_1k_tokens=0.01,
        system_prompt="""You are an expert real estate negotiator agent in an autonomous AI system.
        Your mission is to communicate with property owners, build relationships, and negotiate deals.
        
        Your capabilities include:
        1. Crafting personalized outreach messages (email, SMS, voice scripts)
        2. Analyzing seller responses for sentiment and motivation
        3. Building rapport and trust with property owners
        4. Negotiating purchase terms and price with win-win outcomes
        5. Handling objections and concerns professionally
        6. Coordinating multi-channel communication campaigns
        
        Always be professional, empathetic, and focused on win-win outcomes.
        Adapt your communication style to each seller's preferences and situation.
        Maintain ethical standards and comply with all communication regulations."""
    )
    
    CONTRACT_AGENT = LLMConfig(
        model=LLMModel.GPT_4_TURBO,
        provider=LLMProvider.OPENAI,
        temperature=0.1,
        max_tokens=3000,
        backup_model=LLMModel.CLAUDE_3_OPUS,
        cost_per_1k_tokens=0.01,
        system_prompt="""You are a real estate legal expert agent in an autonomous AI system.
        Your mission is to generate contracts, ensure compliance, and manage transactions.
        
        Your capabilities include:
        1. Dynamic contract generation based on deal specifics
        2. Legal compliance checking for state and local regulations
        3. Document analysis and risk assessment
        4. Transaction timeline management and coordination
        5. Electronic signature workflow management
        6. Closing process coordination
        
        Always ensure legal accuracy and compliance with all applicable laws.
        Use precise legal language while maintaining clarity.
        Flag any potential legal issues for human review."""
    )
    
    PORTFOLIO_AGENT = LLMConfig(
        model=LLMModel.GPT_4_TURBO,
        provider=LLMProvider.OPENAI,
        temperature=0.4,
        max_tokens=2500,
        backup_model=LLMModel.CLAUDE_3_SONNET,
        cost_per_1k_tokens=0.01,
        system_prompt="""You are a portfolio management expert agent in an autonomous AI system.
        Your mission is to optimize and manage the real estate investment portfolio.
        
        Your capabilities include:
        1. Portfolio performance tracking and analysis
        2. Investment strategy optimization recommendations
        3. Market condition analysis and timing decisions
        4. Risk management and diversification strategies
        5. Cash flow optimization and refinancing opportunities
        6. Exit strategy planning and execution
        
        Always focus on maximizing risk-adjusted returns.
        Consider market cycles, tax implications, and liquidity needs.
        Provide clear, actionable recommendations with supporting analysis."""
    )
    
    SUPERVISOR_AGENT = LLMConfig(
        model=LLMModel.GPT_4_TURBO,
        provider=LLMProvider.OPENAI,
        temperature=0.5,
        max_tokens=2000,
        backup_model=LLMModel.CLAUDE_3_OPUS,
        cost_per_1k_tokens=0.01,
        system_prompt="""You are the Supervisor Agent orchestrating an autonomous real estate AI hive system.
        Your mission is to coordinate all specialized agents and make strategic decisions.
        
        Your capabilities include:
        1. Analyzing system state and agent performance
        2. Making strategic routing decisions for workflows
        3. Coordinating agent collaboration and conflict resolution
        4. Escalating critical decisions to human oversight
        5. Optimizing system performance and resource allocation
        6. Managing risk and ensuring compliance across all operations
        
        Always prioritize system efficiency and profitability.
        Make data-driven decisions based on current market conditions.
        Ensure all agents work together toward common investment goals."""
    )


class LLMManager:
    """Manages LLM instances and provides unified interface"""
    
    def __init__(self):
        self.llm_instances: Dict[str, Any] = {}
        self.api_keys = self._load_api_keys()
        self._initialize_llms()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        return {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY")
        }
    
    def _initialize_llms(self):
        """Initialize all LLM instances"""
        configs = [
            ("scout", AgentLLMConfigs.SCOUT_AGENT),
            ("analyst", AgentLLMConfigs.ANALYST_AGENT),
            ("negotiator", AgentLLMConfigs.NEGOTIATOR_AGENT),
            ("contract", AgentLLMConfigs.CONTRACT_AGENT),
            ("portfolio", AgentLLMConfigs.PORTFOLIO_AGENT),
            ("supervisor", AgentLLMConfigs.SUPERVISOR_AGENT),
        ]
        
        for agent_name, config in configs:
            self.llm_instances[agent_name] = self._create_llm_instance(config)
    
    def _create_llm_instance(self, config: LLMConfig):
        """Create an LLM instance based on configuration"""
        if config.provider == LLMProvider.OPENAI:
            api_key = self.api_keys["openai"]
            if not api_key:
                # For testing or when API key is not available
                api_key = "test-key"
            return ChatOpenAI(
                model=config.model.value,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                openai_api_key=api_key,
                request_timeout=config.timeout_seconds
            )
        elif config.provider == LLMProvider.ANTHROPIC:
            api_key = self.api_keys["anthropic"]
            if not api_key:
                # For testing or when API key is not available
                api_key = "test-key"
            return ChatAnthropic(
                model=config.model.value,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                anthropic_api_key=api_key,
                timeout=config.timeout_seconds
            )
        elif config.provider == LLMProvider.GOOGLE:
            api_key = self.api_keys["google"]
            if api_key:
                genai.configure(api_key=api_key)
            return genai.GenerativeModel(config.model.value)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")
    
    def get_llm(self, agent_name: str):
        """Get LLM instance for a specific agent"""
        if agent_name not in self.llm_instances:
            raise ValueError(f"No LLM configured for agent: {agent_name}")
        return self.llm_instances[agent_name]
    
    def get_config(self, agent_name: str) -> LLMConfig:
        """Get LLM configuration for a specific agent"""
        config_map = {
            "scout": AgentLLMConfigs.SCOUT_AGENT,
            "analyst": AgentLLMConfigs.ANALYST_AGENT,
            "negotiator": AgentLLMConfigs.NEGOTIATOR_AGENT,
            "contract": AgentLLMConfigs.CONTRACT_AGENT,
            "portfolio": AgentLLMConfigs.PORTFOLIO_AGENT,
            "supervisor": AgentLLMConfigs.SUPERVISOR_AGENT,
        }
        
        if agent_name not in config_map:
            raise ValueError(f"No configuration for agent: {agent_name}")
        return config_map[agent_name]
    
    async def invoke_with_fallback(self, agent_name: str, prompt: str) -> str:
        """Invoke LLM with automatic fallback to backup model"""
        config = self.get_config(agent_name)
        primary_llm = self.get_llm(agent_name)
        
        try:
            # Try primary model
            response = await primary_llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            print(f"Primary LLM failed for {agent_name}: {e}")
            
            # Fallback to backup model if configured
            if config.backup_model:
                try:
                    backup_config = LLMConfig(
                        model=config.backup_model,
                        provider=LLMProvider.ANTHROPIC if "claude" in config.backup_model.value else LLMProvider.OPENAI,
                        temperature=config.temperature,
                        max_tokens=config.max_tokens,
                        system_prompt=config.system_prompt
                    )
                    backup_llm = self._create_llm_instance(backup_config)
                    response = await backup_llm.ainvoke(prompt)
                    return response.content
                except Exception as backup_e:
                    print(f"Backup LLM also failed for {agent_name}: {backup_e}")
                    raise backup_e
            else:
                raise e
    
    def estimate_cost(self, agent_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for LLM usage"""
        config = self.get_config(agent_name)
        total_tokens = prompt_tokens + completion_tokens
        return (total_tokens / 1000) * config.cost_per_1k_tokens


# Global LLM manager instance
llm_manager = LLMManager()