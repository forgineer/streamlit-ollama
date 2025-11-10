# Streamlit-Ollama

Streamlit-Ollama is a simple, self-hostable AI chat application that uses Streamlit for a minimal UI and Ollama as the model server. The project focuses on simplicity and configurability — you can point the app at a local or remote Ollama host via a single configuration constant.

## Requirements
- Python 3.12+
- Ollama server reachable at the configured host
- See project dependencies in [pyproject.toml](pyproject.toml)

## Quickstart — clone, install, run
1. Clone the repository:
```sh
git clone https://github.com/forgineer/streamlit-ollama.git
cd streamlit-ollama
```

2. Create a virtual environment and install:
```sh
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .
```

3. Run the app locally:
```sh
streamlit run src/app.py --server.port=8501
```

Open http://localhost:8501 in your browser.

## Configure the Ollama host and logging
Edit the configuration constants in [src/config.py](src/config.py):

- [`STREAMLIT_OLLAMA_HOST`](src/config.py) — the Ollama server URL (default: `http://localhost:11434`)
- [`logger`](src/config.py) — logging helper; it configures output to stdout for easy viewing

If you prefer environment-driven configuration or runtime replacement in Docker, replace or mount a custom `config.py` before starting the container.

## Run with Docker (local or external server)
Build the image:
```sh
docker build -t streamlit-ollama .
```

Run locally (host networking, exposes port 8501):
```sh
docker run -d --rm --network host -p 8501:8501 streamlit-ollama
```

Notes:
- The Dockerfile copies `src/app.py` and `src/config.py` into the image. To point at a remote Ollama host, edit `src/config.py` before building or mount a custom `config.py` into the container at runtime:
```sh
docker run -v "$(pwd)/src/config.py:/config.py:ro" -p 8501:8501 streamlit-ollama
```

## Troubleshooting
- If the app cannot reach Ollama, confirm the URL in [`STREAMLIT_OLLAMA_HOST`](src/config.py) and network connectivity.
- Logs are emitted to stdout by the configured [`logger`](src/config.py). When running Docker, view logs with `docker logs <container-id>` or check the terminal when running locally.

## Files of interest
- App entry: [src/app.py](src/app.py)
- Configuration: [src/config.py](src/config.py)
- Packaging: [pyproject.toml](pyproject.toml)
- Docker: [Dockerfile](Dockerfile)
