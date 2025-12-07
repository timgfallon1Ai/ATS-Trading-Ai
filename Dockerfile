FROM python:3.11-slim

# Ensure Python paths are correct across agents
WORKDIR /app
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Install shared dependencies for all agents
COPY libs/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy shared libs folder
COPY libs /app/libs

# Copy ALL services so each agent can run from its subfolder
COPY services /app/services

# Default entrypoint (overridden per service in docker-compose)
CMD ["python", "--version"]
