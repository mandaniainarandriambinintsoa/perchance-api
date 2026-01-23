# Artigen API

Free AI Image Generator API using Pollinations.ai.

## Features

- Text-to-Image generation with multiple styles
- Image-to-Image transformation (requires API token)
- Multiple AI models (Sana, Turbo, etc.)
- NSFW content supported (safe mode optional)

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy the environment file:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /health` - Health check
- `GET /api/v1/styles` - List available art styles
- `GET /api/v1/models` - List available AI models
- `POST /api/v1/generate` - Generate an image from text
- `POST /api/v1/generate/img2img` - Transform an existing image

### Generate Image

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "beautiful sunset over mountains",
    "style": "realistic",
    "resolution": "1024x1024",
    "model": "sana"
  }'
```

### Available Styles

- realistic, photorealistic, cinematic, portrait
- anime, fantasy, sci-fi, 3d-render

### Available Models

- `sana` - High quality realistic images (recommended)
- `turbo` - Fast generation
- `zimage` - Alternative model

## Deployment (Railway)

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Procfile
3. Set environment variables:
   - `ALLOWED_ORIGINS` - CORS allowed origins

## Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
