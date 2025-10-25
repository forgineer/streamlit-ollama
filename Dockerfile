FROM python:3.12-slim

WORKDIR /streamlit-ollama

# Copy only the necessary files from the build context.
# Users should clone the repo locally and run `docker build .` from the repo root.
COPY images/ ./images/
COPY src/app.py ./app.py
COPY src/config.py ./config.py
COPY pyproject.toml ./

# Install Python dependencies defined in pyproject.toml
RUN pip3 install .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# To build the Docker image, run:
# docker build -t streamlit-ollama .

# To run the Docker container, run:
# docker run -d --rm --network host -p 8501:8501 streamlit-ollama
