FROM python:3.12-slim

WORKDIR /streamlit-ollama

# Copy only the necessary files from the build context.
# Users should clone the repo locally and run `docker build .` from the repo root.
COPY pyproject.toml ./
COPY src/app.py ./app.py
COPY src/config.py ./config.py
COPY images/ ./images/

# Install Python dependencies defined in pyproject.toml
RUN pip3 install .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py"]
