    document.addEventListener('DOMContentLoaded', function() {
        const API_URL = process.env.API_URL || 'http://localhost:5000';
        
        function checkServerStatus() {
            fetch(`${API_URL}/api/status`)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    }
                    throw new Error('Server not responding');
                })
                .then(data => {
                    document.getElementById('status-indicator').className = 'status-circle status-green';
                    document.getElementById('status-text').textContent = 'Online';
                    document.getElementById('run-button').disabled = false;
                })
                .catch(error => {
                    document.getElementById('status-indicator').className = 'status-circle status-red';
                    document.getElementById('status-text').textContent = 'Cannot connect to server';
                    document.getElementById('run-button').disabled = true;
                });
        }
        
        checkServerStatus();
        setInterval(checkServerStatus, 5000);
        
        const pythonKeywords = [
            "False", "None", "True", "and", "as", "assert", "async", "await", "break", 
            "class", "continue", "def", "del", "elif", "else", "except", "finally", 
            "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", 
            "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
            "abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable", "chr",
            "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod", 
            "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", 
            "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", 
            "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", 
            "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow", 
            "print", "property", "range", "repr", "reversed", "round", "set", "setattr", 
            "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple", "type", 
            "vars", "zip", "__import__"
        ];
        
        const codeEditor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
            mode: 'python',
            theme: 'dracula',
            lineNumbers: true,
            indentUnit: 4,
            lineWrapping: true,
            tabSize: 4,
            autoCloseBrackets: true,
            matchBrackets: true,
            extraKeys: {"Ctrl-Space": "autocomplete"}
        });
        
        // Custom autocomplete function
        CodeMirror.registerHelper("hint", "python", function(editor) {
            const cursor = editor.getCursor();
            const line = editor.getLine(cursor.line);
            const start = cursor.ch;
            let end = cursor.ch;
            
            // Find the start of the current word
            while (start > 0 && /[\w\.]/.test(line.charAt(start - 1))) {
                start--;
            }
            
            // Get the current word
            const word = line.slice(start, end);
            const list = [];
            
            // Filter keywords based on the current word
            for (let i = 0; i < pythonKeywords.length; i++) {
                if (pythonKeywords[i].startsWith(word)) {
                    list.push(pythonKeywords[i]);
                }
            }
            
            return {
                list: list,
                from: CodeMirror.Pos(cursor.line, start),
                to: CodeMirror.Pos(cursor.line, end)
            };
        });
        
        // Enable auto-complete on typing
        codeEditor.on("keyup", function(cm, event) {
            if (!cm.state.completionActive && 
                event.keyCode != 13 && // Enter
                event.keyCode != 27 && // Escape
                document.getElementById('autocomplete-toggle').checked) {
                
                const cursor = cm.getCursor();
                const line = cm.getLine(cursor.line);
                
                // Only show hints if we're typing a word character
                if (/[\w\.]/.test(line.charAt(cursor.ch - 1))) {
                    CodeMirror.commands.autocomplete(cm, null, {completeSingle: false});
                }
            }
        });

        const runButton = document.getElementById('run-button');
        const clearButton = document.getElementById('clear-button');
        const shareButton = document.getElementById('share-button');
        const copyButton = document.getElementById('copy-button');
        const shareUrlInput = document.getElementById('share-url');
        const outputArea = document.getElementById('output');
        const languageSelect = document.getElementById('language-select');
        const autocompleteToggle = document.getElementById('autocomplete-toggle');


        autocompleteToggle.addEventListener('change', function() {
            if (this.checked) {
                codeEditor.setOption('extraKeys', {"Ctrl-Space": "autocomplete"});
            } else {
                codeEditor.setOption('extraKeys', {});
            }
        });

        function checkSharedCode() {
            const urlPath = window.location.pathname;
            if (urlPath.startsWith('/share/')) {
                const shareId = urlPath.split('/').pop();
                
                fetch(`${API_URL}/api/code/${shareId}`)
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        }
                        throw new Error('Code not found');
                    })
                    .then(data => {
                        codeEditor.setValue(data.code);
                        languageSelect.value = data.language;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Shared code not found or an error occurred.');
                    });
            }
        }
        
        checkSharedCode();

        runButton.addEventListener('click', function() {
            const code = codeEditor.getValue();
            const language = languageSelect.value;
            
            if (code.trim() === '') {
                outputArea.textContent = 'Error: Code field is empty!';
                return;
            }
            
            runButton.disabled = true;
            runButton.textContent = 'Running...';
            outputArea.textContent = 'Code is running...';
            
            fetch(`${API_URL}/api/execute`, {
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
                if (data.error) {
                    outputArea.textContent = `Error: ${data.error}`;
                } else if (data.output) {
                    outputArea.textContent = data.output;
                } else {
                    outputArea.textContent = 'Code executed, but no output was returned.';
                }
            })
            .catch(error => {
                outputArea.textContent = `Request error: ${error.message}`;
                console.error('Error:', error);
            })
            .finally(() => {
                runButton.disabled = false;
                runButton.textContent = 'Run Code';
            });
        });

        clearButton.addEventListener('click', function() {
            codeEditor.setValue('');
            outputArea.textContent = 'Result will appear here...';
        });


        shareButton.addEventListener('click', function() {
            const code = codeEditor.getValue();
            const language = languageSelect.value;
            
            if (code.trim() === '') {
                alert('You need to enter code to share!');
                return;
            }
            
            fetch(`${API_URL}/api/share`, {
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
                if (data.share_url) {
                    shareUrlInput.value = data.share_url;
                    shareUrlInput.select();
                } else if (data.error) {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch(error => {
                alert(`Request error: ${error.message}`);
                console.error('Error:', error);
            });
        });

        copyButton.addEventListener('click', function() {
            shareUrlInput.select();
            document.execCommand('copy');
            alert('URL copied!');
        });

        languageSelect.addEventListener('change', function() {
            const language = languageSelect.value;
            if (language !== 'python') {
                alert(`Sorry, ${language} is not supported yet.`);
                languageSelect.value = 'python';
            }
        });
    });
