from typing import Annotated

from fastapi import Depends

from business.services.ingestion_service import IngestionService
from business.dependencies import SupabaseClientDependency


# =============================================================================
# SERVICE DEPENDENCIES
# =============================================================================

async def get_ingestion_service(supabase_client: SupabaseClientDependency) -> IngestionService:
    """Provide a configured IngestionService instance."""
    return IngestionService(supabase_client)


# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================


IngestionServiceDependency = Annotated[IngestionService, Depends(get_ingestion_service)]
