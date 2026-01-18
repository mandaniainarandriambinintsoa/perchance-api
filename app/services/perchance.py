import urllib.parse
import random
from typing import Optional, Tuple, List, Literal


class PerchanceService:
    """Service wrapper for AI image generation using Pollinations.ai"""

    AVAILABLE_STYLES = [
        "anime",
        "realistic",
        "fantasy",
        "sci-fi",
        "cartoon",
        "oil-painting",
        "watercolor",
        "pixel-art",
        "comic-book",
        "3d-render"
    ]

    # Pollinations.ai - free, no-auth AI image generation
    BASE_URL = "https://image.pollinations.ai/prompt"

    @classmethod
    def get_styles(cls) -> List[str]:
        """Return list of available styles"""
        return cls.AVAILABLE_STYLES

    @classmethod
    async def generate_image(
        cls,
        prompt: str,
        style: str = "anime",
        resolution: str = "512x768",
        negative_prompt: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Generate an image using Pollinations.ai

        Returns:
            Tuple of (success, image_url, seed, error_message)
        """
        try:
            # Build the full prompt with style
            style_prompts = {
                "anime": "anime style, japanese animation, vibrant colors",
                "realistic": "photorealistic, highly detailed, 8k uhd",
                "fantasy": "fantasy art style, magical, ethereal",
                "sci-fi": "science fiction, futuristic, cyberpunk",
                "cartoon": "cartoon style, colorful, expressive",
                "oil-painting": "oil painting style, classical art, textured",
                "watercolor": "watercolor painting, soft colors, artistic",
                "pixel-art": "pixel art style, retro gaming, 16-bit",
                "comic-book": "comic book style, bold lines, dynamic",
                "3d-render": "3d render, octane render, cinema 4d"
            }

            style_suffix = style_prompts.get(style, style_prompts["anime"])
            full_prompt = f"{prompt}, {style_suffix}, high quality, detailed"

            # Add negative prompt if provided
            if negative_prompt:
                full_prompt += f", avoid {negative_prompt}"

            # Parse resolution
            width, height = cls._parse_resolution(resolution)

            # Generate random seed
            seed = random.randint(1, 2147483647)

            # Encode prompt for URL
            encoded_prompt = urllib.parse.quote(full_prompt)

            # Build Pollinations.ai URL
            # Format: https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}&seed={s}
            image_url = f"{cls.BASE_URL}/{encoded_prompt}?width={width}&height={height}&seed={seed}&nologo=true"

            return True, image_url, seed, None

        except Exception as e:
            return False, None, None, str(e)

    @staticmethod
    def _parse_resolution(resolution: str) -> Tuple[int, int]:
        """Parse resolution string to width and height"""
        try:
            parts = resolution.lower().split('x')
            if len(parts) == 2:
                return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass
        # Default resolution
        return 512, 768
