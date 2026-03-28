FROM python:3.12-slim

WORKDIR /app

COPY bastion-compat/pyproject.toml bastion-compat/README.md bastion-compat/wsgi.py ./
COPY bastion-compat/src/ src/
COPY bastion-compat/data/ data/

RUN pip install --no-cache-dir ".[web]" gunicorn

ENV BASTION_HOSTED=true

EXPOSE 8000

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30"]
