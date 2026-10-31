FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src
EXPOSE 8094
CMD ["uvicorn","i24.api:app","--host","0.0.0.0","--port","8094"]
