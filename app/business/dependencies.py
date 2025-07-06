from typing import Annotated

from fastapi import Depends

from business.agents.portfolio_agent import PortfolioAgent


# =============================================================================
# AGENT DEPENDENCIES
# =============================================================================
def get_portfolio_agent() -> PortfolioAgent:
    """Provide a configured PortfolioAgent instance."""
    return PortfolioAgent()


# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================

# Agent Dependencies
PortfolioAgentDependency = Annotated[PortfolioAgent, Depends(get_portfolio_agent)]
