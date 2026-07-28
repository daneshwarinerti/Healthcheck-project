"""
Router defining CRUD API endpoints for server monitoring configurations.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db
from app.services.servers import ServerService

logger = logging.getLogger("app")
router = APIRouter(prefix="/api/servers", tags=["Servers"])

@router.get(
    "", 
    response_model=List[schemas.ServerResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Servers",
    description="Retrieves a list of all configured servers under monitoring."
)
def get_servers(db: Session = Depends(get_db)) -> List[models.Server]:
    """
    Get all servers.
    """
    logger.info("GET /api/servers - Fetching all servers")
    return ServerService.get_all_servers(db)

@router.get(
    "/{server_id}", 
    response_model=schemas.ServerResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Server by ID",
    description="Retrieves a single server's configuration and metrics using its ID."
)
def get_server(
    server_id: int, 
    db: Session = Depends(get_db)
) -> models.Server:
    """
    Get single server details.
    """
    logger.info(f"GET /api/servers/{server_id} - Fetching server details")
    return ServerService.get_server_by_id(db, server_id)

@router.post(
    "", 
    response_model=schemas.ServerResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create Server",
    description="Registers a new server to the monitoring list. Requires admin authorization."
)
def create_server(
    server_in: schemas.ServerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> models.Server:
    """
    Create a new server configuration.
    """
    logger.info(f"POST /api/servers - Request from admin '{current_user.username}' to add server '{server_in.name}'")
    return ServerService.create_server(db, server_in)

@router.put(
    "/{server_id}", 
    response_model=schemas.ServerResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Server",
    description="Modifies an existing server configuration. Requires admin authorization."
)
def update_server(
    server_id: int,
    server_in: schemas.ServerUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> models.Server:
    """
    Update server details.
    """
    logger.info(f"PUT /api/servers/{server_id} - Request from admin '{current_user.username}' to update server ID {server_id}")
    return ServerService.update_server(db, server_id, server_in)

@router.delete(
    "/{server_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Server",
    description="Deletes a server from the monitoring dashboard configurations. Requires admin authorization."
)
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
) -> None:
    """
    Delete a server configuration.
    """
    logger.info(f"DELETE /api/servers/{server_id} - Request from admin '{current_user.username}' to remove server ID {server_id}")
    ServerService.delete_server(db, server_id)
    return None
