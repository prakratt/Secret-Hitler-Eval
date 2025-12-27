#!/usr/bin/env python3
"""Main entry point for AI Secret Hitler."""
import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import GameOrchestrator
from src.ai.openrouter import AVAILABLE_MODELS, ModelConfig
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text


console = Console()


def print_event(event_type: str, data: dict):
    """Pretty print game events."""
    if event_type == "game_started":
        console.print(Panel.fit(
            f"[bold green]Game Started![/] {len(data['players'])} players",
            title="Secret Hitler"
        ))
        for p in data['players']:
            console.print(f"  Seat {p['seat']}: {p['name']}")

    elif event_type == "game_setup_complete":
        console.print("\n[bold cyan]All AI players ready![/]\n")

    elif event_type == "chancellor_nominated":
        console.print(f"\n[yellow]President (seat {data['president_seat']}) nominates seat {data['chancellor_seat']} as Chancellor[/]")

    elif event_type == "election_result":
        result = "[green]PASSED[/]" if data['passed'] else "[red]FAILED[/]"
        console.print(f"[bold]Election {result}[/] (Ja: {data['ja_votes']}, Nein: {data['nein_votes']})")

    elif event_type == "policy_enacted":
        policy_color = "blue" if data['policy'] == "liberal" else "red"
        console.print(f"\n[bold {policy_color}]{data['policy'].upper()}[/] policy enacted!")
        console.print(f"  Liberal: {data['liberal_count']}/5 | Fascist: {data['fascist_count']}/6")

    elif event_type == "discussion_message":
        console.print(f"  [{data['player']}]: {data['message']}")

    elif event_type == "player_executed":
        console.print(f"\n[bold red]EXECUTION![/] Player in seat {data['target']} was executed!")
        if data['was_hitler']:
            console.print("[bold green]IT WAS HITLER![/]")

    elif event_type == "game_over":
        winner_color = "blue" if data['winner'] == "liberal" else "red"
        console.print(Panel.fit(
            f"[bold {winner_color}]{data['winner'].upper()} WINS![/]\n\n"
            f"Condition: {data['condition']}",
            title="Game Over",
            border_style=winner_color
        ))

        # Show final roles
        table = Table(title="Player Roles Revealed")
        table.add_column("Seat", justify="center")
        table.add_column("Model", style="cyan")
        table.add_column("Role", justify="center")
        table.add_column("Team", justify="center")
        table.add_column("Status", justify="center")

        for p in data['players']:
            role_color = "yellow" if p['role'] == "hitler" else ("red" if p['team'] == "fascist" else "blue")
            status = "[red]DEAD[/]" if p['is_dead'] else "[green]Alive[/]"
            table.add_row(
                str(p['seat']),
                p['name'],
                f"[{role_color}]{p['role'].upper()}[/]",
                f"[{role_color}]{p['team'].upper()}[/]",
                status
            )
        console.print(table)

    elif event_type == "new_round":
        console.print(f"\n[bold]═══ Round {data['round_number']} ═══[/]")
        console.print(f"President: seat {data['president_seat']}")


def main():
    parser = argparse.ArgumentParser(description="Run an AI Secret Hitler game")
    parser.add_argument("--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY env var)")
    parser.add_argument("--players", type=int, default=7, choices=range(5, 11),
                       help="Number of players (5-10)")
    parser.add_argument("--output", help="Save game log to this file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--list-models", action="store_true", help="List available models")

    args = parser.parse_args()

    if args.list_models:
        console.print("[bold]Available Models:[/]")
        for i, model in enumerate(AVAILABLE_MODELS):
            console.print(f"  {i+1}. {model.name} ({model.provider}) - {model.id}")
        return

    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: No API key provided.[/]")
        console.print("Set OPENROUTER_API_KEY environment variable or use --api-key flag")
        sys.exit(1)

    # Select models for the game
    models = AVAILABLE_MODELS[:args.players]

    console.print(Panel.fit(
        "[bold]AI Secret Hitler[/]\n\n"
        f"Players: {args.players}\n"
        f"Models: {', '.join(m.name for m in models)}",
        title="Game Setup"
    ))

    # Create and run game
    event_handler = None if args.quiet else print_event

    orchestrator = GameOrchestrator(
        api_key=api_key,
        models=models,
        on_event=event_handler,
        max_rounds=50,
        discussion_rounds=1  # Keep discussion short for faster games
    )

    try:
        console.print("\n[bold]Starting game...[/]\n")
        result = orchestrator.run_game()

        # Print summary
        if not args.quiet:
            console.print("\n[bold]Game Summary:[/]")
            console.print(f"  Duration: {result['duration']:.1f}s")
            console.print(f"  Rounds: {result['rounds']}")
            console.print(f"  Winner: {result['winner']}")
            console.print(f"  Condition: {result['win_condition']}")

        # Save log if requested
        if args.output:
            orchestrator.save_log(args.output)
            console.print(f"\n[green]Game log saved to {args.output}[/]")
        else:
            # Auto-save to logs directory
            logs_dir = Path(__file__).parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_path = logs_dir / f"game_{timestamp}.json"
            orchestrator.save_log(str(log_path))
            console.print(f"\n[dim]Game log saved to {log_path}[/]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Game interrupted.[/]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/]")
        raise
    finally:
        orchestrator.cleanup()


if __name__ == "__main__":
    main()
