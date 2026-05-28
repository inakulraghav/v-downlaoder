from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import tempfile

app = Flask(__name__)

DOWNLOAD_DIR = tempfile.gettempdir()

BYPASS_OPTIONS = {
    'quiet': True, 
    'noplaylist': True,
    'no_warnings': True,
    'geo_bypass': True,
    'geo_bypass_country': 'IN',
    'legacyserverconnect': True,
    'cookiefile': 'cookies.txt',  # <--- YE NAYI LINE ADD HUI HAI
    'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
    }
}

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
        # Bypass options ko fetch info me use kar rahe hain
        ydl_opts = BYPASS_OPTIONS.copy()
        
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
        print(f"Fetch Info Error: {e}")
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
        # Bypass options ko download me bhi use kar rahe hain
        ydl_opts = BYPASS_OPTIONS.copy()
        
        if format_type == "MP4":
            if quality == 'Best':
                fmt = 'bestvideo+bestaudio/best'
            else:
                fmt = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                
            ydl_opts.update({
                'format': fmt,
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            })
        else: # MP3
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == 'MP3':
                # FFmpeg download ke baad file ka naam .mp3 kar deta hai
                filename = os.path.splitext(filename)[0] + '.mp3'

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Render ke hisaab se host aur port set kar diya
    app.run(debug=True, host='0.0.0.0', port=10000)