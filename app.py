import streamlit as st
import os
from subtitle_generator import process_video, LANG_DICT

os.makedirs("uploads", exist_ok=True)

st.title("🎬 Whisper Subtitle Translator (Cloud-Compatible Version)")

# Initialize session state
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'progress' not in st.session_state:
    st.session_state.progress = 0

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# Language selector
target_lang = st.selectbox("Select Subtitle Output Language", list(LANG_DICT.keys()))

# Save uploaded file to session state
if uploaded_file is not None:
    st.session_state.uploaded_file = uploaded_file
    st.session_state.result = None
    st.session_state.progress = 0

progress_bar = st.progress(st.session_state.progress)

def update_progress(val):
    st.session_state.progress = val
    st.rerun()  # Force re-render to update the progress bar

def process():
    st.session_state.processing = True
    file = st.session_state.uploaded_file
    if file is None:
        st.error("No file uploaded!")
        st.session_state.processing = False
        return

    temp_video_path = os.path.join("uploads", file.name)
    with open(temp_video_path, "wb") as f:
        f.write(file.getbuffer())

    result = process_video(temp_video_path, LANG_DICT[target_lang], progress_callback=update_progress)

    if result is not None:
        st.session_state.result = result
    else:
        st.error("Processing failed. Please try again.")

    st.session_state.processing = False
    st.session_state.progress = 100
    st.rerun()  # Force rerun to refresh UI

if st.session_state.uploaded_file is not None:
    if st.button("Generate Subtitles"):
        process()

if st.session_state.result:
    result = st.session_state.result
    st.success(f"✅ Subtitled video generated successfully!\nDetected Language: {result['detected_language']}")

    with open(result["output_video"], "rb") as f:
        st.download_button("⬇️ Download Video with Subtitles", f, file_name=os.path.basename(result["output_video"]))

    with open(result["subtitle_file"], "rb") as f:
        st.download_button("⬇️ Download Subtitle File (.srt)", f, file_name=os.path.basename(result["subtitle_file"]))

    with open(result["summary_file"], "rb") as f:
        st.download_button("⬇️ Download Full Transcript", f, file_name=os.path.basename(result["summary_file"]))
elif st.session_state.processing:
    st.info("Processing video, please wait...")
    st.progress(st.session_state.progress)
elif st.session_state.uploaded_file:
    st.info("Ready to process. Click the button to start.")
