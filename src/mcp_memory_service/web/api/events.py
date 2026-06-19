"""
Server-Sent Events endpoints for real-time updates.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from ...config import OAUTH_ENABLED
from ..sse import create_event_stream, sse_manager
from ..dependencies import get_storage

# OAuth authentication imports (conditional)
if OAUTH_ENABLED or TYPE_CHECKING:
    from ..oauth.middleware import require_read_access, AuthenticationResult
else:
    # Provide type stubs when OAuth is disabled
    AuthenticationResult = None
    require_read_access = None

router = APIRouter()


class ConnectionInfo(BaseModel):
    """Individual connection information."""
    connection_id: str
    client_ip: str
    user_agent: str
    connected_duration_seconds: float
    last_heartbeat_seconds_ago: float


class SSEStatsResponse(BaseModel):
    """Response model for SSE connection statistics."""
    total_connections: int
    heartbeat_interval: int
    connections: List[ConnectionInfo]


async def authenticate_sse_request(request: Request) -> Optional[AuthenticationResult]:
    """
    Authenticate SSE requests with support for query parameter token.

    EventSource API doesn't support custom headers, so we allow token
    to be passed via query parameter for SSE connections.
    """
    from fastapi import HTTPException, status

    if not OAUTH_ENABLED:
        return None

    # Try query parameter first (for EventSource)
    token = request.query_params.get("token")
    if token:
        from ..oauth.middleware import authenticate_api_key
        api_key_result = authenticate_api_key(token)
        if api_key_result.authenticated:
            return api_key_result

        # Try OAuth token validation
        from ..oauth.middleware import authenticate_bearer_token
        oauth_result = await authenticate_bearer_token(token)
        if oauth_result.authenticated:
            return oauth_result

    # Fall back to header-based authentication
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        from ..oauth.middleware import authenticate_api_key, authenticate_bearer_token

        api_key_result = authenticate_api_key(token)
        if api_key_result.authenticated:
            return api_key_result

        oauth_result = await authenticate_bearer_token(token)
        if oauth_result.authenticated:
            return oauth_result

    # If we get here, authentication failed
    from ...config import ALLOW_ANONYMOUS_ACCESS
    if ALLOW_ANONYMOUS_ACCESS:
        from ..oauth.middleware import AuthenticationResult
        return AuthenticationResult(
            authenticated=True,
            client_id="anonymous",
            scope="read",
            auth_method="none"
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"error": "authentication_required", "error_description": "Provide token via query parameter or Authorization header"}
    )


@router.get("/events")
async def events_endpoint(
    request: Request,
    user: AuthenticationResult = Depends(authenticate_sse_request) if OAUTH_ENABLED else None
):
    """
    Server-Sent Events endpoint for real-time updates.

    Provides a continuous stream of events including:
    - memory_stored: When new memories are added
    - memory_deleted: When memories are removed
    - search_completed: When searches finish
    - health_update: System status changes
    - heartbeat: Periodic keep-alive signals
    - connection_established: Welcome message

    Authentication:
    - Standard API: Use Authorization: Bearer <token> header
    - EventSource/SSE: Use ?token=<api_key> query parameter
    """
    return await create_event_stream(request)


@router.get("/events/stats")
async def get_sse_stats(
    user: AuthenticationResult = Depends(require_read_access) if OAUTH_ENABLED else None
):
    """
    Get statistics about current SSE connections.
    
    Returns information about active connections, connection duration,
    and heartbeat status.
    """
    try:
        # Get raw stats first to debug the structure
        stats = sse_manager.get_connection_stats()
        
        # Validate structure and transform if needed
        connections = []
        for conn_data in stats.get('connections', []):
            connections.append({
                "connection_id": conn_data.get("connection_id", "unknown"),
                "client_ip": conn_data.get("client_ip", "unknown"),
                "user_agent": conn_data.get("user_agent", "unknown"),
                "connected_duration_seconds": conn_data.get("connected_duration_seconds", 0.0),
                "last_heartbeat_seconds_ago": conn_data.get("last_heartbeat_seconds_ago", 0.0)
            })
        
        return {
            "total_connections": stats.get("total_connections", 0),
            "heartbeat_interval": stats.get("heartbeat_interval", 30),
            "connections": connections
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error getting SSE stats: {str(e)}")
        # Return safe default stats if there's an error
        return {
            "total_connections": 0,
            "heartbeat_interval": 30,
            "connections": []
        }