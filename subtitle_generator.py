import os
import tempfile
import subprocess
import whisper
import srt
from datetime import timedelta
import textwrap
import re
from PIL import ImageFont
from deep_translator import GoogleTranslator

SUPPORTED_LANGS = GoogleTranslator().get_supported_languages(as_dict=True)
LANG_DICT = {name.title(): code for name, code in SUPPORTED_LANGS.items()}

def get_font_for_text(text):
    if re.search(r'[\u0600-\u06FF]', text):
        return "fonts/NotoSansArabic-Regular.ttf"
    elif re.search(r'[\u0590-\u05FF]', text):
        return "fonts/NotoSansHebrew-Regular.ttf"
    elif re.search(r'[\u3040-\u30FF\u31F0-\u31FF]', text):
        return "fonts/NotoSansCJKjp-Regular.otf"
    elif re.search(r'[\uAC00-\uD7AF]', text):
        return "fonts/NotoSansCJKkr-Regular.otf"
    elif re.search(r'[\u4E00-\u9FFF]', text):
        return "fonts/NotoSansSC-Regular.ttf"
    elif re.search(r'[\u0900-\u097F]', text):
        return "fonts/NotoSansDevanagari-Regular.ttf"
    elif re.search(r'[\u0980-\u09FF]', text):
        return "fonts/NotoSansBengali-Regular.ttf"
    elif re.search(r'[\u0A00-\u0A7F]', text):
        return "fonts/NotoSansGurmukhi-Regular.ttf"
    elif re.search(r'[\u0A80-\u0AFF]', text):
        return "fonts/NotoSansGujarati-Regular.ttf"
    elif re.search(r'[\u0B00-\u0B7F]', text):
        return "fonts/NotoSansOriya-Regular.ttf"
    elif re.search(r'[\u0B80-\u0BFF]', text):
        return "fonts/NotoSansTamil-Regular.ttf"
    elif re.search(r'[\u0C00-\u0C7F]', text):
        return "fonts/NotoSansTelugu-Regular.ttf"
    elif re.search(r'[\u0C80-\u0CFF]', text):
        return "fonts/NotoSansKannada-Regular.ttf"
    elif re.search(r'[\u0D00-\u0D7F]', text):
        return "fonts/NotoSansMalayalam-Regular.ttf"
    elif re.search(r'[\u0E00-\u0E7F]', text):
        return "fonts/NotoSansThai-Regular.ttf"
    elif re.search(r'[\u0E80-\u0EFF]', text):
        return "fonts/NotoSansLao-Regular.ttf"
    elif re.search(r'[\u1780-\u17FF]', text):
        return "fonts/NotoSansKhmer-Regular.ttf"
    elif re.search(r'[\u1000-\u109F]', text):
        return "fonts/NotoSansMyanmar-Regular.ttf"
    elif re.search(r'[\u1200-\u137F]', text):
        return "fonts/NotoSansEthiopic-Regular.ttf"
    elif re.search(r'[\u0530-\u058F]', text):
        return "fonts/NotoSansArmenian-Regular.ttf"
    elif re.search(r'[\u10A0-\u10FF]', text):
        return "fonts/NotoSansGeorgian-Regular.ttf"
    else:
        return "fonts/NotoSans-Regular.ttf"

def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".wav")
    command = ['ffmpeg', '-y', '-i', video_path, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_path

def transcribe_audio(audio_path, model_size="medium"):
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


def process_video(video_path, target_lang_code, progress_callback=None):
    try:
        base_name = os.path.splitext(video_path)[0]
        if progress_callback: progress_callback(5)
        audio_path = extract_audio(video_path)
        if progress_callback: progress_callback(20)
        segments, full_text, detected_lang = transcribe_audio(audio_path)
        if progress_callback: progress_callback(50)
        translated_segments = translate_segments(segments, target_lang_code)
        if progress_callback: progress_callback(70)
        srt_path = base_name + ".srt"
        export_srt(translated_segments, srt_path)
        if progress_callback: progress_callback(80)
        final_output = base_name + "_with_subs.mp4"
        burn_subtitles_ffmpeg(video_path, srt_path, final_output)
        if progress_callback: progress_callback(100)
        summary_path = base_name + "_summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        return {
    "output_video": os.path.abspath(final_output),
    "subtitle_file": os.path.abspath(srt_path),
    "summary_file": os.path.abspath(summary_path),
    "detected_language": detected_lang
     }

    except Exception as e:
        raise RuntimeError(f"Processing failed: {e}")
