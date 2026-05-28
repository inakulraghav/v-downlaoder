from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import tempfile

app = Flask(__name__)
DOWNLOAD_DIR = tempfile.gettempdir()

# ✅ Local (Windows) ya Render dono pe kaam karega
IS_RENDER = os.environ.get('RENDER', False)
FFMPEG_LOC = None if IS_RENDER else r'C:\ffmpeg\bin'

# ✅ Cookie path — local ya Render Secret File
COOKIE_PATH = None
for path in ['/etc/secrets/cookies.txt', 'cookies.txt']:
    if os.path.exists(path):
        COOKIE_PATH = path
        break

def base_opts():
    opts = {
        'quiet': True,
        'noplaylist': True,
        'geo_bypass': True,          # ✅ Region bypass
        'geo_bypass_country': 'IN',  # ✅ India ke liye
    }
    if COOKIE_PATH:
        opts['cookiefile'] = COOKIE_PATH
    if FFMPEG_LOC:
        opts['ffmpeg_location'] = FFMPEG_LOC
    return opts


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
        with yt_dlp.YoutubeDL(base_opts()) as ydl:
            info = ydl.extract_info(url, download=False)

        resolutions = set()
        for f in info.get('formats', []):
            if f.get('vcodec') != 'none' and f.get('height'):
                resolutions.add(f.get('height'))

        sorted_res = sorted(resolutions, reverse=True)
        return jsonify({
            'title': info.get('title', 'Video'),
            'resolutions': [str(r) for r in sorted_res] if sorted_res else ['Best']
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
        ydl_opts = base_opts()

        if format_type == 'MP4':
            if quality == 'Best':
                fmt = 'bestvideo+bestaudio/best'
            else:
                # ✅ ext restriction hata di — yahi error ka karan tha
                fmt = f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best'

            ydl_opts.update({
                'format': fmt,
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            })
        else:  # MP3
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality if quality != 'Best' else '192',
                }],
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            })

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