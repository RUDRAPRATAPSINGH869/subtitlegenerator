document.addEventListener('DOMContentLoaded', function () {
    loadLanguages();
});

function loadLanguages() {
    fetch('/languages')
        .then(response => response.json())
        .then(languages => {
            const spokenLangSelect = document.getElementById('spokenLang');
            const targetLangSelect = document.getElementById('targetLang');

            languages.forEach(lang => {
                const option1 = document.createElement('option');
                option1.value = lang;
                option1.textContent = lang;
                spokenLangSelect.appendChild(option1);

                const option2 = document.createElement('option');
                option2.value = lang;
                option2.textContent = lang;
                targetLangSelect.appendChild(option2);
            });
        });
}

function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const spokenLang = document.getElementById('spokenLang').value;
    const targetLang = document.getElementById('targetLang').value;

    if (fileInput.files.length === 0) {
        alert('Please select a file.');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('spoken_lang', spokenLang);
    formData.append('target_lang', targetLang);

    const progressBar = document.getElementById('progressBar');
    progressBar.value = 0;

    let progress = 0;
    let interval = setInterval(() => {
        if (progress >= 95) {
            progress = 0; // Restart the progress bar to loop
        }
        progress += 5;
        progressBar.value = progress;
    }, 300);

    fetch('/transcribe', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            clearInterval(interval);
            progressBar.value = 100;

            document.getElementById('transcribedText').value = data.transcribed_text;
            document.getElementById('translatedText').value = data.translated_text;

            // Provide download links
            const downloads = document.getElementById('downloads');
            downloads.innerHTML = `
                <a href="/download/${data.srt_file}" download>Download SRT File</a><br>
                <a href="/download/${data.video_file}" download>Download Video with Subtitles</a>
            `;
        })
        .catch(error => {
            clearInterval(interval);
            alert('An error occurred: ' + error.message);
        });
}
