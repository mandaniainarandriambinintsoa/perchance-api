# Artigen - Projet de Génération d'Images IA

## Vue d'ensemble

Ce projet contient **2 repositories** pour une application de génération d'images IA utilisant **Pollinations.ai** :

1. **perchance-api** - Backend API (FastAPI/Python)
2. **perchance-webapp** - Frontend Web (Next.js/React/TypeScript)

---

## 1. PERCHANCE-API (Backend)

### Stack technique
- **Framework**: FastAPI (Python 3.11+)
- **Serveur**: Uvicorn
- **Validation**: Pydantic
- **Service d'IA**: Pollinations.ai (via `gen.pollinations.ai`, nécessite API key)
- **HTTP Client**: `httpx` (async, streaming)

### Structure du projet
```
perchance-api/
├── app/
│   ├── main.py              # Point d'entrée FastAPI + keep-alive
│   ├── config.py            # Configuration et variables d'environnement
│   ├── routes/
│   │   ├── generate.py      # POST /api/v1/generate, POST /api/v1/generate/img2img, queue endpoints
│   │   └── styles.py        # GET /api/v1/styles, GET /api/v1/models
│   ├── schemas/
│   │   └── generate.py      # Modèles Pydantic
│   └── services/
│       ├── pollinations.py  # Service PerchanceService (utilise gen.pollinations.ai)
│       └── queue_service.py # File d'attente en mémoire pour la génération
├── requirements.txt
└── .env                     # ALLOWED_ORIGINS, POLLINATIONS_TOKEN
```

### Endpoints API

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/` | Info API |
| GET | `/health` | Health check |
| GET | `/api/v1/styles` | Liste des styles disponibles |
| GET | `/api/v1/models` | Liste des modèles IA disponibles |
| POST | `/api/v1/generate` | Générer une image |
| POST | `/api/v1/generate/img2img` | Transformer une image (image-to-image) |
| POST | `/api/v1/generate/queue` | Générer via file d'attente (non-bloquant) |
| GET | `/api/v1/generate/queue/{job_id}` | Status d'un job en queue |
| GET | `/api/v1/generate/queue` | Status global de la queue |

### POST /api/v1/generate - Corps de requête
```json
{
  "prompt": "description de l'image",
  "style": "realistic",           // défaut: realistic
  "resolution": "512x768",        // défaut: 512x768
  "model": "flux",                // défaut: flux
  "negative_prompt": "flou",      // optionnel
  "enhance": true                 // amélioration IA du prompt (défaut: true)
}
```

### POST /api/v1/generate/img2img - Corps de requête
```json
{
  "prompt": "transformation à appliquer",
  "image_url": "https://example.com/image.jpg",
  "style": "anime",               // optionnel
  "resolution": "512x768",        // optionnel
  "negative_prompt": "flou"       // optionnel
}
```

### Réponse
```json
{
  "success": true,
  "image_url": "https://gen.pollinations.ai/image/...",
  "seed": 12345,
  "model": "flux"
}
```

### Styles disponibles (8) - Optimisés pour le réalisme
- **realistic** - Photoréaliste, haute définition
- **photorealistic** - Photo RAW, hyperdetaillée
- **cinematic** - Plan cinématographique, éclairage dramatique
- **portrait** - Photographie portrait professionnelle
- **anime** - Style animation japonaise
- **fantasy** - Art fantastique, magique
- **sci-fi** - Science-fiction, cyberpunk
- **3d-render** - Rendu 3D, Octane, Unreal Engine

### Modèles IA disponibles (2 + premium)
| Modèle | Description | Tier |
|--------|-------------|------|
| **flux** | Flux Schnell - Rapide, haute qualité | Gratuit (recommandé) |
| **zimage** | Z-Image Turbo - Rapide avec upscaling 2x | Gratuit |
| **kontext** | Transformation d'images | Image-to-image uniquement |
| *seedream* | Seedream 4.0 - ByteDance (meilleure qualité) | Premium (402) |
| *gptimage* | GPT Image 1 Mini - OpenAI | Premium (402) |
| *imagen-4* | Imagen 4 - Google | Premium (402) |

### Comment ça fonctionne

#### Génération d'image
1. L'API reçoit une requête avec prompt, style, modèle
2. Elle construit un prompt enrichi avec le suffixe du style
3. Elle appelle `gen.pollinations.ai/image/` avec la clé API en streaming httpx
4. L'API retourne l'URL (sans la clé API exposée)

#### Image-to-image (kontext)
1. L'API reçoit une URL d'image source + prompt de transformation
2. Elle utilise le modèle `kontext` avec le paramètre `image=`
3. L'image est retournée en base64 (pour ne pas exposer la clé API)

#### Keep-alive (Render)
- Un background task ping `/health` toutes les 10 minutes
- Activé uniquement si `RENDER_EXTERNAL_URL` est défini (auto-injecté par Render)
- Empêche le free tier Render de mettre le service en veille

### Code du service (pollinations.py)
```python
import httpx
from urllib.parse import quote

BASE_URL = "https://gen.pollinations.ai/image"

# Génération d'image (streaming pour chunked responses)
url = f"{BASE_URL}/{quote(prompt)}?width={w}&height={h}&model=flux&nologo=true&enhance=true&key={token}"
timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
    async with client.stream("GET", url) as response:
        await response.aread()

# Image-to-image
url = f"{BASE_URL}/{quote(prompt)}?model=kontext&image={quote(image_url)}&key={token}"
```

### Commandes
```bash
# Développement
cd perchance-api
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Production (Render)
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Configuration (.env)
```
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.vercel.app
POLLINATIONS_TOKEN=sk_xxxxx  # Clé API obligatoire (https://enter.pollinations.ai)
```

### Dépendances (requirements.txt)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.27.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

---

## 2. PERCHANCE-WEBAPP (Frontend)

### Stack technique
- **Framework**: Next.js 14 (App Router)
- **UI**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Composants**: shadcn/ui + Radix UI
- **Icônes**: Lucide React

### Structure du projet
```
perchance-webapp/
├── src/
│   ├── app/
│   │   ├── layout.tsx       # Layout racine
│   │   ├── page.tsx         # Page principale (générateur)
│   │   └── globals.css      # Styles globaux + thème
│   ├── components/
│   │   ├── CharacterForm.tsx    # Formulaire de génération
│   │   ├── ImageDisplay.tsx     # Affichage de l'image + téléchargement
│   │   ├── LoadingState.tsx     # État de chargement
│   │   ├── StyleSelector.tsx    # Sélecteur de style
│   │   └── ui/                  # Composants shadcn/ui
│   ├── lib/
│   │   ├── api.ts           # Client API (ApiClient class)
│   │   └── utils.ts         # Utilitaires (cn pour les classes)
│   └── types/
│       └── index.ts         # Interfaces TypeScript
├── package.json
├── tailwind.config.ts
└── next.config.js           # Domaines d'images autorisés (gen.pollinations.ai)
```

### Client API (src/lib/api.ts)
```typescript
class ApiClient {
  getStyles(): Promise<StylesResponse>
  getModels(): Promise<ModelsResponse>
  generateImage(request: GenerateRequest, onStatus?: callback): Promise<GenerateResponse>
  imageToImage(request: ImageToImageRequest): Promise<GenerateResponse>
  checkHealth(): Promise<boolean>
}
```

### Commandes
```bash
# Développement
cd perchance-webapp
npm install
npm run dev  # localhost:3000

# Production
npm run build
npm run start
```

### Configuration (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Architecture globale

```
┌─────────────────┐     HTTP      ┌──────────────────┐    HTTP       ┌───────────────────┐
│  perchance-     │ ──────────── │  perchance-api   │ ───────────► │  gen.pollinations  │
│  webapp         │  Render URL  │  (FastAPI)       │  + API key   │  .ai (Image Gen)   │
│  (Next.js)      │              │  Render          │              │                    │
│  Vercel         │              │                  │              │                    │
└─────────────────┘              └──────────────────┘              └───────────────────┘
```

---

## Points clés à retenir

1. **API key requise**: `POLLINATIONS_TOKEN` (obtenir sur https://enter.pollinations.ai)
2. **Endpoint**: `gen.pollinations.ai/image/` (l'ancien `image.pollinations.ai` est down depuis fév 2026)
3. **Streaming httpx**: Nécessaire pour les réponses chunked de Pollinations (sinon timeout)
4. **Modèle par défaut**: `flux` (Flux Schnell - rapide et gratuit)
5. **Image-to-image**: Modèle `kontext` pour transformer des images existantes
6. **8 styles**: realistic, photorealistic, cinematic, portrait, anime, fantasy, sci-fi, 3d-render
7. **Modèles gratuits**: flux, zimage (les autres retournent 402)
8. **Keep-alive**: Self-ping toutes les 10 min pour empêcher Render de dormir
9. **NSFW**: `safe=true` pour activer le filtre (désactivé par défaut)
10. **Enhance**: Amélioration IA du prompt activée par défaut

---

## Déploiement

### Backend (perchance-api)
- **Platform**: Render.com (free tier)
- **Variables d'env**: `POLLINATIONS_TOKEN`, `ALLOWED_ORIGINS`, `RENDER_EXTERNAL_URL` (auto)
- **Python**: 3.11+

### Frontend (perchance-webapp)
- **Platform**: Vercel
- **Variable**: `NEXT_PUBLIC_API_URL` vers l'URL Render

---

## Démarrage rapide

### Prérequis
- Python 3.11+ (pour l'API)
- Node.js 18+ (pour le frontend)
- Clé API Pollinations (https://enter.pollinations.ai)

### Étape 1: Démarrer l'API Backend
```bash
cd perchance-api
pip install -r requirements.txt
# Configurer .env avec POLLINATIONS_TOKEN
python -m uvicorn app.main:app --reload --port 8000
```

### Étape 2: Démarrer le Frontend
```bash
cd perchance-webapp
npm install
npm run dev
```

### Vérification
- API Health check: http://localhost:8000/health
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Tests manuels

### Tester la génération d'image
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a beautiful sunset over mountains", "style": "cinematic", "model": "flux"}'
```

### Tester les styles / modèles / health
```bash
curl http://localhost:8000/api/v1/styles
curl http://localhost:8000/api/v1/models
curl http://localhost:8000/health
```

---

## Problèmes connus et solutions

### Erreur 530 (Cloudflare) sur image.pollinations.ai
**Cause**: L'ancien endpoint `image.pollinations.ai` est down depuis février 2026.
**Solution**: Migré vers `gen.pollinations.ai/image/` avec clé API.

### Erreur 401 (Unauthorized)
**Cause**: `POLLINATIONS_TOKEN` manquant ou invalide.
**Solution**: Configurer la variable d'env avec une clé valide de https://enter.pollinations.ai

### Erreur 402 (Payment Required)
**Cause**: Crédits insuffisants pour le modèle demandé (seedream, gptimage, imagen-4).
**Solution**: Utiliser `flux` ou `zimage` (gratuits).

### Timeout de génération
**Cause**: httpx ne gère pas bien les réponses chunked de Pollinations avec un timeout simple.
**Solution**: Utiliser `client.stream("GET", url)` + `response.aread()` avec des timeouts séparés (read: 300s).

### Erreur 422 (Unprocessable Content)
**Cause**: Le champ `prompt` est vide ou manquant.
**Solution**: Validation côté client + logs serveur détaillés.

### Render met l'API en veille
**Cause**: Free tier Render dort après 15 min d'inactivité.
**Solution**: Keep-alive intégré (self-ping /health toutes les 10 min via `RENDER_EXTERNAL_URL`).

---

## Historique des changements

### 2026-02-15 - V4 (Migration gen.pollinations.ai)
- **Migration endpoint**: `image.pollinations.ai` -> `gen.pollinations.ai/image/`
- **API key**: `POLLINATIONS_TOKEN` requise (gratuite via enter.pollinations.ai)
- **Nouveaux modèles**: flux (recommandé), zimage (gratuits)
- **Streaming httpx**: Résolution des timeouts sur réponses chunked
- **Keep-alive**: Self-ping toutes les 10 min pour Render free tier
- **Health check**: Corrigé vers le bon endpoint
- **Erreurs améliorées**: Messages clairs pour 401, 402

### 2025-01-19 - V3 (Debug & UI)
- **Logging amélioré**: Les erreurs 422 loggent le corps de la requête
- **Gestion erreurs frontend**: Messages d'erreur Pydantic lisibles
- **UI Tabs**: Interface avec onglets pour Text-to-Image et Image-to-Image
- **Design responsive**: Inspiré de Dribbble, adapté mobile/desktop

### 2025-01-19 - V2 (Amélioration réalisme)
- **Modèle par défaut**: `flux-realism` pour des rendus hyperréalistes
- **Image-to-image**: Nouveau endpoint avec modèle `kontext`
- **Nouveaux styles**: Optimisés pour le photoréalisme

### 2025-01-19 - V1 (Migration Pollinations)
- **Migration de Perchance.org vers Pollinations.ai**
