from typing import Annotated

from fastapi import Depends

from business.agents.portfolio_agent import PortfolioAgent
from business.clients.supabase_client import SupabaseClient


# =============================================================================
# AGENT DEPENDENCIES
# =============================================================================
def get_portfolio_agent() -> PortfolioAgent:
    """Provide a configured PortfolioAgent instance."""
    return PortfolioAgent()


# =============================================================================
# CLIENT DEPENDENCIES
# =============================================================================
def get_supabase_client() -> SupabaseClient:
    """Provide a configured SupabaseClient instance."""
    return SupabaseClient()


# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================

# Agent Dependencies
PortfolioAgentDependency = Annotated[PortfolioAgent, Depends(get_portfolio_agent)]

# Client Dependencies
SupabaseClientDependency = Annotated[SupabaseClient, Depends(get_supabase_client)]
