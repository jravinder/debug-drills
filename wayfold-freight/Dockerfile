FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8775
CMD ["sh", "-c", "[ -f wayfold.db ] || python seed.py; uvicorn wayfold.app:app --host 0.0.0.0 --port 8775"]
