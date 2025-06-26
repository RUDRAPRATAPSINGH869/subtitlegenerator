import streamlit as st
import os
from subtitle_generator import process_video, LANG_DICT

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

st.title("🎬 Whisper Subtitle Translator (Cloud-Compatible Version)")

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# Language selector
target_lang = st.selectbox("Select Subtitle Output Language", list(LANG_DICT.keys()))

# Reset result if a new file is uploaded
if uploaded_file and (st.session_state.get('last_uploaded') != uploaded_file.name):
    st.session_state.result = None
    st.session_state.last_uploaded = uploaded_file.name

if uploaded_file and st.button("Generate Subtitles"):
    # Save the uploaded file to disk
    temp_video_path = os.path.join("uploads", uploaded_file.name)
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info("Processing video, please wait...")
    st.session_state.processing = True

    # Progress bar setup
    progress_bar = st.progress(0)

    def update_progress(val):
        progress_bar.progress(val)

    result = process_video(temp_video_path, LANG_DICT[target_lang], progress_callback=update_progress)
    st.session_state.result = result
    st.session_state.processing = False

if st.session_state.result:
    st.success(f"✅ Subtitled video generated successfully!\nDetected Language: {st.session_state.result['detected_language']}")

    with open(st.session_state.result["output_video"], "rb") as f:
        st.download_button("⬇️ Download Video with Subtitles", f, file_name=os.path.basename(st.session_state.result["output_video"]))

    with open(st.session_state.result["subtitle_file"], "rb") as f:
        st.download_button("⬇️ Download Subtitle File (.srt)", f, file_name=os.path.basename(st.session_state.result["subtitle_file"]))

    with open(st.session_state.result["summary_file"], "rb") as f:
        st.download_button("⬇️ Download Full Transcript", f, file_name=os.path.basename(st.session_state.result["summary_file"]))

elif not st.session_state.processing and uploaded_file:
    st.warning("Processing failed or not started yet.")
