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

## Deployment to Render

### Prerequisites

1. A Render account (free tier available)
2. Your code pushed to a Git repository (GitHub, GitLab, etc.)
3. ElevenLabs API key (optional, for voice features)

### Deployment Steps

1. **Connect your repository to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" and select "Web Service"
   - Connect your Git repository

2. **Configure the service:**
   - **Name:** csv-timeline (or your preferred name)
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

3. **Set environment variables:**
   - Go to the "Environment" tab
   - Add `ELEVENLABS_API_KEY` with your API key (optional)

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Important Notes

- **File Storage:** Render uses an ephemeral filesystem, so uploaded files will be lost when the service restarts. For production use, consider integrating with cloud storage (AWS S3, Google Cloud Storage, etc.).
- **FFmpeg:** The application uses FFmpeg for video processing. If you need video conversion features, you'll need to ensure FFmpeg is available in your deployment environment.
- **Free Tier Limitations:** The free tier has limitations on build time and runtime. For production use, consider upgrading to a paid plan.

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