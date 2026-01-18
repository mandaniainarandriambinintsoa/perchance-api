from fastapi import APIRouter
from app.schemas import StylesResponse
from app.services import PerchanceService

router = APIRouter(prefix="/styles", tags=["Styles"])


@router.get("", response_model=StylesResponse)
async def get_styles() -> StylesResponse:
    """
    Get list of available art styles for character generation
    """
    styles = PerchanceService.get_styles()
    return StylesResponse(styles=styles)
