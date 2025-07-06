from typing import Annotated

from fastapi import Depends

from business.services.ingestion_service import IngestionService


# =============================================================================
# SERVICE DEPENDENCIES
# =============================================================================

def get_ingestion_service() -> IngestionService:
    return IngestionService()


# =============================================================================
# TYPE ALIASES FOR DEPENDENCY INJECTION
# =============================================================================


IngestionServiceDependency = Annotated[IngestionService, Depends(get_ingestion_service)]
