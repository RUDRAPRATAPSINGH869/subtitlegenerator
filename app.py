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
        # Process the video
        result = process_video(temp_video_path, LANG_DICT[target_lang], progress_callback=update_progress)

    if result:
        st.success(f"✅ Subtitled video generated successfully!\nDetected Language: {result['detected_language']}")

        with open(result["output_video"], "rb") as f:
            st.download_button("⬇️ Download Video with Subtitles", f, file_name=os.path.basename(result["output_video"]))

        with open(result["subtitle_file"], "rb") as f:
            st.download_button("⬇️ Download Subtitle File (.srt)", f, file_name=os.path.basename(result["subtitle_file"]))

        with open(result["summary_file"], "rb") as f:
            st.download_button("⬇️ Download Full Transcript", f, file_name=os.path.basename(result["summary_file"]))
   else:
       st.error("Processing failed. Please check the logs.")
