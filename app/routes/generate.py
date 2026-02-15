from fastapi import APIRouter, HTTPException
from app.schemas import GenerateRequest, GenerateResponse, ImageToImageRequest
from app.services import PerchanceService
from app.services.queue_service import queue_service, JobStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("", response_model=GenerateResponse)
async def generate_image(body: GenerateRequest) -> GenerateResponse:
    """
    Generate a realistic image using Pollinations.ai

    - **prompt**: Description of the image to generate
    - **style**: Art style (realistic, photorealistic, cinematic, portrait, anime, fantasy, sci-fi, 3d-render)
    - **resolution**: Image dimensions (e.g., 512x768)
    - **model**: AI model (sana, zimage, turbo)
    - **negative_prompt**: What to avoid in the generation
    - **enhance**: Enable AI prompt enhancement (default: True)
    """
    # Validate style
    available_styles = PerchanceService.get_styles()
    if body.style and body.style not in available_styles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style. Available styles: {', '.join(available_styles)}"
        )

    # Validate model
    available_models = PerchanceService.get_models()
    model = body.model or "flux"
    if model not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Available models: {', '.join(available_models.keys())}"
        )

    # Generate image
    success, image_url, seed, error = await PerchanceService.generate_image(
        prompt=body.prompt,
        style=body.style or "realistic",
        resolution=body.resolution or "512x768",
        negative_prompt=body.negative_prompt,
        model=model,
        enhance=body.enhance if body.enhance is not None else True
    )

    if not success:
        logger.error(f"Image generation failed: {error}")
        raise HTTPException(
            status_code=500,
            detail=error if error else "Failed to generate image"
        )

    return GenerateResponse(
        success=True,
        image_url=image_url,
        seed=seed,
        model=model
    )


@router.post("/img2img", response_model=GenerateResponse)
async def image_to_image(body: ImageToImageRequest) -> GenerateResponse:
    """
    Transform an existing image using AI (image-to-image with kontext model).

    - **prompt**: Description of the transformation to apply
    - **image_url**: URL of the input image to transform (must be HTTPS)
    - **style**: Art style to apply
    - **resolution**: Output image resolution
    - **negative_prompt**: What to avoid in the generation
    """
    # Validate style
    available_styles = PerchanceService.get_styles()
    if body.style and body.style not in available_styles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style. Available styles: {', '.join(available_styles)}"
        )

    # Generate image using kontext model
    success, image_url, seed, error = await PerchanceService.image_to_image(
        prompt=body.prompt,
        image_url=body.image_url,
        style=body.style or "realistic",
        resolution=body.resolution or "512x768",
        negative_prompt=body.negative_prompt
    )

    if not success:
        logger.error(f"Image transformation failed: {error}")
        raise HTTPException(
            status_code=500,
            detail=error if error else "Failed to transform image"
        )

    return GenerateResponse(
        success=True,
        image_url=image_url,
        seed=seed,
        model="kontext"
    )


# ============== QUEUE ENDPOINTS ==============

@router.post("/queue", tags=["Queue"])
async def queue_generate_image(body: GenerateRequest):
    """
    Add image generation to queue (non-blocking).
    Returns a job_id to check status later.

    Use this for high-traffic scenarios to prevent server overload.
    """
    # Validate style
    available_styles = PerchanceService.get_styles()
    if body.style and body.style not in available_styles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid style. Available styles: {', '.join(available_styles)}"
        )

    # Validate model
    available_models = PerchanceService.get_models()
    model = body.model or "flux"
    if model not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model. Available models: {', '.join(available_models.keys())}"
        )

    # Add to queue
    job = await queue_service.add_job({
        "job_type": "generate",
        "prompt": body.prompt,
        "style": body.style or "realistic",
        "resolution": body.resolution or "512x768",
        "negative_prompt": body.negative_prompt,
        "model": model,
        "enhance": body.enhance if body.enhance is not None else True
    })

    return {
        "job_id": job.id,
        "status": job.status.value,
        "position": job.position,
        "message": f"Job queued. Position: {job.position}"
    }


@router.get("/queue/{job_id}", tags=["Queue"])
async def get_job_status(job_id: str):
    """
    Check the status of a queued job.

    - **pending**: Job is waiting in queue
    - **processing**: Job is being processed
    - **completed**: Job finished, result available
    - **failed**: Job failed, error available
    """
    job = queue_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    response = {
        "job_id": job.id,
        "status": job.status.value,
        "position": job.position if job.status == JobStatus.PENDING else 0
    }

    if job.status == JobStatus.COMPLETED and job.result:
        response["result"] = job.result
    elif job.status == JobStatus.FAILED:
        response["error"] = job.error

    return response


@router.get("/queue", tags=["Queue"])
async def get_queue_status():
    """
    Get current queue status.

    Returns number of pending/processing jobs and available slots.
    """
    return queue_service.get_queue_status()
