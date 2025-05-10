FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/nanodlna.db
ENV DEBUG=False
ENV HOST=0.0.0.0
ENV PORT=8000

# Create a script to initialize the database and run the application
RUN echo '#!/bin/bash\n\
# Set Python path\n\
export PYTHONPATH=/app\n\
\n\
# Initialize the database\n\
python -c "from database.database import init_db; init_db()"\n\
\n\
# Run the application\n\
python run.py --host ${HOST} --port ${PORT}\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application
CMD ["/app/start.sh"]
