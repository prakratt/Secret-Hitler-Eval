#!/usr/bin/env python3
"""HTTP server for live game streaming."""
import os
import sys
import json
import threading
import time
from pathlib import Path
from flask import Flask, send_from_directory, Response, jsonify
from flask_cors import CORS

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import GameOrchestrator
from src.ai.openrouter import AVAILABLE_MODELS

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Global state for event streaming
event_queue = []
event_listeners = []
game_running = False
orchestrator = None
game_thread = None

def event_handler(event_type: str, data: dict):
    """Handle game events and broadcast to listeners."""
    event = {
        "type": event_type,
        "data": data,
        "timestamp": time.time()
    }
    event_queue.append(event)
    
    # Broadcast to all connected clients
    for listener in event_listeners[:]:  # Copy list to avoid modification during iteration
        try:
            listener(event)
        except Exception as e:
            print(f"Error broadcasting to listener: {e}")
            if listener in event_listeners:
                event_listeners.remove(listener)

@app.route('/')
def index():
    """Serve the standalone HTML file."""
    return send_from_directory('frontend', 'standalone.html')

@app.route('/api/events')
def stream_events():
    """Server-Sent Events stream for game events."""
    def generate():
        # Send all queued events first
        for event in event_queue:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Then listen for new events
        new_events = []
        
        def add_event(event):
            new_events.append(event)
        
        event_listeners.append(add_event)
        
        try:
            while True:
                if new_events:
                    event = new_events.pop(0)
                    yield f"data: {json.dumps(event)}\n\n"
                else:
                    yield f": keepalive\n\n"  # Keep connection alive
                    time.sleep(0.5)
        finally:
            if add_event in event_listeners:
                event_listeners.remove(add_event)
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })

@app.route('/api/status')
def status():
    """Get current game status."""
    return jsonify({
        "running": game_running,
        "events_count": len(event_queue)
    })

@app.route('/api/stop', methods=['POST'])
def stop_game():
    """Stop the current game."""
    global game_running, orchestrator, game_thread
    
    if not game_running:
        return jsonify({"error": "No game running"}), 400
    
    # Signal game to stop
    if orchestrator:
        orchestrator.stop()
    
    game_running = False
    event_handler("game_stopped", {"message": "Game stopped by user"})
    
    return jsonify({"status": "stopped"})

@app.route('/api/start', methods=['POST'])
def start_game():
    """Start a new game."""
    global game_running, orchestrator, event_queue
    
    if game_running:
        return jsonify({"error": "Game already running"}), 400
    
    import os
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "OPENROUTER_API_KEY not set"}), 500
    
    # Get player count from request or use default
    from flask import request
    player_count = request.json.get('players', 7) if request.json else 7
    
    # Clear previous events
    event_queue.clear()
    
    # Start game in background thread
    def run_game():
        global game_running, orchestrator
        
        try:
            game_running = True
            models = AVAILABLE_MODELS[:player_count]
            
            orchestrator = GameOrchestrator(
                api_key=api_key,
                models=models,
                on_event=event_handler,
                max_rounds=50,
                discussion_rounds=1
            )
            
            orchestrator.setup_game()
            orchestrator.run_game()
            
            # Auto-save log if game completed (not stopped)
            if not orchestrator.should_stop:
                logs_dir = Path(__file__).parent / "logs"
                logs_dir.mkdir(exist_ok=True)
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_path = logs_dir / f"game_{timestamp}.json"
                orchestrator.save_log(str(log_path))
            
        except Exception as e:
            event_handler("error", {"message": str(e)})
        finally:
            game_running = False
            if orchestrator:
                orchestrator.cleanup()
    
    game_thread = threading.Thread(target=run_game, daemon=True)
    game_thread.start()
    
    return jsonify({"status": "started", "players": player_count})

if __name__ == '__main__':
    print("Starting server on http://localhost:5000")
    print("Open http://localhost:5000 in your browser to watch games live!")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)

