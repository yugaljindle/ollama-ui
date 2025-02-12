# Ollama UI
Simple `streamlit` web-app & fastapi server to communicate with Ollama backend. 


## Setup
1. Update `config.json` for app
2. Create & Activate a new python env with conda (`brew install --cask miniconda`)
2. `cd client` and run `pip install -r requirements.txt`
3. `cd server` and run `pip install -r requirements.txt`
1. Run Ollama server (localhost:11434)

## Run Client
`streamlit run client.py`

## Run Server
`python server.py`

## Web Browser
Open `https://localhost:8501/`