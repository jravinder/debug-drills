FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8765
CMD ["sh", "-c", "[ -f harbor.db ] || python seed.py; uvicorn harbor.app:app --host 0.0.0.0 --port 8765"]
