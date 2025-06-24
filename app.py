from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import whisper
from deep_translator import GoogleTranslator
import tempfile
import os
from subtitle_generator import get_font_for_text, export_srt, render_subtitles_on_video

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

SUPPORTED_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)
LANG_DICT = {name.title(): code for name, code in SUPPORTED_LANGS.items()}

os.makedirs('output', exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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

        base_name = os.path.splitext(os.path.basename(temp_file.name))[0]
        srt_filename = f"{base_name}.srt"
        video_filename = f"{base_name}_subtitled.mp4"

        socketio.emit('progress', {'progress': 10})

        model = whisper.load_model('medium')

        socketio.emit('progress', {'progress': 30})

        transcription = model.transcribe(temp_file.name, language=None if spoken_lang == 'Auto' else LANG_DICT[spoken_lang])
        transcribed_text = transcription['text']

        socketio.emit('progress', {'progress': 50})

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

        socketio.emit('progress', {'progress': 70})

        srt_path = os.path.join('output', srt_filename)
        export_srt(translated_segments, srt_path)

        socketio.emit('progress', {'progress': 85})

        sample_text = translated_segments[0]['text'] if translated_segments else ''
        font_path = get_font_for_text(sample_text)

        video_output_path = os.path.join('output', video_filename)
        render_subtitles_on_video(temp_file.name, translated_segments, video_output_path, font_path)

        socketio.emit('progress', {'progress': 100})

        return jsonify({
            'transcribed_text': transcribed_text,
            'srt_file': srt_filename,
            'video_file': video_filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('output', filename, as_attachment=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
