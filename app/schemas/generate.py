from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
import re


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000, description="Image description prompt")
    style: Optional[str] = Field(default="realistic", description="Art style (realistic, photorealistic, cinematic, portrait, anime, fantasy, sci-fi, 3d-render)")
    resolution: Optional[str] = Field(default="512x768", description="Image resolution (e.g., 512x768)")
    negative_prompt: Optional[str] = Field(default=None, max_length=50000, description="What to avoid in generation")
    model: Optional[str] = Field(default="flux", description="AI model (flux, seedream, zimage, gptimage, imagen-4)")
    enhance: Optional[bool] = Field(default=True, description="Enable AI prompt enhancement")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "a beautiful woman with blue eyes, professional portrait",
                    "style": "photorealistic",
                    "resolution": "512x768",
                    "model": "flux",
                    "negative_prompt": "blurry, bad quality, distorted"
                }
            ]
        }
    }


class ImageToImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=50000, description="Description of the transformation to apply")
    image_url: str = Field(..., max_length=2048, description="URL of the input image to transform")
    style: Optional[str] = Field(default="realistic", description="Art style to apply")
    resolution: Optional[str] = Field(default="512x768", description="Output image resolution")
    negative_prompt: Optional[str] = Field(default=None, max_length=50000, description="What to avoid in generation")

    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v: str) -> str:
        """Validate that image_url is a valid HTTPS URL"""
        # Must start with https://
        if not v.startswith('https://'):
            raise ValueError('image_url must use HTTPS protocol')

        # Basic URL pattern validation
        url_pattern = re.compile(
            r'^https://'
            r'[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
            r'(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*'
            r'(:\d{1,5})?'
            r'(/[^\s]*)?$'
        )

        if not url_pattern.match(v):
            raise ValueError('image_url must be a valid URL')

        # Block localhost and private IPs (SSRF protection)
        blocked_patterns = [
            r'localhost',
            r'127\.\d+\.\d+\.\d+',
            r'10\.\d+\.\d+\.\d+',
            r'172\.(1[6-9]|2\d|3[01])\.\d+\.\d+',
            r'192\.168\.\d+\.\d+',
            r'0\.0\.0\.0',
            r'\[::1\]',
        ]

        for pattern in blocked_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('image_url cannot point to local or private addresses')

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "prompt": "transform into anime style",
                    "image_url": "https://example.com/photo.jpg",
                    "style": "anime",
                    "resolution": "512x768"
                }
            ]
        }
    }


class GenerateResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    seed: Optional[int] = None
    error: Optional[str] = None
    model: Optional[str] = None


class StylesResponse(BaseModel):
    styles: List[str]


class ModelsResponse(BaseModel):
    models: Dict[str, str]
