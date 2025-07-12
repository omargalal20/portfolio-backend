from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import Match


class LoggerMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request and response details."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        logger.debug(f"{request.method} {request.url}")

        # Log path parameters
        routes = request.app.router.routes
        for route in routes:
            match, scope = route.matches(request)
            if match == Match.FULL:
                logger.debug("Path Params:")
                for name, value in scope["path_params"].items():
                    logger.debug(f"\t{name}: {value}")

        # Log authorization header (excluding token)
        auth_header = request.headers.get("authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) > 1:
                logger.debug(f"Authorization: {parts[0]} ***")
            else:
                logger.debug("Authorization header present but not in expected format.")

        response = await call_next(request)

        return response
