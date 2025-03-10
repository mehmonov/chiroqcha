# 🚀 Chiroqcha - Online Code Runner

A simple, secure and fast online code execution platform that runs Python code in isolated Docker containers.

## 🌟 Key Features

- 🐍 Python 3.9 support
- 🔒 Secure code execution in Docker containers
- ⚡ Real-time code execution
- 🎨 CodeMirror editor with Dracula theme
- 📝 Code autocompletion
- 🔗 Code sharing functionality
- 🎯 Server health monitoring

## 🛠️ Technologies

- **Frontend**: HTML, CSS, JavaScript, CodeMirror
- **Backend**: Python, Flask
- **Containerization**: Docker
- **Security**: Docker isolation, resource limits

## 🚀 Getting Started

1. Clone repository:

```bash
git clone https://github.com/mehmonov/chiroqcha.git
cd chiroqcha
```

2. Create and activate virtual environment:

```bash
python -m venv env
source env/bin/activate  # For Linux/Mac
# or
.\env\Scripts\activate  # For Windows
pip install -r requirements.txt
```

3. Ensure Docker is installed

4. Start server:

```bash
python main.py
```

## 🔒 Security

- All code runs in isolated Docker containers
- CPU and memory resource limits
- Network access disabled
- Container timeout limits

## 🌐 API Endpoints

- `POST /api/execute` - Execute code
- `GET /api/status` - Check server status
- `POST /api/share` - Share code
- `GET /api/code/{share_id}` - Get shared code

## 🤝 Contributing

Feel free to submit Pull Requests. For major changes, please open an Issue first.

## 📝 License

[MIT](LICENSE)

## 👨‍💻 Author

Husniddin Mehmonov - [@mehmonov](https://github.com/mehmonov)

## 🙏 Acknowledgments

- CodeMirror team for the editor
- Docker team for containerization

---
⭐️ Star this repo if you find it useful!