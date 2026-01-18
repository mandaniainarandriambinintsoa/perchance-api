from pydantic import BaseModel, Field
from typing import Optional, List


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=1000, description="Character description prompt")
    style: Optional[str] = Field(default="anime", description="Art style for generation")
    resolution: Optional[str] = Field(default="512x768", description="Image resolution (e.g., 512x768)")
    negative_prompt: Optional[str] = Field(default=None, max_length=500, description="What to avoid in generation")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "a warrior with blue eyes and silver armor",
                    "style": "anime",
                    "resolution": "512x768",
                    "negative_prompt": "blurry, bad quality"
                }
            ]
        }
    }


class GenerateResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    seed: Optional[int] = None
    error: Optional[str] = None


class StylesResponse(BaseModel):
    styles: List[str]
