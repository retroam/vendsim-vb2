FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY vendsim_vb2/ vendsim_vb2/

RUN pip install --no-cache-dir ".[server]"

EXPOSE 7860

CMD ["uvicorn", "vendsim_vb2.server.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "7860"]
