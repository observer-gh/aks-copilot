# syntax=docker/dockerfile:1

# ---- Builder Stage ----
# This stage builds a virtual environment with all dependencies.
FROM python:3.11-slim as builder

# 1. Install uv
RUN pip install uv

# 2. Create a virtual environment
ENV VENV_PATH=/opt/venv
RUN python -m venv $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# 3. Copy dependency definitions and install them into the venv
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv pip install --no-cache .

# ---- Final Stage ----
# This stage creates the final, lean image.
FROM python:3.11-slim

# 1. Set up non-root user
RUN useradd -m appuser
USER appuser
WORKDIR /home/appuser/app

# 2. Copy the virtual environment from the builder stage
ENV VENV_PATH=/opt/venv
COPY --from=builder $VENV_PATH $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# 3. Copy source code
COPY --chown=appuser:appuser . .

# 4. Set up entrypoint
COPY --chown=appuser:appuser .docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["--help"]
