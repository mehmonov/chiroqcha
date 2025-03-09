import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import docker
import uuid
import os
import tempfile
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", 
                            "methods": ["GET", "POST", "OPTIONS"], 
                            "allow_headers": ["Content-Type", "Authorization", "Accept"],
                            "supports_credentials": False}})
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
        logger.info(f"container is being created: {container_name}")
        container = client.containers.run(
            "python:3.9-slim", 
            "python /code/script.py", 
            volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
            name=container_name,
            detach=True,
            mem_limit="50m",
            cpu_period=100000,
            cpu_quota=25000, 
            network_mode="none" 
        )
        
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
    This function accepts code and executes it
    """
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.json
        if not data or 'code' not in data:
            return jsonify({"error": "Kod kiritilmagan"}), 400
            
        code = data['code']
        language = data.get('language', 'python') # Kelajakda boshqa tillar uchun
        
        if language != 'python':
            return jsonify({"error": f"{language} language is not supported yet"}), 400
            
        result = run_code_in_docker(code)
        return jsonify(result)
    except Exception as e:
        logger.error(f"API xatosi: {str(e)}")
        return jsonify({"error": str(e), "status": -1}), 500

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    try:
        client = docker.from_env(timeout=30)
        client.ping()
        logger.info("Docker server bilan bog'lanish muvaffaqiyatli")
    except Exception as e:
        logger.error(f"Docker server is not running: {str(e)}")
     
        subprocess.run(["sudo", "systemctl", "start", "docker"])
        subprocess.run(["sudo", "usermod", "-aG", "docker", "$USER"])
        subprocess.run(["newgrp", "docker"])
        exit(1)
    
    cert_file = '/root/ssl-cert/cert.pem'
    key_file = '/root/ssl-cert/key.pem'
        
        
    if os.path.exists(cert_file) and os.path.exists(key_file):
        # HTTPS bilan ishga tushirish
        ssl_context = (cert_file, key_file)
        app.run(host='0.0.0.0', port=5000, ssl_context=ssl_context)
    else:
        # Sertifikat fayllarini yaratish
        logger.info("SSL sertifikat fayllari topilmadi. HTTP rejimida ishga tushirilmoqda...")
        app.run(host='0.0.0.0', port=5000)