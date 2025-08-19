# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app


# Copy project files
COPY db/ ./db
COPY data/ ./data
COPY app/ ./app/

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install punkt and punkt_tab into a fixed location
RUN python -m nltk.downloader punkt punkt_tab -d /usr/local/nltk_data

# Specify Env Variable
ENV NLTK_DATA=/usr/local/nltk_data



# Expose port
EXPOSE 8000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
