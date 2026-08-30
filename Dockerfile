FROM python:3.12-slim

WORKDIR /app

# System deps needed by matplotlib/xgboost/pyarrow wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY api/ ./api/
COPY web/ ./web/
COPY models/ ./models/
COPY outputs/ ./outputs/

EXPOSE 8000

# The image ships with the ALREADY-TRAINED closed-loop detector in /app/models
# (see README "How to run locally" for the from-scratch training commands).
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
