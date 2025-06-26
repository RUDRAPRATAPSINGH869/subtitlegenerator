import streamlit as st
import os
from subtitle_generator import process_video, LANG_DICT

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)

st.title("🎬 Whisper Subtitle Translator (Cloud-Compatible Version)")

# File uploader
uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov"])

# Language selector
target_lang = st.selectbox("Select Subtitle Output Language", list(LANG_DICT.keys()))

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None

if uploaded_file and st.button("Generate Subtitles"):
    # Save the uploaded file to disk
    temp_video_path = os.path.join("uploads", uploaded_file.name)
    with open(temp_video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.info("Processing video, please wait...")

    # Progress bar setup
    progress_bar = st.progress(0)

    def update_progress(val):
        progress_bar.progress(val)

    try:
        st.session_state.result = process_video(temp_video_path, LANG_DICT[target_lang], progress_callback=update_progress)
        if st.session_state.result:
            st.success(f"✅ Subtitled video generated successfully!\nDetected Language: {st.session_state.result['detected_language']}")
        else:
            st.error("Processing failed. Please check the logs.")
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")

# Show download buttons if processing is complete
if st.session_state.result:
    with open(st.session_state.result["output_video"], "rb") as f:
        st.download_button("⬇️ Download Video with Subtitles", f, file_name=os.path.basename(st.session_state.result["output_video"]))

    with open(st.session_state.result["subtitle_file"], "rb") as f:
        st.download_button("⬇️ Download Subtitle File (.srt)", f, file_name=os.path.basename(st.session_state.result["subtitle_file"]))

    with open(st.session_state.result["summary_file"], "rb") as f:
        st.download_button("⬇️ Download Full Transcript", f, file_name=os.path.basename(st.session_state.result["summary_file"]))
