FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    LOG_FILE='/vol/web/logs/file.log'

# Create a dedicated appuser
RUN groupadd -r appuser && \
    useradd --no-log-init -r -g appuser appuser

# Update and install necessary packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        postgresql-client \
        postgresql-server-dev-all

# Set the working directory
WORKDIR /app

# Copy requirements files
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# Create a virtual environment and install dependencies
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    /py/bin/pip install -U 'Twisted[tls,http2]'

# Conditionally install dev dependencies
ARG DEV=false
RUN if [ "$DEV" = "true" ]; then /py/bin/pip install -r /tmp/requirements.dev.txt ; fi

# Cleanup
RUN rm -rf /tmp && \
    /py/bin/pip uninstall -y pip

# Create necessary directories and set permissions
RUN mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R appuser:appuser /vol/web && \
    mkdir -p /vol/web/logs && \
    chmod -R u+rwx,g+rx,o+rx /vol && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /vol && \
    echo > /vol/web/logs/file.log

# Copy app and scripts
COPY ./app /app
COPY ./scripts /scripts
RUN chmod -R +x /scripts

# Update PATH
ENV PATH="/scripts:/py/bin:$PATH"

# Switch to appuser
USER appuser

# Expose ports
EXPOSE 8000 8001

# Set the entrypoint
ENTRYPOINT ["run.sh"]