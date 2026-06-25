FROM python:3.12-slim@sha256:46cb7cc2877e60fbd5e21a9ae6115c30ace7a077b9f8772da879e4590c18c2e3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:/root/.local/bin:${PATH}"

WORKDIR /app

COPY pyproject.toml README.md LICENSE uv.lock ./
COPY src ./src

ADD https://astral.sh/uv/install.sh /tmp/uv-installer.sh

RUN chmod +x /tmp/uv-installer.sh \
    && UV_UNMANAGED_INSTALL=/root/.local /tmp/uv-installer.sh \
    && uv sync --locked --no-dev --extra api \
    && rm /tmp/uv-installer.sh

EXPOSE 8000

CMD ["uvicorn", "alcove_dux.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
