from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import tempfile

app = Flask(__name__)

DOWNLOAD_DIR = tempfile.gettempdir()
# Final Brahmastra with Cookies & Desktop Bypass
# The "No-Cookie TV/Mobile" Bypass

BYPASS_OPTIONS = {
    'quiet': True,
    'noplaylist': True,
    'no_warnings': True,
    'cookiefile': 'cookies.txt',
    'geo_bypass': True,
    'geo_bypass_country': 'IN',
    # ✅ FIX 7: Yeh 3 options add karo
    'socket_timeout': 30,
    'retries': 3,
    'fragment_retries': 3,
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
        # ✅ FIX 1: extractor_args se YouTube ka player client change karo
        ydl_opts.update({
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],  # android client pe format milte hain
                }
            }
        })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        formats = info.get('formats', [])
        resolutions = set()
        
        for f in formats:
            # ✅ FIX 2: acodec check hata do, sirf vcodec aur height dekho
            if f.get('vcodec') != 'none' and f.get('height'):
                resolutions.add(f.get('height'))
                
        sorted_res = sorted(list(resolutions), reverse=True)
        
        if not sorted_res:
            res_list = ['Best']
        else:
            res_list = [str(r) for r in sorted_res]

        return jsonify({
            'title': info.get('title', 'Video'),
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
        
        # ✅ FIX 3: extractor_args yahan bhi lagao
        ydl_opts.update({
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            }
        })
        
        if format_type == "MP4":
            if quality == 'Best':
                # ✅ FIX 4: ext restriction bilkul mat lagao
                fmt = 'bestvideo+bestaudio/best'
            else:
                # ✅ FIX 5: Yahi sabse important fix hai
                # ext=mp4 aur ext=m4a hata diya — sirf height se filter karo
                # Multiple fallbacks chain kiye hain
                fmt = (
                    f'bestvideo[height<={quality}]+bestaudio'
                    f'/bestvideo[height<={quality}]+bestaudio/best'
                )
                
            ydl_opts.update({
                'format': fmt,
                'merge_output_format': 'mp4',  # merge hone ke baad mp4 milega
                'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            })
        else:  # MP3
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
            elif format_type == 'MP4':
                # ✅ FIX 6: merge ke baad .mp4 extension ensure karo
                filename = os.path.splitext(filename)[0] + '.mp4'

        if not os.path.exists(filename):
            return jsonify({'error': 'File download nahi hua'}), 500

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print(f"Download Error: {e}")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    # Render ke hisaab se host aur port set kar diya
    app.run(debug=True, host='0.0.0.0', port=10000)