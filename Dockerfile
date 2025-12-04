FROM python:3.10-slim

WORKDIR /app

# Copia dependências
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia seu arquivo (renomeando internamente para evitar problema com ponto no nome)
COPY monaimockv.1.0.py ./app.py

EXPOSE 8000

# 4 workers + 4 threads = até 16 requisições simultâneas
CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:8000", "app:app"]
