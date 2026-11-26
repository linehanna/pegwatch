# PegWatch ingestion jobs for Cloud Run.
# Build context is the REPO ROOT, so the shared package can be copied in.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY shared/pyproject.toml shared/README.md ./shared/
COPY shared/pegwatch_shared ./shared/pegwatch_shared
RUN pip install "./shared[gcp]"

# Run as a non-root user
RUN useradd --create-home pegwatch
USER pegwatch

# The job name and sink are passed as arguments by the Cloud Run job, e.g.
#   --job market_hourly --sink gs://pegwatch-bronze-9aa513
ENTRYPOINT ["python", "-m", "pegwatch_shared.ingest"]
