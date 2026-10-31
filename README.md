# RA Property Studio AI — Every Property. A Story Worth Sharing.

> **Brand:** Realty Assistant | **Parent:** Viraj Ventures  
> Transform property photos and details into professional, cinematic promotional MP4 videos — fully automated with AI-powered scripts, Ken Burns effects, voiceover narration, and ambient soundtracks.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-4.2%2B-green.svg)](https://ffmpeg.org)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Brand Identity & Color System](#brand-identity--color-system)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Running the Application](#running-the-application)
- [Sample Data & Demo](#sample-data--demo)
- [API Documentation](#api-documentation)
- [Video Generation Pipeline](#video-generation-pipeline)
- [AI Models & Fallback Behavior](#ai-models--fallback-behavior)
- [Configuration Reference](#configuration-reference)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [Project Structure](#project-structure)

---

## Overview

**RA Property Studio AI** is an enterprise-grade full-stack web application created by **Realty Assistant** (part of **Viraj Ventures**) that turns property information, a draft script, and up to 8 uploaded photos into a professional, ready-to-share promotional video in MP4 format — **without requiring the user to manually edit a video**.

The application works without API keys using a deterministic template-based script generator and Edge TTS narration. With Gemini configured, it can refine a supplied narration draft and generate illustrative concept images to fill any missing scenes. Gemini generated images are labeled as concepts because they do not show the exact property.

---

## Brand Identity & Color System

- **Product Name:** RA Property Studio AI
- **Brand:** Realty Assistant
- **Parent Organization:** Viraj Ventures
- **Tagline:** *Every Property. A Story Worth Sharing.*
- **Color System:**
  - **Primary Blue:** `#344E8B`
  - **Accent Magenta:** `#A93478`
  - **Mid Purple:** `#67417F`
  - **Brand Gradient:** `linear-gradient(110deg, #344E8B 0%, #67417F 50%, #A93478 100%)`
  - **Main Background:** `#F7F7FC`
  - **Surface/Cards:** `#FFFFFF`
  - **Primary Text:** `#292943`
  - **Secondary Text:** `#686A7D`
  - **Borders:** `#E5E5EF`
  - **Success:** `#21865B`
  - **Error:** `#C53C53`

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React Frontend (Vite)                     │
│  Landing → Property Form → Storyboard Preview → Video Player │
│                    Tailwind CSS + Lucide Icons                 │
└──────────────┬───────────────────────────────────┬────────────┘
               │  HTTP API (Vite Proxy → :8000)    │
┌──────────────▼───────────────────────────────────▼────────────┐
│                   FastAPI Backend (Python)                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐ │
│  │ Property │ │  Script  │ │Storyboard │ │  Video Renderer  │ │
│  │Validation│ │Generator │ │  Service  │ │   (FFmpeg)       │ │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐ │
│  │   File   │ │  Audio   │ │    Job    │ │   Background     │ │
│  │ Storage  │ │ Service  │ │  Manager  │ │   Thread Pool    │ │
│  └──────────┘ └──────────┘ └───────────┘ └──────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Frontend**: React 19 + Vite 8 + Tailwind CSS 4 (dark premium real estate theme)  
**Backend**: Python + FastAPI + Pydantic v2  
**Rendering**: FFmpeg (via imageio-ffmpeg) — H.264 video, AAC audio, MP4 container  
**TTS**: Microsoft Edge TTS (free, no API key required)  
**LLM**: Configurable (Gemini / OpenAI / Groq / Template fallback)

---

## Features

- **Property Information Form**: Comprehensive form with validation for property name, location, price, type, features, bedrooms/bathrooms, contact info, and video settings
- **Image Upload**: Support for up to 8 images (JPEG, PNG, WebP) with drag-to-reorder, preview, and server-side validation; Gemini can generate missing scene concepts
- **AI Script Generation**: Theme-aware promotional scripts using LLM or deterministic template fallback; Gemini can polish a user draft while keeping claims grounded in property details
- **Storyboard Preview**: Visual scene-by-scene preview before rendering
- **Ken Burns Effects**: Subtle zoom and pan animations on property images
- **Text Overlays**: Theme-specific translucent info cards with typography, tags, and price badges
- **Voiceover Narration**: Scene-specific narration is synthesized per image and timed to its scene duration using Edge TTS (configurable voice)
- **Background Music**: Synthesized ambient soundtrack with volume ducking under narration
- **Video Formats**: 16:9 landscape or 9:16 vertical (Instagram/TikTok ready)
- **Duration Control**: 20, 30, or 40 second videos
- **Visual Themes**: Luxury (gold), Modern (cyan), Minimal (white), Elegant (rose gold)
- **Background Jobs**: Non-blocking video rendering with real-time progress updates
- **Download**: Direct MP4 download with clean filenames

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| **Python**  | 3.10+   | Tested with 3.12 |
| **Node.js** | 18+     | Tested with 22.x |
| **npm/pnpm**| Any     | For frontend dependencies |

> **FFmpeg** is bundled automatically via the `imageio-ffmpeg` Python package. No separate FFmpeg installation is required.

---

## Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd assignment
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest
```

### 3. Frontend setup

```bash
cd frontend

# Install Node.js dependencies
npm install
```

### 4. Environment configuration

```bash
# From the project root:
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/macOS

# Set LLM_PROVIDER=gemini and add your Gemini API key for script refinement and image generation.
# Add your MongoDB Atlas URI to enable GridFS and video library persistence.
```

The application loads settings from the project-root `.env` file. Replace the blank `LLM_API_KEY` and `MONGODB_URI` entries with your credentials; `.env` is ignored by git. Without Gemini, upload at least four photos to create a video.

### 5. FFmpeg verification

FFmpeg is bundled via `imageio-ffmpeg`. Verify it works:

```bash
python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
```

If you prefer using a system-installed FFmpeg, set `FFMPEG_PATH` in your `.env` file.

#### Installing FFmpeg system-wide (optional)

**Windows:**
```
# Using winget:
winget install FFmpeg

# Or download from https://www.gyan.dev/ffmpeg/builds/
# Extract and add bin/ folder to your PATH
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

---

## Running the Application

### Start the Backend (Terminal 1)

```bash
cd backend
python run.py
```

The API server starts at **http://127.0.0.1:8000**.  
API docs available at **http://127.0.0.1:8000/docs** (Swagger UI).

### Start the Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

The development server starts at **http://localhost:5173**.  
API requests are automatically proxied to the backend.

### Open the application

Navigate to **http://localhost:5173** in your browser.

---

## Sample Data & Demo

The application includes bundled demo data for **Greenview Residency** (Mohali, Punjab):

1. Click **"Try Sample Demo"** on the landing page
2. The form pre-fills with sample property details and 6 pre-bundled images
3. Click **"Generate Storyboard"** to preview the scene plan
4. Click **"Generate Video"** to render a real MP4

**Demo property details:**
- Property: Greenview Residency
- Location: Sector 82, Mohali, Punjab
- Price: ₹85 Lakh (2-BHK Apartment)
- Features: Modular Italian Kitchen, Spacious Balcony, Covered Parking, Natural Daylight
- Theme: Luxury (gold accents)

The demo generates a working MP4 using the template-based script generator and Edge TTS — no API keys required.

### Sample images

6 property images are bundled at `backend/app/assets/sample_properties/`:
- `1_exterior_facade.jpg` — Building exterior
- `2_living_room.jpg` — Living room interior
- `3_modular_kitchen.jpg` — Kitchen view
- `4_master_bedroom.jpg` — Bedroom
- `5_private_balcony.jpg` — Balcony with view
- `6_covered_parking.jpg` — Parking area

These are generated placeholder images created with PIL for demo purposes.

---

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | System health check (FFmpeg, LLM, TTS status) |
| `POST` | `/api/properties/validate` | Validate property input data |
| `POST` | `/api/images/upload` | Upload and validate a property image |
| `GET` | `/api/images/{image_id}/preview` | Serve uploaded image preview |
| `POST` | `/api/scripts/generate` | Generate promotional script |
| `POST` | `/api/storyboards/generate` | Generate visual storyboard |
| `POST` | `/api/videos/generate` | Submit video rendering job |
| `GET` | `/api/videos/jobs/{job_id}` | Poll video job status |
| `GET` | `/api/videos/{video_id}` | Get video metadata |
| `GET` | `/api/videos/{video_id}/stream` | Stream video for playback |
| `GET` | `/api/videos/{video_id}/download` | Download MP4 file |
| `GET` | `/api/samples/listing` | Get sample property listing |
| `GET` | `/api/samples/images/{filename}` | Serve sample images |

### Request/Response Examples

#### Validate Property

```bash
curl -X POST http://localhost:8000/api/properties/validate \
  -H "Content-Type: application/json" \
  -d '{
    "property_name": "Greenview Residency",
    "location": "Mohali, Punjab",
    "price": 8500000,
    "currency": "₹",
    "property_type": "apartment",
    "key_features": ["Modular Kitchen", "Balcony"],
    "bedrooms": 2,
    "bathrooms": 2,
    "cta_text": "Schedule a Visit",
    "duration": 30,
    "aspect_ratio": "16:9",
    "theme": "luxury",
    "image_ids": ["1_exterior_facade.jpg", "2_living_room.jpg", "3_modular_kitchen.jpg", "4_master_bedroom.jpg"]
  }'
```

#### Upload Image

```bash
curl -X POST http://localhost:8000/api/images/upload \
  -F "file=@property_photo.jpg"
```

#### Generate Video

```bash
curl -X POST http://localhost:8000/api/videos/generate \
  -H "Content-Type: application/json" \
  -d '{ ... PropertyInput JSON ... }'
# Returns: { "job_id": "uuid", "status": "queued", ... }

# Poll status:
curl http://localhost:8000/api/videos/jobs/{job_id}
```

Full interactive API documentation is available at **http://localhost:8000/docs** when the backend is running.

---

## Video Generation Pipeline

```
User Input → Validation → Script Generation → Storyboard → Video Rendering → MP4 Output
```

### Detailed Pipeline

1. **Input Validation**: Pydantic model validates all fields, image count (up to 8; Gemini fills missing scenes when configured), price > 0, duration in [20, 30, 40]

2. **Script Generation**: 
   - Tries configured LLM provider (Gemini/OpenAI/Groq) if API key is set
   - Falls back to deterministic template generator (always available)
   - Outputs: video title, opening hook, voiceover text, scene captions, closing CTA

3. **Storyboard Creation**:
   - Maps each uploaded image to a scene (opening, highlight, features, closing)
   - Calculates per-scene duration so total matches requested duration
   - Generates theme-specific overlay data (tags, badges, colors)

4. **Scene Rendering** (FFmpeg per scene):
   - Scale and center-crop image to target resolution (1920×1080 or 1080×1920)
   - Apply Ken Burns zoom effect (1.0→1.06 scale over duration)
   - Composite translucent overlay card with PIL-rendered typography
   - Encode to H.264 clip

5. **Audio Generation**:
   - Voiceover via Edge TTS (if narration enabled)
   - Background music from bundled ambient WAV
   - Audio mixing with volume ducking (music at 22% under narration)
   - Fade in/out on music

6. **Final Muxing**:
   - Concatenate all scene clips
   - Mux video + mixed audio
   - H.264 video, AAC audio, MP4 container with `faststart` flag
   - Validate output file integrity

---

## AI Models & Fallback Behavior

### Script Generation

| Provider | Model | API Key Required | Notes |
|----------|-------|-----------------|-------|
| **Template** (default) | N/A | No | Deterministic, always works |
| Gemini | gemini-1.5-flash | Yes | Google AI Studio |
| OpenAI | gpt-4o-mini | Yes | OpenAI API |
| Groq | llama-3.1-70b | Yes | Groq Cloud |

**Factuality Rules**: The script generator (both LLM and template) strictly uses only user-provided facts. It never invents prices, amenities, distances, sizes, or legal claims.

### Text-to-Speech

| Provider | API Key Required | Notes |
|----------|-----------------|-------|
| **edge_tts** (default) | No | Microsoft Edge TTS, free, requires internet |
| none | N/A | Disabled — renders silent video |

**Fallback**: If TTS fails (e.g., no internet), the video renders successfully without narration.

### Cascading Fallback Chain

```
LLM Script → Template Script (if LLM fails)
Edge TTS → Silent video (if TTS fails)
Ken Burns → Simple scale (if FFmpeg zoompan fails)
Background music → No music (if WAV not found)
MongoDB Atlas (GridFS & Metadata) → Local storage & in-memory jobs (if unconfigured/offline)
```

The application always produces a valid MP4 and maintains full functionality, even with all external services or databases unavailable.

---

## MongoDB Atlas Storage

RA Property Studio AI includes enterprise storage support for **MongoDB Atlas** with **GridFS**:

- **Collections**:
  - `jobs`: Stores video generation jobs, progress percentages, and current stage messages.
  - `videos`: Catalogs completed video records with duration, resolution, property details, and download links.
  - `properties`: Persists submitted property inputs and parameters.
  - `storyboards`: Archives generated scene sequences and overlay text.
- **GridFS Binary Storage**:
  - Automatically stores uploaded property photos and rendered MP4 promotional videos directly in Atlas GridFS when configured.
  - Supports chunked storage, making it suitable for high-definition video files.
  - Built-in caching: assets stored in GridFS are transparently streamed or downloaded to local disk as needed.
- **Graceful Fallback**:
  - If `MONGODB_URI` is not set or network is unreachable, the system automatically falls back to local disk storage (`storage/uploads`, `storage/outputs`) and in-memory job dictionaries.

To enable MongoDB Atlas, add your connection string to `.env`:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=ra_property_studio
MONGODB_GRIDFS_ENABLED=true
```

Connection health is reported live on `GET /api/health`.

---

## Configuration Reference

All configuration is via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `template` | Script generation provider: template, gemini, openai, groq |
| `LLM_API_KEY` | (empty) | API key for LLM provider |
| `LLM_MODEL` | `gemini-3.8-flash` | Text model for script refinement |
| `GEMINI_IMAGE_MODEL` | `gemini-3.1-flash-image` | Gemini image model for missing scene concepts |
| `TTS_PROVIDER` | `edge_tts` | TTS provider: edge_tts, none |
| `TTS_VOICE_EN` | `en-US-ChristopherNeural` | English TTS voice |
| `TTS_VOICE_IN` | `en-IN-PrabhatNeural` | Indian English TTS voice |
| `FFMPEG_PATH` | (auto-detect) | Custom FFmpeg binary path |
| `MONGODB_URI` | (empty) | MongoDB Atlas connection string (`mongodb+srv://...`) |
| `MONGODB_DB_NAME` | `ra_property_studio` | MongoDB database name |
| `MONGODB_GRIDFS_ENABLED` | `true` | Enable GridFS binary storage for images & MP4s |
| `HOST` | `0.0.0.0` | Server bind host |
| `PORT` | `8000` | Server bind port |

---

## Testing

### Running Tests

```bash
cd backend
pip install pytest

# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_api.py -v -k "health"
python -m pytest tests/test_api.py -v -k "validation"
python -m pytest tests/test_api.py -v -k "upload"
python -m pytest tests/test_api.py -v -k "script"
python -m pytest tests/test_api.py -v -k "storyboard"
```

### Test Categories

- **Health check**: Verifies /api/health returns proper structure
- **Property validation**: Missing fields, invalid prices, image count bounds, duration validation
- **Image upload**: Valid JPEG uploads, invalid file types, corrupted images
- **Script generation**: Template fallback, required fields present, factual content
- **Storyboard generation**: Scene count matches images, duration sums correctly, overlay data
- **Sample data**: Demo listing accessible, sample images served
- **Video jobs**: Job creation, status polling, 404 for missing jobs

### Manual End-to-End Test

1. Start both backend and frontend servers
2. Click "Try Sample Demo" on the landing page
3. Click "Generate Storyboard" — verify scenes display correctly
4. Click "Generate Video" — watch progress through all stages
5. When complete, verify video plays in the browser player
6. Click "Download MP4" — verify file downloads and plays in VLC/media player

---

## Troubleshooting

### FFmpeg not found

```
Error: FFmpeg binary not found
```

**Solution**: The `imageio-ffmpeg` package bundles FFmpeg. Verify installation:
```bash
pip install imageio-ffmpeg==0.5.1
python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
```

Or install FFmpeg system-wide and set `FFMPEG_PATH` in `.env`.

### Edge TTS connection error

```
Warning: Voiceover generation failed with edge-tts
```

**Cause**: Edge TTS requires an internet connection.  
**Impact**: Video renders successfully without narration. Not a fatal error.

### Import errors on backend start

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**: Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend proxy errors

```
Error: connect ECONNREFUSED 127.0.0.1:8000
```

**Cause**: Backend is not running.  
**Solution**: Start the backend first: `cd backend && python run.py`

### Video rendering takes too long

Video rendering is CPU-intensive. A 30-second video with 6 scenes typically takes 30–90 seconds depending on hardware. The progress indicator shows real-time status.

### Unicode/emoji in property details

The renderer handles Unicode text safely. However, some special characters may not render if the system font doesn't support them.

---

## Known Limitations

1. **In-memory job storage**: Video jobs are stored in memory and lost on server restart. A production deployment would use a database or Redis.
2. **Single-server**: The background thread pool (3 workers) runs on the same process. Not suitable for high-concurrency production use.
3. **FFmpeg 4.2.2**: The bundled FFmpeg via imageio-ffmpeg is v4.2.2. Some advanced filter features require newer versions.
4. **Edge TTS requires internet**: Voiceover generation needs network access. Falls back gracefully to silent video.
5. **No persistent file cleanup**: Generated videos accumulate in `backend/storage/outputs/`. Manual cleanup or a cron job is recommended for long-running deployments.
6. **No user authentication**: The application is designed for single-user local use. No auth layer is implemented.
7. **Font availability**: Text rendering quality depends on system fonts (Segoe UI on Windows, DejaVu Sans on Linux).

---

## Project Structure

```
assignment/
├── .env.example              # Environment configuration template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
│
├── backend/
│   ├── run.py                # Application entry point (uvicorn launcher)
│   ├── requirements.txt      # Python dependencies
│   ├── pytest.ini            # Test configuration
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # Central configuration & settings
│   │   ├── main.py           # FastAPI app, CORS, routers
│   │   │
│   │   ├── models/           # Pydantic data models
│   │   │   ├── property.py   # PropertyInput, ValidationResponse
│   │   │   ├── storyboard.py # StoryboardScene, ScriptOutput, StoryboardOutput
│   │   │   └── job.py        # VideoJob, JobStatus, OutputMetadata
│   │   │
│   │   ├── routes/           # API endpoint handlers
│   │   │   ├── health.py     # GET /api/health
│   │   │   ├── properties.py # POST /api/properties/validate
│   │   │   ├── images.py     # POST /api/images/upload, GET preview
│   │   │   ├── scripts.py    # POST /api/scripts/generate
│   │   │   ├── storyboards.py# POST /api/storyboards/generate
│   │   │   ├── videos.py     # POST /api/videos/generate, GET status/stream/download
│   │   │   └── samples.py    # GET /api/samples/listing, images
│   │   │
│   │   ├── services/         # Business logic
│   │   │   ├── file_storage.py     # Image validation, UUID storage, path resolution
│   │   │   ├── script_generator.py # LLM + deterministic script generation
│   │   │   ├── storyboard_service.py # Scene planning, duration calculation
│   │   │   ├── video_renderer.py   # FFmpeg rendering pipeline (Ken Burns, overlays)
│   │   │   ├── audio_service.py    # Edge TTS voiceover, background music
│   │   │   └── job_manager.py      # Thread pool job manager
│   │   │
│   │   └── assets/
│   │       ├── generate_assets.py  # Script to regenerate demo assets
│   │       ├── audio/
│   │       │   └── ambient_lounge.wav  # Background music
│   │       └── sample_properties/      # 6 demo property images
│   │
│   ├── storage/              # Runtime storage (gitignored)
│   │   ├── uploads/          # Uploaded images
│   │   └── outputs/          # Generated MP4 videos
│   │
│   └── tests/
│       └── test_api.py       # Automated test suite
│
└── frontend/
    ├── package.json          # Node.js dependencies
    ├── vite.config.js        # Vite config with API proxy
    ├── index.html            # HTML entry (dark theme, fonts)
    │
    └── src/
        ├── main.jsx          # React entry point
        ├── index.css         # Tailwind + custom design system
        ├── App.jsx           # Multi-step wizard controller
        ├── App.css           # Animations
        │
        └── components/
            ├── LandingScreen.jsx     # Hero landing page
            ├── PropertyForm.jsx      # Property details + image upload form
            ├── StoryboardPreview.jsx # Scene-by-scene storyboard review
            ├── VideoGenerating.jsx   # Progress tracking during render
            └── VideoComplete.jsx     # Video player + download
```

---

## License

This project is created as an assignment for a software engineering placement assessment.

