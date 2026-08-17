# ---- Backend ----
FROM python:3.11-slim AS backend

WORKDIR /app/backend

# Install system deps for torch/faiss
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libgomp1 && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["python", "run.py"]


# ---- Frontend Build ----
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build


# ---- Production (Nginx serves frontend, proxies API to backend) ----
FROM nginx:alpine AS production

# Copy built frontend
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Nginx config for SPA routing + API proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
