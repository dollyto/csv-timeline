# CSV Timeline

A Flask web application for processing CSV files with timeline data and generating script segments with voice assignments.

## Features

- Upload and process CSV files with timeline data
- Upload video files for preview
- Assign ElevenLabs voices to script segments
- Export processed data back to CSV format
- Web-based interface for easy interaction

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```bash
   export ELEVENLABS_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```bash
   python app.py
   ```
6. Open http://localhost:8080 in your browser

## Deployment Options

### Option 1: Railway (Recommended for Video Processing)

Railway offers better performance for video processing with a generous free tier.

#### Prerequisites
1. A Railway account at [railway.app](https://railway.app)
2. Your code pushed to a Git repository

#### Deployment Steps
1. **Connect to Railway:**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure the service:**
   - Railway will automatically detect it's a Python app
   - The `railway.json` file will configure the deployment

3. **Set environment variables:**
   - Go to the "Variables" tab
   - Add `ELEVENLABS_API_KEY` with your API key (optional)

4. **Deploy:**
   - Railway will automatically build and deploy

#### Advantages
- **Better Performance:** 2GB RAM, 2 CPU cores on paid plan
- **FFmpeg Support:** Built-in support for video processing
- **Cost-Effective:** $5/month credit on free tier

### Option 2: Fly.io (Best Free Tier)

Fly.io offers the most generous free tier for video processing.

#### Prerequisites
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. Sign up at [fly.io](https://fly.io)
3. Run `fly auth login`

#### Deployment Steps
1. **Deploy with Fly CLI:**
   ```bash
   fly launch
   ```
   - Follow the prompts
   - Use the app name: `csv-timeline`

2. **Set environment variables:**
   ```bash
   fly secrets set ELEVENLABS_API_KEY=your_api_key
   ```

3. **Deploy:**
   ```bash
   fly deploy
   ```

#### Advantages
- **Generous Free Tier:** 3 shared-cpu-1x 256mb VMs, 3GB storage
- **Good Performance:** 2GB RAM available on paid plan
- **Docker-based:** More control over the environment

### Option 3: Render (Current)

Render's free tier is limited for video processing but works for basic usage.

#### Prerequisites
1. A Render account (free tier available)
2. Your code pushed to a Git repository

#### Deployment Steps
1. **Connect your repository to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your Git repository

2. **Configure the service:**
   - **Name:** csv-timeline
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

3. **Set environment variables:**
   - Go to the "Environment" tab
   - Add `ELEVENLABS_API_KEY` with your API key (optional)

#### Limitations
- **Limited Resources:** 512MB RAM, 0.5 CPU cores on free tier
- **Video Processing:** May timeout on large files
- **Memory Constraints:** Worker timeouts common with video processing

### Option 4: DigitalOcean App Platform

Good performance with a credit-based free tier.

#### Prerequisites
1. DigitalOcean account with $200 credit
2. Your code pushed to a Git repository

#### Deployment Steps
1. **Create App:**
   - Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App" → "Create App from Source Code"
   - Connect your GitHub repository

2. **Configure:**
   - **Source Directory:** `/`
   - **Build Command:** `pip install -r requirements.txt`
   - **Run Command:** `gunicorn app:app`

3. **Set environment variables:**
   - Add `ELEVENLABS_API_KEY` in the environment section

#### Advantages
- **Good Performance:** 2GB RAM, 1 CPU core
- **Reliable:** Excellent uptime and performance
- **Credit Available:** $200 free credit for 60 days

## Platform Comparison

| Platform | Free Tier | Paid Starting | Video Processing | Recommended |
|----------|-----------|---------------|------------------|-------------|
| **Railway** | $5/month credit | $20/month | ✅ Excellent | ⭐⭐⭐⭐⭐ |
| **Fly.io** | 3 VMs, 3GB storage | $1.94/month | ✅ Good | ⭐⭐⭐⭐ |
| **DigitalOcean** | $200 credit | $12/month | ✅ Good | ⭐⭐⭐⭐ |
| **Render** | 512MB RAM | $7/month | ⚠️ Limited | ⭐⭐ |

## Minimum Requirements for Video Processing

For reliable video processing, you need:
- **RAM:** 2GB+ (video processing is memory-intensive)
- **CPU:** 2+ cores (for FFmpeg processing)
- **Storage:** 10GB+ (for video files)
- **Network:** Good bandwidth for uploads

**Recommendation:** Start with Railway or Fly.io for the best free tier experience with video processing capabilities.

## Environment Variables

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key for voice features
- `PORT`: Port number (automatically set by Render)

## File Structure

```
CSV Timeline/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment configuration
├── templates/
│   └── index.html       # Web interface
├── uploads/             # Upload directory (ephemeral on Render)
└── README.md           # This file
```

## API Endpoints

- `GET /`: Main application interface
- `GET /get-voices`: Fetch available ElevenLabs voices
- `POST /upload-csv`: Upload and process CSV files
- `POST /upload-video`: Upload video files for preview
- `POST /export-csv`: Export processed data to CSV
- `GET /uploads/<filename>`: Serve uploaded files

## CSV Format Requirements

Your CSV file should contain the following columns:
- `speaker`: Speaker name
- `start_time`: Start time in one of these formats:
  - `00.167` (decimal seconds)
  - `00:00:00` (hours:minutes:seconds)
  - `00:00:00:00` (hours:minutes:seconds:frames)
  - `00:00:00.000` (hours:minutes:seconds.milliseconds)
- `end_time`: End time in the same format as start_time
- One column containing script/transcription text (will be auto-detected)

## License

This project is open source and available under the MIT License. 