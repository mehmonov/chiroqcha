from flask import Flask, request, jsonify
from flask_cors import CORS
import docker
import uuid
import os
import tempfile
import logging
from werkzeug.serving import run_simple

app = Flask(__name__, static_folder='static')
CORS(app)  # Cross-Origin so'rovlarni ruxsat berish

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_code_in_docker(code, timeout=10):
    """
    Foydalanuvchi kodini Docker ichida xavfsiz bajarish
    """
    client = docker.from_env()
    container_name = f"python-runner-{uuid.uuid4()}"
    
    # Vaqtinchalik fayl yaratish
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "script.py")
    
    with open(file_path, "w") as f:
        f.write(code)
    
    try:
        logger.info(f"Konteyner yaratilmoqda: {container_name}")
        container = client.containers.run(
            "python:3.9-slim",  # Python image
            "python /code/script.py",  # Bajarish buyrug'i
            volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
            name=container_name,
            detach=True,
            mem_limit="50m",  # Xotira cheklovi
            cpu_period=100000,
            cpu_quota=25000,   # 25% CPU cheklovi
            network_mode="none"  # Tarmoq ulanishlarini o'chirish
        )
        
        # Belgilangan vaqt ichida bajarilishini kutish
        result = container.wait(timeout=timeout)
        logs = container.logs().decode("utf-8")
        
        return {
            "output": logs,
            "status": result["StatusCode"]
        }
    except Exception as e:
        logger.error(f"Xato yuz berdi: {str(e)}")
        return {
            "output": "",
            "error": str(e),
            "status": -1
        }
    finally:
        # Konteyner va faylni tozalash
        try:
            client.containers.get(container_name).remove(force=True)
            os.remove(file_path)
            os.rmdir(temp_dir)
        except Exception as e:
            logger.error(f"Tozalashda xato: {str(e)}")
            pass

@app.route('/api/execute', methods=['POST'])
def execute_code():
    """
    Kodni qabul qilib bajarish uchun API endpoint
    """
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({"error": "Kod kiritilmagan"}), 400
        
        code = data['code']
        language = data.get('language', 'python')  # Kelajakda boshqa tillar uchun
        
        # Hozircha faqat Python-ni qo'llab-quvvatlash
        if language != 'python':
            return jsonify({"error": f"{language} tili hozircha qo'llab-quvvatlanmaydi"}), 400
        
        # Kodni bajarish
        result = run_code_in_docker(code)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"API xatosi: {str(e)}")
        return jsonify({"error": str(e), "status": -1}), 500

# Static fayllarni boshqarish
@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    # Docker-ni tekshirish
    try:
        docker.from_env().ping()
        logger.info("Docker server bilan bog'lanish muvaffaqiyatli")
    except Exception as e:
        logger.error(f"Docker server bilan bog'lanishda xato: {str(e)}")
        print("XATO: Docker daemon ishga tushirilganini tekshiring")
        exit(1)
    
    # Serverning statik papkasini tekshirish
    if not os.path.exists('static'):
        print("XATO: 'static' papkasi mavjud emas. Iltimos, static/index.html, static/style.css va static/script.js fayllarini yarating.")
        print("Ushbu fayllarning namunasi quyida berilgan. Uni nusxalab oling va zarur fayllarga saqlang.")
        print("\n--- static/index.html ---\n")
        print("""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Code Runner</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/theme/dracula.min.css">
</head>
<body>
    <div class="container">
        <h1>Python Code Runner</h1>
        <div class="editor-container">
            <div class="language-selector">
                <select id="language-select">
                    <option value="python" selected>Python</option>
                    <option value="javascript" disabled>JavaScript (Yaqin kelajakda)</option>
                    <option value="java" disabled>Java (Yaqin kelajakda)</option>
                </select>
            </div>
            <textarea id="code-editor">print("Salom, dunyo!")</textarea>
            <div class="button-container">
                <button id="run-button">Kodni bajarish</button>
                <button id="clear-button">Tozalash</button>
            </div>
        </div>
        <div class="output-container">
            <h3>Natija:</h3>
            <pre id="output">Natija shu yerda ko'rsatiladi...</pre>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js"></script>
    <script src="script.js"></script>
</body>
</html>""")
        print("\n--- static/style.css ---\n")
        print("""body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
    color: #333;
}

.container {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    text-align: center;
    margin-bottom: 30px;
    color: #2c3e50;
}

.editor-container {
    background-color: #fff;
    border-radius: 5px;
    padding: 15px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.language-selector {
    margin-bottom: 10px;
}

select {
    padding: 8px 12px;
    border-radius: 4px;
    border: 1px solid #ddd;
    background-color: #fff;
    font-size: 14px;
}

.CodeMirror {
    height: 300px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 15px;
}

.button-container {
    display: flex;
    justify-content: space-between;
    margin-top: 15px;
}

button {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    font-size: 14px;
    cursor: pointer;
    transition: background-color 0.3s;
}

#run-button {
    background-color: #4CAF50;
    color: white;
    flex: 2;
    margin-right: 10px;
}

#run-button:hover {
    background-color: #45a049;
}

#clear-button {
    background-color: #f44336;
    color: white;
    flex: 1;
}

#clear-button:hover {
    background-color: #d32f2f;
}

.output-container {
    background-color: #fff;
    border-radius: 5px;
    padding: 15px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.output-container h3 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

#output {
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    overflow-x: auto;
    min-height: 100px;
    font-family: 'Courier New', Courier, monospace;
    white-space: pre-wrap;
}

/* Responsive design */
@media (max-width: 768px) {
    .container {
        padding: 10px;
    }
    
    .CodeMirror {
        height: 250px;
    }
    
    .button-container {
        flex-direction: column;
    }
    
    #run-button, #clear-button {
        margin-right: 0;
        margin-bottom: 10px;
    }
}""")
        print("\n--- static/script.js ---\n")
        print("""document.addEventListener('DOMContentLoaded', function() {
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
            outputArea.textContent = 'Xato: Kod maydoni bo\\'sh!';
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
        outputArea.textContent = 'Natija shu yerda ko\\'rsatiladi...';
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
});""")
        exit(1)
    
    # Serverni ishga tushirish
    print("Server http://localhost:5000 manzilida ishga tushirildi")
    run_simple('0.0.0.0', 5000, app, use_reloader=True)