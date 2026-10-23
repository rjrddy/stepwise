FROM node:22-bookworm-slim AS web
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home app
COPY --from=web /web/dist ./apps/web/dist
USER 10001
ENV HOST=0.0.0.0 PORT=8091
EXPOSE 8091
CMD ["python", "-m", "stepwise.server"]
