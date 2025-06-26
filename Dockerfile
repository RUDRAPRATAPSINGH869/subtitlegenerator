# Use Python 3.10 base image
FROM python:3.10-slim

# Set working directory
ENV STREAMLIT_CONFIG_DIR=/tmp/.streamlit

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip setuptools<81
RUN pip install -r requirements.txt

# Expose port (required by Render)
EXPOSE 8000

# Start the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
