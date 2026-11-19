# Built by `lk agent deploy`. The build context is this directory only, so the
# agent must not depend on other workspace packages.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home agent
USER agent

CMD ["python", "-m", "fromage_agent.worker", "start"]
