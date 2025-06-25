from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_cors import CORS
import whisper
from deep_translator import GoogleTranslator
import tempfile
import os
from subtitle_generator import get_font_for_text, export_srt, render_subtitles_on_video

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

SUPPORTED_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)
LANG_DICT = {name.title(): code for name, code in SUPPORTED_LANGS.items()}

os.makedirs('output', exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

users = {}

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('signup.html', error='Username already exists')
        users[username] = password
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/languages', methods=['GET'])
def get_languages():
    return jsonify(list(LANG_DICT.keys()))

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        file = request.files['file']
        spoken_lang = request.form.get('spoken_lang', 'Auto')
        target_lang = request.form.get('target_lang', 'English')

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        file.save(temp_file.name)

        model = whisper.load_model('tiny')

        transcription = model.transcribe(temp_file.name, language=None if spoken_lang == 'Auto' else LANG_DICT[spoken_lang])
        transcribed_text = transcription['text']

        try:
            translated_text = GoogleTranslator(source='auto', target=LANG_DICT[target_lang]).translate(transcribed_text)
        except Exception:
            translated_text = '[Translation Failed]'

        base_name = os.path.splitext(os.path.basename(temp_file.name))[0]
        srt_filename = f"{base_name}.srt"
        video_filename = f"{base_name}_subtitled.mp4"

        segments = transcription['segments']
        translated_segments = []
        for seg in segments:
            text = seg['text']
            try:
                translated_text_segment = GoogleTranslator(source='auto', target=LANG_DICT[target_lang]).translate(text)
            except Exception:
                translated_text_segment = '[Translation Failed]'
            translated_segments.append({
                'start': seg['start'],
                'end': seg['end'],
                'text': translated_text_segment
            })

        srt_path = os.path.join('output', srt_filename)
        export_srt(translated_segments, srt_path)

        sample_text = translated_segments[0]['text'] if translated_segments else ''
        font_path = get_font_for_text(sample_text)

        video_output_path = os.path.join('output', video_filename)
        render_subtitles_on_video(temp_file.name, translated_segments, video_output_path, font_path)

        return jsonify({
            'transcribed_text': transcribed_text,
            'translated_text': translated_text,
            'srt_file': srt_filename,
            'video_file': video_filename
        })

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({'error': f'Failed to process the file: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('output', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
