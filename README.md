# AI Secret Hitler

AI models play Secret Hitler against each other.

![Game Screenshot](Screenshot%202025-12-27%20at%202.39.41%20PM.png)

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