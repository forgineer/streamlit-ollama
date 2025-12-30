# Streamlit-Ollama

Streamlit-Ollama is a simple, self-hostable AI chat application that uses Streamlit for a minimal UI and Ollama as the model server. The project focuses on simplicity and configurability — you can point the app at a local or remote Ollama host via a single configuration constant.

## Requirements

- Python 3.12+
- Ollama server reachable at the configured host
- See project dependencies in the [pyproject.toml](pyproject.toml) file
- Docker (optional)

## Quickstart — clone, install, and run locally

> ✋ This Quickstart assumes that you are serving Ollama from your `localhost` to run out of the box. If you are hosting Ollama externally, please be sure to read the Configuration and Customization section of this page before running the app.

1. Clone the repository:

```sh
git clone https://github.com/forgineer/streamlit-ollama.git
cd streamlit-ollama
```

2. Create a virtual environment and install:

```sh
python3 -m venv .venv   # or python -m venv .venv on Windows
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install .
```

3. Run the app locally:

```sh
streamlit run src/app.py --server.port=8501
```

Open http://localhost:8501 in your browser to start using the app! Starting the server will also create a local 'data' directory with a 'streamlit-ollama.db' SQLite file for storing any saved chat conversations.

## Configuration and Customization

Out of the box, the app is configured to look for Ollama being served locally or at `localhost`. This is primarily for quick setup with Docker on the same server where Ollama might be running. However, if Ollma isn't running locally, you will need to configure the app to look externally.

All available configurations and customizations can be made in the config.py file. Most notibly, the `STREAMLIT_OLLAMA_HOST` variable that points to the Ollama service.

## Run with Docker (local or external server)

Streamlit-Ollama shines best when running as a Docker container since Streamlit apps, by their nature, are meant for deployments to the cloud. However, due to the nature of this project, the container build and deployment is up to you. I have tried to make this as easy as possible though.

Assuming you remotely logged into your server and have followed the first step of cloning and navigating to the `streamlit-ollama` directory (see Quickstart) these next two commands should help you bulid and run the container.

> ✋ Prior to building your container, ensure that any additional configurations or customizations are well aligned.

Build the image:
```sh
docker build -t streamlit-ollama .
```

Run locally (host networking, exposes port 8501):
```sh
docker run -d --restart=unless-stopped --network host -p 8501:8501 -v "$(pwd)/data:/streamlit-ollama/data" streamlit-ollama
```

## Troubleshooting

- If the app cannot reach Ollama, verify the URL in [`STREAMLIT_OLLAMA_HOST`](src/config.py) and network connectivity. If you are accessing Ollama externally you should also ensure that the Ollama service is accessable from the network (eg. 0.0.0.0).

## Disclaimers and Contributing

This project is meant for simplicity and offer a more self-hosted oriented option among the MANY other AI clients out there (ex. Open WebUI). All current and future features will likely continue to center around simplicity and only offer features that make it easier to interface with Ollama with the out of the box features of Streamlit (without custom components).

Contributions (or Issues logged) are welcome through forking and pull request while keeping the above in mind.
