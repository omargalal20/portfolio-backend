from typing import Annotated

from fastapi import Depends

from business.services.ingestion_service import IngestionService
from business.dependencies import SupabaseClientDependency, PortfolioAgentDependency
from business.services.orchestrator_service import OrchestratorService
# =============================================================================
# SERVICE DEPENDENCIES
# =============================================================================

async def get_ingestion_service(supabase_client: SupabaseClientDependency) -> IngestionService:
    """Provide a configured IngestionService instance."""
    return IngestionService(supabase_client)

def get_orchestrator_service(portfolio_agent: PortfolioAgentDependency) -> OrchestratorService:
    """Provide a configured OrchestratorService instance."""
    return OrchestratorService(portfolio_agent)



# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================


IngestionServiceDependency = Annotated[IngestionService, Depends(get_ingestion_service)]

OrchestratorServiceDependency = Annotated[OrchestratorService, Depends(get_orchestrator_service)]