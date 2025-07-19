from typing import Optional

from fastapi import APIRouter, HTTPException, status

from presentation.dependencies import OrchestratorServiceDependency

router = APIRouter(prefix="/portfolio-agent")


@router.post("/turn-credentials")
async def generate_turn_credentials(
        orchestrator_service: OrchestratorServiceDependency,
        ttl: Optional[int] = 900,
):
    """
    Generate TURN server credentials for WebRTC connections
    
    Args:
        ttl: Time to live for the credentials in seconds (default: 900 = 15 minutes)
        orchestrator_service: Injected orchestrator service
        
    Returns:
        dict: ICE servers configuration for WebRTC
    """
    try:
        credentials = await orchestrator_service.generate_turn_credentials(ttl=ttl)
        return credentials
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate TURN credentials: {str(e)}"
        )
