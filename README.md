# Perchance API

A FastAPI wrapper for Perchance.org AI character generation.

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
- `POST /api/v1/generate` - Generate a character image

### Generate Character

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "anime girl with blue hair",
    "style": "anime",
    "resolution": "512x768"
  }'
```

## Deployment (Railway)

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Procfile
3. Set environment variables as needed

## Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
