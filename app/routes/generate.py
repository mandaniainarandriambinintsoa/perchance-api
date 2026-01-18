from fastapi import APIRouter, HTTPException
from app.schemas import GenerateRequest, GenerateResponse
from app.services import PerchanceService

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("", response_model=GenerateResponse)
async def generate_character(request: GenerateRequest) -> GenerateResponse:
    """
    Generate a character image using Perchance.org

    - **prompt**: Description of the character to generate
    - **style**: Art style (anime, realistic, fantasy, etc.)
    - **resolution**: Image dimensions (e.g., 512x768)
    - **negative_prompt**: What to avoid in the generation
    """
    # Validate style
    available_styles = PerchanceService.get_styles()
    if request.style and request.style not in available_styles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style. Available styles: {', '.join(available_styles)}"
        )

    # Generate image
    success, image_url, seed, error = await PerchanceService.generate_image(
        prompt=request.prompt,
        style=request.style or "anime",
        resolution=request.resolution or "512x768",
        negative_prompt=request.negative_prompt
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail=error or "Failed to generate image"
        )

    return GenerateResponse(
        success=True,
        image_url=image_url,
        seed=seed
    )
