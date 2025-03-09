from flask import Flask, request, jsonify
from flask_cors import CORS
import docker
import uuid
import os
import tempfile
import logging

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_code_in_docker(code, timeout=10):
    """
    This function runs the code in a docker container
    """
    client = docker.from_env()
    container_name = f"python-runner-{uuid.uuid4()}"
    
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, "script.py")
    
    with open(file_path, "w") as f:
        f.write(code)
    
    try:
        logger.info(f"Konteyner yaratilmoqda: {container_name}")
        container = client.containers.run(
            "python:3.9-slim", 
            "python /code/script.py", # Bajarish buyrug'i
            volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
            name=container_name,
            detach=True,
            mem_limit="50m", # Xotira cheklovi
            cpu_period=100000,
            cpu_quota=25000, # 25% CPU cheklovi
            network_mode="none" # Tarmoq ulanishlarini o'chirish
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

@app.route('/api/execute', methods=['POST', 'OPTIONS'])
def execute_code():
    """
    Kodni qabul qilib bajarish uchun API endpoint
    """
    # OPTIONS so'rovlari uchun javob
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({"error": "Kod kiritilmagan"}), 400
            
        code = data['code']
        language = data.get('language', 'python') # Kelajakda boshqa tillar uchun
        
        # Hozircha faqat Python-ni qo'llab-quvvatlash
        if language != 'python':
            return jsonify({"error": f"{language} tili hozircha qo'llab-quvvatlanmaydi"}), 400
            
        # Kodni bajarish
        result = run_code_in_docker(code)
        return jsonify(result)
    except Exception as e:
        logger.error(f"API xatosi: {str(e)}")
        return jsonify({"error": str(e), "status": -1}), 500

# Server holati tekshirish uchun endpoint
@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    # Docker-ni tekshirish
    try:
        # Docker socket faylini aniq ko'rsatish
        # client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        # Yoki
        client = docker.from_env(timeout=30)
        client.ping()
        logger.info("Docker server bilan bog'lanish muvaffaqiyatli")
    except Exception as e:
        logger.error(f"Docker server bilan bog'lanishda xato: {str(e)}")
        print("XATO: Docker daemon ishga tushirilganini tekshiring")
        print("Yechim: 'sudo systemctl start docker' buyrug'ini bajaring")
        print("Yoki foydalanuvchingizni docker guruhiga qo'shing: 'sudo usermod -aG docker $USER'")
        print("So'ng tizimdan chiqib, qayta kiring yoki 'newgrp docker' buyrug'ini bajaring")
        exit(1)
        
    # Serverni ishga tushirish
    print("API server http://localhost:5000 manzilida ishga tushirildi")
    # Debug rejimini o'chirib qo'yish kerak production muhitda
    app.run(host='0.0.0.0', port=5000, debug=True)