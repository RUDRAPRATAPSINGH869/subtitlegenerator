import streamlit as st
from subtitle_generator import process_video, LANG_DICT

st.title("🎬 Whisper Subtitle Translator (Streamlit Version)")

uploaded_file = st.file_uploader("Upload a video", type=["mp4", "avi", "mov"])

if uploaded_file:
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    target_lang = st.selectbox("Select Subtitle Output Language", list(LANG_DICT.keys()))

    if st.button("Generate Subtitles"):
        progress_bar = st.progress(0)

        def update_progress(val):
            progress_bar.progress(val)

        result = process_video(uploaded_file.name, LANG_DICT[target_lang], progress_callback=update_progress)

        st.success(f"Subtitled video created! Detected language: {result['detected_language']}")

        with open(result["output_video"], "rb") as f:
            st.download_button("Download Video with Subtitles", f, file_name=os.path.basename(result["output_video"]))

        with open(result["subtitle_file"], "rb") as f:
            st.download_button("Download Subtitle File (SRT)", f, file_name=os.path.basename(result["subtitle_file"]))

        with open(result["summary_file"], "rb") as f:
            st.download_button("Download Full Transcript", f, file_name=os.path.basename(result["summary_file"]))
