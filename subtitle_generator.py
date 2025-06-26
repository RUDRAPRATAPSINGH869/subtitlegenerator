import os
import tempfile
import subprocess
import whisper
import srt
from datetime import timedelta
import re
from deep_translator import GoogleTranslator

# Load supported languages
SUPPORTED_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)
LANG_DICT = {name.title(): code for name, code in SUPPORTED_LANGS.items()}

def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".wav")
    command = ['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def transcribe_audio(audio_path, model_size="tiny"):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, task="transcribe")
    detected_lang = result.get("language", "unknown")
    return result["segments"], result["text"], detected_lang

def translate_segments(segments, target_lang):
    translated_segments = []
    for seg in segments:
        text = seg["text"]
        try:
            translated_text = GoogleTranslator(source="auto", target=target_lang).translate(text)
        except Exception:
            translated_text = "[Translation Failed]"
        translated_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": translated_text
        })
    return translated_segments

def export_srt(segments, srt_path):
    subs = []
    for i, segment in enumerate(segments, start=1):
        subs.append(srt.Subtitle(index=i,
                                 start=timedelta(seconds=segment["start"]),
                                 end=timedelta(seconds=segment["end"]),
                                 content=segment["text"]))
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

def burn_subtitles_ffmpeg(video_path, srt_path, output_path):
    command = [
        'ffmpeg',
        '-y',
        '-i', os.path.abspath(video_path),
        '-vf', f"subtitles={os.path.abspath(srt_path)}",
        '-c:a', 'copy',
        os.path.abspath(output_path)
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def process_video(video_path, target_lang_code, progress_callback):
    try:
        base_name = os.path.splitext(video_path)[0]
        progress_callback(5)

        audio_path = extract_audio(video_path)
        progress_callback(20)

        segments, full_text, detected_lang = transcribe_audio(audio_path, model_size="tiny")
        print(f"Segments detected: {len(segments)}")

        if not segments:
            print("No transcription segments detected.")
            return None

        progress_callback(50)

        translated_segments = translate_segments(segments, target_lang_code)
        print(f"Translated segments: {len(translated_segments)}")

        if not translated_segments:
            print("No translated segments produced.")
            return None

        progress_callback(70)

        srt_path = base_name + ".srt"
        export_srt(translated_segments, srt_path)
        progress_callback(80)

        final_output = base_name + "_with_subs.mp4"
        burn_subtitles_ffmpeg(video_path, srt_path, final_output)
        progress_callback(100)

        summary_path = base_name + "_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        print("Checking if output files exist:")
        print(f"Video exists: {os.path.exists(final_output)}")
        print(f"SRT exists: {os.path.exists(srt_path)}")
        print(f"Summary exists: {os.path.exists(summary_path)}")

        print("Processing completed successfully!")
        print(f"Returning: video={final_output}, srt={srt_path}, summary={summary_path}")

        return {
            "output_video": os.path.abspath(final_output),
            "subtitle_file": os.path.abspath(srt_path),
            "summary_file": os.path.abspath(summary_path),
            "detected_language": detected_lang
        }

    except Exception as e:
        print(f"Processing failed: {e}")
        return None
