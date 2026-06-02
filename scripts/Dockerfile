FROM python:3.12-alpine
WORKDIR /app
RUN pip install requests --break-system-packages 2>/dev/null || pip install requests
COPY tracker-watcher.py .
CMD ["python3", "-u", "tracker-watcher.py"]
