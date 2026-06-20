FROM python:3.11-slim

WORKDIR /app

# Instala as dependências de sistema se seu app precisar buildar pacotes C
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O Railway injeta dinamicamente a porta, mas expor a 8080 ajuda o proxy dele a te achar
EXPOSE 8080

# Usamos a variável $PORT que o Railway dá. Se ela não existir, ele usa a 8080 por padrão.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 3 --loop uvloop --http httptools"]