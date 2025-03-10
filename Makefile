.PHONY: setup run test clean deploy restart logs


env:
	source env/bin/activate

setup:
	make env 
	pip install -r requirements.txt

server-start:
	make env 
	make supervisor-stop
	make setup
	make supervisor-start

server-stop:
	make supervisor-stop

server-restart:
	make supervisor-restart

run:
	python main.py


supervisor-start:
	supervisorctl start chiroqcha
supervisor-stop:
	supervisorctl stop chiroqcha
supervisor-restart:
	supervisorctl restart chiroqcha

run-background:
	nohup python main.py > app.log 2>&1 &
	@echo "Application started in background. Check logs with 'make logs'"

test:
	pytest

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -f *.pyc
	rm -f *.log

stop:
	@echo "Stopping application..."
	-pkill -f "python main.py" || echo "Application was not running"

restart: stop run-background
	@echo "Application restarted"

logs:
	@if [ -f app.log ]; then \
		tail -f app.log; \
	else \
		echo "Log file not found. Start the application first."; \
	fi

deploy:
	@echo "Deploying to server..."
	git pull
	make setup
	make restart
	@echo "Deployment completed successfully!"

status:
	@if pgrep -f "python main.py" > /dev/null; then \
		echo "Application is running"; \
	else \
		echo "Application is not running"; \
	fi

help:
	@echo "Available commands:"
	@echo "  make setup          - Install required packages"
	@echo "  make run            - Run the application in foreground"
	@echo "  make run-background - Run the application in background"
	@echo "  make stop           - Stop the application"
	@echo "  make restart        - Restart the application"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Remove temporary files"
	@echo "  make logs           - View application logs"
	@echo "  make deploy         - Deploy the application (git pull, setup, restart)"
	@echo "  make status         - Check if the application is running"
	@echo "  make help           - Show this help message"

default: help