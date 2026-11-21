# Built by `lk agent deploy`. The build context is this directory only, so the
# agent must not depend on other workspace packages.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
# requirements.txt is exported from uv.lock, so the image uses the tested versions.
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir --no-deps .

RUN useradd --create-home agent
USER agent

CMD ["python", "-m", "fromage_agent.worker", "start"]
