# AI Secret Hitler

AI models play Secret Hitler against each other.

<img width="1470" height="833" alt="Screenshot 2025-12-27 at 2 39 41 PM" src="https://github.com/user-attachments/assets/17f304f3-8a7a-4be9-9d6d-54d4d8f730c5" />



## Installation

```bash
cd ai-secret-hitler
pip install -r requirements.txt
```

## Usage

### Set your API key

```bash
export OPENROUTER_API_KEY=your_key_here
```

### Run a game

```bash
python main.py
```

### Options

```bash
python main.py --help

# Specify number of players (5-10)
python main.py --players 7

# Save game log to specific file
python main.py --output game.json

# Quiet mode (minimal output)
python main.py --quiet

# List available models
python main.py --list-models
```

### Live Game Viewer

Watch games being played in real-time in your browser:

```bash
# Start the server
python server.py

# Open http://localhost:5000 in your browser
# Click "START LIVE GAME" to begin
```

## Available Models

The following models are configured by default:

1. GPT-4o (OpenAI)
2. GPT-5.1 (OpenAI)
3. Claude Opus 4.5 (Anthropic)
4. Claude Sonnet 4.5 (Anthropic)
5. Claude 3.5 Sonnet (Anthropic)
6. Llama 3.3 70B (Meta)
7. Grok 4 (xAI)
