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
_supabase_client_singleton = None

async def get_supabase_client() -> SupabaseClient:
    """Provide a configured SupabaseClient instance (singleton)."""
    global _supabase_client_singleton
    
    if _supabase_client_singleton is None:
        _supabase_client_singleton = SupabaseClient()
        await _supabase_client_singleton.initialize()
    
    return _supabase_client_singleton


# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================

# Agent Dependencies
PortfolioAgentDependency = Annotated[PortfolioAgent, Depends(get_portfolio_agent)]

# Client Dependencies
SupabaseClientDependency = Annotated[SupabaseClient, Depends(get_supabase_client)]
