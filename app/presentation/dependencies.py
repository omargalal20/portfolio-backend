from typing import Annotated

from fastapi import Depends

from business.dependencies import SupabaseClientDependency
from business.services.ingestion_service import IngestionService


# =============================================================================
# SERVICE DEPENDENCIES
# =============================================================================

def get_ingestion_service(supabase_client: SupabaseClientDependency) -> IngestionService:
    return IngestionService(supabase_client)


# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================


IngestionServiceDependency = Annotated[IngestionService, Depends(get_ingestion_service)]
