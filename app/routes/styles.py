from fastapi import APIRouter
from app.schemas import StylesResponse, ModelsResponse
from app.services import PerchanceService

router = APIRouter(tags=["Styles & Models"])


@router.get("/styles", response_model=StylesResponse)
async def get_styles() -> StylesResponse:
    """
    Get list of available art styles for image generation.
    Styles are optimized for realistic renders.
    """
    styles = PerchanceService.get_styles()
    return StylesResponse(styles=styles)


@router.get("/models", response_model=ModelsResponse)
async def get_models() -> ModelsResponse:
    """
    Get list of available AI models from Pollinations.ai.

    - **klein**: Best available quality without premium credits (recommended)
    - **zimage**: Fast generation with crisp upscaling
    - **flux**: Fast generation at low cost
    """
    models = PerchanceService.get_models()
    return ModelsResponse(models=models)
