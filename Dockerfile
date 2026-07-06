# ---------- Build React ----------
FROM node:20 AS frontend

WORKDIR /frontend

COPY app/package*.json ./

RUN npm install

COPY app .

RUN npm run build


# ---------- Python ----------
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copy React build
COPY --from=frontend /frontend/dist ./app/dist

EXPOSE 8000

CMD ["uvicorn","api:app","--host","0.0.0.0","--port","8000"]