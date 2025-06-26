import streamlit as st
from subtitle_generator import process_video, LANG_DICT

# Initialize session state variables
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'result' not in st.session_state:
    st.session_state.result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

st.title("🎬 Whisper Subtitle Translator\n(Cloud-Compatible Version)")

uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov", "mpeg4"])

language = st.selectbox("Select Subtitle Output Language", list(LANG_DICT.keys()))

if uploaded_file:
    # Reset session state when a new file is uploaded
    if 'last_uploaded_file' not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.progress = 0
        st.session_state.result = None
        st.session_state.processing = False
        st.session_state.last_uploaded_file = uploaded_file.name

    if st.button("Generate Subtitles"):
        st.session_state.processing = True

        def update_progress(value):
            st.session_state.progress = value
            st.rerun()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
            temp_video.write(uploaded_file.read())
            temp_video_path = temp_video.name

        st.session_state.result = process_video(temp_video_path, LANG_DICT[language], update_progress)
        st.session_state.processing = False
        st.rerun()

# Show progress bar
if st.session_state.processing:
    st.progress(st.session_state.progress)
    st.info("Processing video, please wait...")

# Show download buttons
if st.session_state.result:
    st.success("Processing completed!")

    with open(st.session_state.result["output_video"], "rb") as file:
        st.download_button(label="Download Video with Subtitles",
                           data=file,
                           file_name="output_with_subtitles.mp4",
                           mime="video/mp4")

    with open(st.session_state.result["subtitle_file"], "rb") as file:
        st.download_button(label="Download Subtitle File (SRT)",
                           data=file,
                           file_name="subtitles.srt",
                           mime="text/plain")

    with open(st.session_state.result["summary_file"], "rb") as file:
        st.download_button(label="Download Transcript",
                           data=file,
                           file_name="transcript.txt",
                           mime="text/plain")
