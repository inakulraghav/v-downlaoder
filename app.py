from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import tempfile

app = Flask(__name__)

DOWNLOAD_DIR = tempfile.gettempdir()

# Ekdum Clean Options: Sirf Cookies aur India Geo-Bypass. Baaki yt-dlp khud handle karega.
BYPASS_OPTIONS = {
    'quiet': True, 
    'noplaylist': True,
    'no_warnings': True,
    'cookiefile': 'cookies.txt',  # Teri chaabi
    'geo_bypass': True,
    'geo_bypass_country': 'IN',   # India ke videos ko unblock karne ke liye
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
        ydl_opts = BYPASS_OPTIONS.copy()
        
        # YAHAN SE MINE 'format' = 'best' WALI LINE DELETE KAR DI HAI
        ydl_opts['ignore_no_formats_error'] = True # Ye audio-only video ko crash hone se bachayega
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        formats = info.get('formats', [])
        resolutions = set()
        
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                resolutions.add(f.get('height'))
                
        sorted_res = sorted(list(resolutions), reverse=True)
        
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
        ydl_opts = BYPASS_OPTIONS.copy()
        
        if format_type == "MP4":
            if quality == 'Best':
                # 'b' ek aakhri failsafe hai jo kisi bhi halat me download fail nahi hone dega
                fmt = 'bestvideo+bestaudio/best/b'
            else:
                # Agar user 1080p/720p chune, aur wo na mile, toh crash hone ki jagah automatically best de dega
                fmt = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/bestvideo+bestaudio/best/b'
                
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
                filename = os.path.splitext(filename)[0] + '.mp3'
            else:
                filename = os.path.splitext(filename)[0] + '.mp4'

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)