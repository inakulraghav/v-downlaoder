from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import tempfile

app = Flask(__name__)

DOWNLOAD_DIR = tempfile.gettempdir()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/fetch_info', methods=['POST'])
def fetch_info():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL missing'}), 400

    try:
        ydl_opts = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        formats = info.get('formats', [])
        resolutions = set()
        
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                resolutions.add(f.get('height'))
                
        sorted_res = sorted(list(resolutions), reverse=True)
        
        # Agar koi resolution na mile (Jaise Insta/TikTok me hota h), toh 'Best' set kar do
        if not sorted_res:
            res_list = ['Best']
        else:
            res_list = [str(r) for r in sorted_res]

        return jsonify({
            'title': info.get('title', 'Video Document'),
            'resolutions': res_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.form
    url = data.get('url')
    format_type = data.get('format')
    quality = data.get('quality')
    
    if not url:
        return jsonify({'error': 'URL missing'}), 400

    try:
        if format_type == "MP4":
            # Agar user ne 'Best' select kiya (Non-YouTube sites ke liye)
            if quality == 'Best':
                fmt = 'bestvideo+bestaudio/best'
            else:
                fmt = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                
            ydl_opts = {
                'format': fmt,
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
                
            }
        else: # MP3
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality if quality != 'Best' else '192',
                }],
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
                'noplaylist': True,
                
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'MP3':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)