import random
import httpx
from typing import Optional, Tuple, List
from urllib.parse import quote
from app.config import POLLINATIONS_TOKEN


class PerchanceService:
    """Service wrapper for AI image generation using Pollinations.ai"""

    # Unified API endpoint (requires API key since Feb 2026)
    BASE_URL = "https://gen.pollinations.ai/image"
    DEFAULT_MODEL = "seedream-pro"

    AVAILABLE_STYLES = [
        "realistic",
        "photorealistic",
        "cinematic",
        "portrait",
        "anime",
        "fantasy",
        "sci-fi",
        "3d-render"
    ]

    # Curated Pollinations models. Seedream 4.5 Pro is the quality-first
    # default for Artigen's photorealistic scenes and portraits.
    AVAILABLE_MODELS = {
        "seedream-pro": "Seedream 4.5 Pro - Best photorealism for lifelike scenes and portraits (recommended, premium)",
        "seedream": "Seedream 4.0 - Photorealistic images with strong prompt adherence (premium)",
        "klein": "FLUX.2 Klein 4B - Fast generation and editing up to 2.4 MP",
        "zimage": "Z-Image Turbo - Fast, budget-friendly generation with crisp upscaling",
        "flux": "Flux Schnell - Fast generation at low cost",
    }

    # Prompts de style optimisés pour le réalisme maximum
    STYLE_PROMPTS = {
        "realistic": "ultra realistic photograph, real person, real human, natural skin texture, pores visible, authentic human features, professional DSLR photo, Canon EOS R5, 85mm f/1.4 lens, natural lighting, unedited raw photo, no AI artifacts, genuine photograph",
        "photorealistic": "real photograph, not AI generated, actual photo, genuine human, natural imperfections, authentic skin texture, RAW unprocessed photo, professional photography, Hasselblad camera, medium format, true to life, documentary style",
        "cinematic": "cinematic film still, real movie scene, 35mm film, Arri Alexa camera, anamorphic lens, natural film grain, Hollywood production quality, real actors, authentic cinematography, color graded",
        "portrait": "real portrait photograph, actual person, genuine human face, natural skin with pores and texture, studio photography, Profoto lighting, 85mm portrait lens, shallow depth of field, magazine quality, unretouched natural beauty",
        "anime": "anime style, japanese animation, vibrant colors, detailed linework, studio ghibli quality",
        "fantasy": "fantasy art, magical atmosphere, ethereal lighting, highly detailed digital painting, concept art quality",
        "sci-fi": "science fiction scene, futuristic technology, cyberpunk aesthetics, neon lighting, detailed environment",
        "3d-render": "3d render, octane render, cinema 4d, unreal engine 5, photorealistic materials, ray tracing, subsurface scattering"
    }

    # Negative prompts par défaut pour éviter les artefacts AI
    DEFAULT_NEGATIVE = "cartoon, anime, illustration, drawing, painting, sketch, artificial, fake, cgi, 3d render, digital art, plastic skin, mannequin, doll, wax figure, unrealistic, ai generated look, oversaturated, overprocessed"

    @classmethod
    def get_styles(cls) -> List[str]:
        """Return list of available styles"""
        return cls.AVAILABLE_STYLES

    @classmethod
    def get_models(cls) -> dict:
        """Return dict of available models with descriptions"""
        return cls.AVAILABLE_MODELS

    @classmethod
    def _parse_resolution(cls, resolution: str) -> Tuple[int, int]:
        """Parse resolution string to width and height"""
        try:
            width, height = resolution.split("x")
            return int(width), int(height)
        except (ValueError, AttributeError):
            return 512, 768  # Default

    @classmethod
    async def generate_image(
        cls,
        prompt: str,
        style: str = "realistic",
        resolution: str = "512x768",
        negative_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        safe: bool = False,
        enhance: bool = True
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Generate an image using Pollinations.ai

        Args:
            prompt: Image description
            style: Art style to apply (realistic, photorealistic, cinematic, etc.)
            resolution: Image resolution (e.g., "512x768")
            negative_prompt: Things to avoid in the image
            model: Pollinations model (seedream-pro, seedream, klein, zimage, flux)
            safe: Enable NSFW filter (default: False)
            enhance: Enable AI prompt enhancement (default: True)

        Returns:
            Tuple of (success, image_url, seed, error_message)
        """
        try:
            # Build the full prompt with style
            style_suffix = cls.STYLE_PROMPTS.get(style, cls.STYLE_PROMPTS["realistic"])
            full_prompt = f"{prompt}, {style_suffix}"

            # Add negative prompt - use default for realistic styles if none provided
            realistic_styles = ["realistic", "photorealistic", "cinematic", "portrait"]
            if negative_prompt:
                full_prompt += f". Avoid: {negative_prompt}"
            elif style in realistic_styles:
                full_prompt += f". Avoid: {cls.DEFAULT_NEGATIVE}"

            # Parse resolution
            width, height = cls._parse_resolution(resolution)

            # Generate seed for reproducibility
            seed = random.randint(1, 2147483647)

            encoded_prompt = quote(full_prompt)

            url = (
                f"{cls.BASE_URL}/{encoded_prompt}"
                f"?width={width}"
                f"&height={height}"
                f"&seed={seed}"
                f"&model={model}"
                f"&nologo=true"
            )

            if safe:
                url += "&safe=true"
            if enhance:
                url += "&enhance=true"

            if POLLINATIONS_TOKEN:
                url += f"&key={POLLINATIONS_TOKEN}"
            else:
                return False, None, None, "POLLINATIONS_TOKEN is not configured. Get a free API key at https://enter.pollinations.ai"

            # Fetch image from Pollinations using streaming to handle chunked responses
            timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code == 401:
                        return False, None, None, "Invalid or expired API key. Check your POLLINATIONS_TOKEN."
                    if response.status_code == 402:
                        return False, None, None, f"Insufficient credits for model '{model}'. Try 'klein', 'zimage', or 'flux'."
                    if response.status_code != 200:
                        return False, None, None, f"Pollinations API error: {response.status_code}"

                    # Read the full response to ensure generation is complete
                    await response.aread()

                # Return URL without the API key
                public_url = url.split("&key=")[0]
                return True, public_url, seed, None

        except httpx.TimeoutException:
            return False, None, None, "Image generation timed out"
        except Exception as e:
            return False, None, None, str(e)

    @classmethod
    async def generate_image_base64(
        cls,
        prompt: str,
        style: str = "realistic",
        resolution: str = "512x768",
        negative_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        safe: bool = False,
        enhance: bool = True
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Generate an image and return as base64 data URI

        Same as generate_image but returns base64 instead of URL
        """
        import base64

        try:
            # Build the full prompt with style
            style_suffix = cls.STYLE_PROMPTS.get(style, cls.STYLE_PROMPTS["realistic"])
            full_prompt = f"{prompt}, {style_suffix}"

            # Add negative prompt - use default for realistic styles if none provided
            realistic_styles = ["realistic", "photorealistic", "cinematic", "portrait"]
            if negative_prompt:
                full_prompt += f". Avoid: {negative_prompt}"
            elif style in realistic_styles:
                full_prompt += f". Avoid: {cls.DEFAULT_NEGATIVE}"

            width, height = cls._parse_resolution(resolution)
            seed = random.randint(1, 2147483647)

            encoded_prompt = quote(full_prompt)

            url = (
                f"{cls.BASE_URL}/{encoded_prompt}"
                f"?width={width}"
                f"&height={height}"
                f"&seed={seed}"
                f"&model={model}"
                f"&nologo=true"
            )

            if safe:
                url += "&safe=true"
            if enhance:
                url += "&enhance=true"

            if POLLINATIONS_TOKEN:
                url += f"&key={POLLINATIONS_TOKEN}"
            else:
                return False, None, None, "POLLINATIONS_TOKEN is not configured. Get a free API key at https://enter.pollinations.ai"

            # Fetch and convert to base64
            timeout = httpx.Timeout(connect=30.0, read=180.0, write=30.0, pool=30.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    return False, None, None, f"Pollinations API error: {response.status_code}"

                # Convert to base64 data URI
                image_bytes = response.content
                base64_image = base64.b64encode(image_bytes).decode('utf-8')

                # Detect content type from response headers or default to jpeg
                content_type = response.headers.get("content-type", "image/jpeg")
                image_url = f"data:{content_type};base64,{base64_image}"

                return True, image_url, seed, None

        except httpx.TimeoutException:
            return False, None, None, "Image generation timed out"
        except Exception as e:
            return False, None, None, str(e)

    @classmethod
    async def image_to_image(
        cls,
        prompt: str,
        image_url: str,
        style: str = "realistic",
        resolution: str = "512x768",
        negative_prompt: Optional[str] = None,
        safe: bool = False
    ) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
        """
        Transform an existing image using kontext model (image-to-image)

        Args:
            prompt: Description of the transformation to apply
            image_url: URL of the input image to transform
            style: Art style to apply
            resolution: Output image resolution
            negative_prompt: Things to avoid in the generation
            safe: Enable NSFW filter (default: False)

        Returns:
            Tuple of (success, image_url, seed, error_message)
        """
        try:
            # Build the full prompt with style
            style_suffix = cls.STYLE_PROMPTS.get(style, cls.STYLE_PROMPTS["realistic"])
            full_prompt = f"{prompt}, {style_suffix}"

            if negative_prompt:
                full_prompt += f". Avoid: {negative_prompt}"

            width, height = cls._parse_resolution(resolution)
            seed = random.randint(1, 2147483647)

            # Build Pollinations URL with kontext model for img2img
            encoded_prompt = quote(full_prompt)
            encoded_image_url = quote(image_url, safe='')

            url = (
                f"{cls.BASE_URL}/{encoded_prompt}"
                f"?width={width}"
                f"&height={height}"
                f"&seed={seed}"
                f"&model=kontext"
                f"&image={encoded_image_url}"
                f"&nologo=true"
            )

            if POLLINATIONS_TOKEN:
                url += f"&key={POLLINATIONS_TOKEN}"
            else:
                return False, None, None, "POLLINATIONS_TOKEN is not configured. Get a free API key at https://enter.pollinations.ai"

            if safe:
                url += "&safe=true"

            # Fetch image from Pollinations
            timeout = httpx.Timeout(connect=30.0, read=180.0, write=30.0, pool=30.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code == 429:
                    # Rate limit exceeded
                    try:
                        error_data = response.json()
                        retry_after = error_data.get("retryAfterSeconds", 30)
                        return False, None, None, f"Rate limit exceeded. Please wait {int(retry_after)} seconds before trying again."
                    except (ValueError, KeyError):
                        return False, None, None, "Rate limit exceeded. Please wait 30 seconds before trying again."

                if response.status_code != 200:
                    return False, None, None, f"Pollinations API error: {response.status_code}"

                # Convert image to base64 to avoid exposing API key in URL
                import base64
                image_bytes = response.content
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                content_type = response.headers.get("content-type", "image/jpeg")
                image_data_url = f"data:{content_type};base64,{base64_image}"

                return True, image_data_url, seed, None

        except httpx.TimeoutException:
            return False, None, None, "Image transformation timed out"
        except Exception as e:
            return False, None, None, str(e)
