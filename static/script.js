document.addEventListener('DOMContentLoaded', function() {
    // CodeMirror editorini sozlash
    const codeEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
        mode: 'python',
        theme: 'dracula',
        lineNumbers: true,
        indentUnit: 4,
        lineWrapping: true,
        tabSize: 4,
        autoCloseBrackets: true,
        matchBrackets: true
    });

    // Tugmalarni topish
    const runButton = document.getElementById('run-button');
    const clearButton = document.getElementById('clear-button');
    const outputArea = document.getElementById('output');
    const languageSelect = document.getElementById('language-select');

    // Kodni bajarish uchun tugma bosilganda
    runButton.addEventListener('click', function() {
        const code = codeEditor.getValue();
        const language = languageSelect.value;
        
        if (code.trim() === '') {
            outputArea.textContent = 'Xato: Kod maydoni bo\'sh!';
            return;
        }
        
        // Bajarish jarayonida tugma holatini o'zgartirish
        runButton.disabled = true;
        runButton.textContent = 'Bajarilmoqda...';
        outputArea.textContent = 'Kod bajarilmoqda...';
        
        // API ga so'rov yuborish
        fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                code: code,
                language: language
            })
        })
        .then(response => response.json())
        .then(data => {
            // Natijani ko'rsatish
            if (data.error) {
                outputArea.textContent = `Xato: ${data.error}`;
            } else if (data.output) {
                outputArea.textContent = data.output;
            } else {
                outputArea.textContent = 'Kod bajarildi, lekin hech qanday natija qaytarilmadi.';
            }
        })
        .catch(error => {
            outputArea.textContent = `So'rov yuborishda xato: ${error.message}`;
            console.error('Error:', error);
        })
        .finally(() => {
            // Tugmani boshlang'ich holatiga qaytarish
            runButton.disabled = false;
            runButton.textContent = 'Kodni bajarish';
        });
    });

    // Tozalash tugmasi bosilganda
    clearButton.addEventListener('click', function() {
        codeEditor.setValue('');
        outputArea.textContent = 'Natija shu yerda ko\'rsatiladi...';
    });

    // Til o'zgartirilganda
    languageSelect.addEventListener('change', function() {
        const language = languageSelect.value;
        if (language !== 'python') {
            alert(`Kechirasiz, ${language} tili hozircha qo'llab-quvvatlanmaydi.`);
            languageSelect.value = 'python';
        }
        
        // Kod tilini o'zgartirish (kelajakda)
        // codeEditor.setOption('mode', language);
    });
});