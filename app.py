import os
import pandas as pd
import re
import subprocess
import tempfile
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import json
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB max file size

# ElevenLabs API configuration
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')
ELEVENLABS_BASE_URL = 'https://api.elevenlabs.io/v1'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Allowed video file extensions
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv'}

def allowed_video_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def get_elevenlabs_voices():
    """Fetch available voices from ElevenLabs API"""
    if not ELEVENLABS_API_KEY:
        return []
    
    try:
        headers = {
            'xi-api-key': ELEVENLABS_API_KEY
        }
        
        response = requests.get(f'{ELEVENLABS_BASE_URL}/voices', headers=headers)
        
        if response.status_code == 200:
            voices_data = response.json()
            voices = []
            
            for voice in voices_data.get('voices', []):
                voices.append({
                    'voice_id': voice.get('voice_id'),
                    'name': voice.get('name'),
                    'category': voice.get('category', ''),
                    'description': voice.get('description', ''),
                    'labels': voice.get('labels', {})
                })
            
            return voices
        else:
            app.logger.error(f'ElevenLabs API error: {response.status_code} - {response.text}')
            return []
            
    except Exception as e:
        app.logger.error(f'Error fetching ElevenLabs voices: {str(e)}')
        return []

def parse_timecode(time_str):
    """Parse timecode in format hh:mm:ss:ff, hh:mm:ss.ff, or decimal seconds"""
    # Convert to string and strip whitespace
    time_str = str(time_str).strip()
    
    # Handle different timecode formats
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 4:  # hh:mm:ss:ff format
            try:
                hours, minutes, seconds, frames = map(int, parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds + frames / 30.0
            except (ValueError, TypeError):
                return 0
        elif len(parts) == 3:  # hh:mm:ss format
            try:
                hours, minutes, seconds = map(int, parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds
            except (ValueError, TypeError):
                return 0
        else:
            return 0
    else:
        # Try to parse as decimal seconds
        try:
            total_seconds = float(time_str)
        except (ValueError, TypeError):
            return 0
    
    return total_seconds

def format_timecode(seconds):
    """Format seconds to hh:mm:ss.000 format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def normalize_column_name(column_name):
    """Normalize column names to handle case-insensitive matching"""
    return column_name.lower().strip()

def find_source_column(df):
    """Find the source column (script, line, text, transcription) in the CSV"""
    source_keywords = ['script', 'line', 'text', 'transcription']
    
    for col in df.columns:
        normalized_col = normalize_column_name(col)
        if any(keyword in normalized_col for keyword in source_keywords):
            return col
    
    return None

def convert_video_for_preview(input_path, output_path):
    """Convert video to MP4 format suitable for web preview"""
    try:
        # Get video info
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', input_path
        ]
        
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Failed to probe video file"
        
        # Parse video info
        video_info = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in video_info.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return False, "No video stream found"
        
        # Get original dimensions
        width = int(video_stream.get('width', 1920))
        height = int(video_stream.get('height', 1080))
        
        # Calculate new dimensions (maximum 720p, maintain aspect ratio)
        if height > 720:
            # Scale down to maximum 720p
            scale_factor = 720 / height
            new_width = int(width * scale_factor)
            new_height = 720
        else:
            # Keep original size if already 720p or lower
            new_width = width
            new_height = height
        
        # Calculate bitrate to keep file under 200MB
        # Estimate: 200MB = ~1600Mbps for reasonable quality
        target_bitrate = "1600k"
        
        # Convert video
        convert_cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',  # H.264 codec
            '-c:a', 'aac',       # AAC audio codec
            '-b:v', target_bitrate,
            '-vf', f'scale={new_width}:{new_height}',
            '-preset', 'medium',  # Balance between speed and quality
            '-movflags', '+faststart',  # Optimize for web streaming
            '-y',  # Overwrite output file
            output_path
        ]
        
        result = subprocess.run(convert_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return False, f"FFmpeg conversion failed: {result.stderr}"
        
        return True, "Video converted successfully"
        
    except Exception as e:
        return False, f"Video conversion error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-voices', methods=['GET'])
def get_voices():
    """Get available ElevenLabs voices"""
    try:
        voices = get_elevenlabs_voices()
        return jsonify({
            'voices': voices,
            'api_key_configured': bool(ELEVENLABS_API_KEY)
        })
    except Exception as e:
        return jsonify({
            'error': f'Error fetching voices: {str(e)}',
            'voices': [],
            'api_key_configured': bool(ELEVENLABS_API_KEY)
        }), 500

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No CSV file provided'}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file extension
    if not file.filename.lower().endswith('.csv'):
        return jsonify({'error': 'Please upload a CSV file. Only .csv files are allowed.'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Normalize column names for case-insensitive matching
        df.columns = [col.strip() for col in df.columns]
        
        # Find required columns
        speaker_col = None
        start_time_col = None
        end_time_col = None
        source_col = None
        
        for col in df.columns:
            normalized_col = normalize_column_name(col)
            
            if normalized_col in ['speaker']:
                speaker_col = col
            elif normalized_col in ['start_time', 'starttime', 'start time']:
                start_time_col = col
            elif normalized_col in ['end_time', 'endtime', 'end time']:
                end_time_col = col
        
        # Find source column
        source_col = find_source_column(df)
        
        if not speaker_col or not start_time_col or not end_time_col or not source_col:
            missing_cols = []
            if not speaker_col:
                missing_cols.append('speaker')
            if not start_time_col:
                missing_cols.append('start_time')
            if not end_time_col:
                missing_cols.append('end_time')
            if not source_col:
                missing_cols.append('source (script/line/text/transcription)')
            
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_cols)}'
            }), 400
        
        # Parse timecodes and create segments
        segments = []
        speakers = set()
        
        for index, row in df.iterrows():
            try:
                start_time = parse_timecode(str(row[start_time_col]))
                end_time = parse_timecode(str(row[end_time_col]))
                speaker = str(row[speaker_col])
                text = str(row[source_col])
            except Exception as e:
                app.logger.error(f"Error processing row {index}: {e}")
                app.logger.error(f"Row data: {row.to_dict()}")
                continue
            
            if start_time >= 0 and end_time > start_time:
                segments.append({
                    'id': index,
                    'speaker': speaker,
                    'start_time': start_time,
                    'end_time': end_time,
                    'start_time_formatted': format_timecode(start_time),
                    'end_time_formatted': format_timecode(end_time),
                    'text': text,
                    'duration': end_time - start_time
                })
                speakers.add(speaker)
        
        # Sort segments by start time
        segments.sort(key=lambda x: x['start_time'])
        
        return jsonify({
            'segments': segments,
            'speakers': list(speakers),
            'total_duration': max([seg['end_time'] for seg in segments]) if segments else 0
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing CSV: {str(e)}'}), 400

@app.route('/upload-video', methods=['POST'])
def upload_video():
    try:
        if 'video_file' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_video_file(file.filename):
            return jsonify({'error': 'Invalid video file format'}), 400
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save original file with temporary name
        original_filename = secure_filename(file.filename)
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"original_{original_filename}")
        file.save(original_filepath)
        
        # Verify original file was saved
        if not os.path.exists(original_filepath):
            return jsonify({'error': 'Failed to save original video file'}), 500
        
        # Convert video for preview
        preview_filename = f"preview_{original_filename.rsplit('.', 1)[0]}.mp4"
        preview_filepath = os.path.join(app.config['UPLOAD_FOLDER'], preview_filename)
        
        success, message = convert_video_for_preview(original_filepath, preview_filepath)
        
        if not success:
            # Clean up original file
            if os.path.exists(original_filepath):
                os.remove(original_filepath)
            return jsonify({'error': f'Video conversion failed: {message}'}), 400
        
        # Clean up original file to save space
        if os.path.exists(original_filepath):
            os.remove(original_filepath)
        
        return jsonify({
            'filename': preview_filename,
            'filepath': preview_filepath
        })
        
    except Exception as e:
        app.logger.error(f'Video upload error: {str(e)}')
        return jsonify({'error': f'Error uploading video: {str(e)}'}), 400

@app.route('/export-csv', methods=['POST'])
def export_csv():
    try:
        data = request.get_json()
        segments = data.get('segments', [])
        include_voices = data.get('include_voices', False)
        
        if not segments:
            return jsonify({'error': 'No segments to export'}), 400
        
        # Create DataFrame
        df_data = []
        for segment in segments:
            row_data = {
                'speaker': segment['speaker'],
                'start_time': segment['start_time_formatted'],
                'end_time': segment['end_time_formatted'],
                'transcription': segment['text']
            }
            
            # Add voice information if requested and available
            if include_voices and 'voice_id' in segment:
                row_data['voice_id'] = segment.get('voice_id', '')
                
                # Try to get voice name if we have voices loaded
                if segment.get('voice_id'):
                    # This would need to be enhanced to include voice names
                    # For now, just include the voice_id
                    pass
            
            df_data.append(row_data)
        
        df = pd.DataFrame(df_data)
        
        # Save to temporary file
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'exported_script.csv')
        df.to_csv(output_path, index=False)
        
        return send_file(output_path, as_attachment=True, download_name='script_timeline.csv')
        
    except Exception as e:
        return jsonify({'error': f'Error exporting CSV: {str(e)}'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port) 