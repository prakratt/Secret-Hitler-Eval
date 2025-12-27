#!/usr/bin/env python3
"""Test script for game logic without API calls."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.game import GameEngine, GameState, GamePhase, VoteChoice, Policy


def test_basic_game_flow():
    """Test a complete game flow with manual actions."""
    print("=" * 60)
    print("Testing Secret Hitler Game Logic")
    print("=" * 60)

    # Create a 7-player game
    model_names = [
        "Claude", "GPT-4", "Gemini", "Llama", "Mistral", "DeepSeek", "Qwen"
    ]

    state = GameState(player_count=7)
    engine = GameEngine(state)

    # Track events
    events = []
    def on_event(event_type, data):
        events.append((event_type, data))
        print(f"  [{event_type}] {data}")

    engine.on_event = on_event

    # Start game
    print("\n1. Starting game...")
    result = engine.start_game(model_names)
    assert result.success, f"Failed to start: {result.message}"
    print(f"   Started with {len(state.players)} players")
    print(f"   President: seat {state.president_index}")

    # Show roles
    print("\n   Roles assigned:")
    for p in state.players:
        print(f"   Seat {p.seat}: {p.name} - {p.role.value} ({p.team.value})")

    # Test nomination
    print("\n2. Testing nomination phase...")
    assert state.phase == GamePhase.NOMINATION
    eligible = state.get_eligible_chancellors()
    print(f"   Eligible chancellors: {eligible}")

    result = engine.nominate_chancellor(eligible[0])
    assert result.success, f"Failed to nominate: {result.message}"
    print(f"   Nominated seat {eligible[0]}")

    # Test voting
    print("\n3. Testing election phase...")
    assert state.phase == GamePhase.ELECTION

    # All players vote Ja
    for seat in range(7):
        if not state.get_player(seat).is_dead:
            result = engine.cast_vote(seat, VoteChoice.JA)
            print(f"   Seat {seat} voted JA")

    # Election should have passed
    assert state.phase == GamePhase.LEGISLATIVE_PRESIDENT
    print("   Election passed!")

    # Test legislative session
    print("\n4. Testing legislative session...")
    policies = state.current_policies
    print(f"   President drew: {[p.value for p in policies]}")

    result = engine.president_discard(0)
    assert result.success, f"Failed to discard: {result.message}"
    print(f"   President discarded policy 0")

    # Chancellor's turn
    assert state.phase == GamePhase.LEGISLATIVE_CHANCELLOR
    policies = state.policies_for_chancellor
    print(f"   Chancellor received: {[p.value for p in policies]}")

    result = engine.chancellor_enact(0)
    assert result.success, f"Failed to enact: {result.message}"
    print(f"   Chancellor enacted policy 0")

    # Check result
    print(f"\n5. After first round:")
    print(f"   Liberal policies: {state.board.liberal_policies}")
    print(f"   Fascist policies: {state.board.fascist_policies}")

    # Run a few more rounds
    print("\n6. Simulating more rounds...")
    for round_num in range(5):
        if state.phase == GamePhase.GAME_OVER:
            break

        if state.phase == GamePhase.NOMINATION:
            eligible = state.get_eligible_chancellors()
            if eligible:
                engine.nominate_chancellor(eligible[0])

        elif state.phase == GamePhase.ELECTION:
            for seat in range(7):
                player = state.get_player(seat)
                if not player.is_dead and seat not in state.votes:
                    engine.cast_vote(seat, VoteChoice.JA)

        elif state.phase == GamePhase.LEGISLATIVE_PRESIDENT:
            engine.president_discard(0)

        elif state.phase == GamePhase.LEGISLATIVE_CHANCELLOR:
            engine.chancellor_enact(0)

        elif state.phase == GamePhase.EXECUTIVE_ACTION:
            # Handle executive actions
            from src.game.types import ExecutiveAction
            action = state.pending_executive_action

            if action == ExecutiveAction.INVESTIGATE_LOYALTY:
                targets = [p.seat for p in state.players
                          if not p.is_dead and p.seat != state.president_index and not p.was_investigated]
                if targets:
                    engine.investigate_player(targets[0])

            elif action == ExecutiveAction.SPECIAL_ELECTION:
                targets = [p.seat for p in state.players
                          if not p.is_dead and p.seat != state.president_index]
                if targets:
                    engine.call_special_election(targets[0])

            elif action == ExecutiveAction.POLICY_PEEK:
                engine.peek_policies()

            elif action == ExecutiveAction.EXECUTION:
                targets = [p.seat for p in state.players
                          if not p.is_dead and p.seat != state.president_index]
                if targets:
                    engine.execute_player(targets[0])

    print(f"\n   Final state:")
    print(f"   Liberal policies: {state.board.liberal_policies}")
    print(f"   Fascist policies: {state.board.fascist_policies}")
    print(f"   Phase: {state.phase.value}")

    if state.winner:
        print(f"\n   WINNER: {state.winner.value}")
        print(f"   Condition: {state.win_condition.value}")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)

    return True


def test_tools():
    """Test tool definitions."""
    print("\n" + "=" * 60)
    print("Testing Tool Definitions")
    print("=" * 60)

    from src.tools.definitions import GAME_TOOLS, get_tool_definitions

    print(f"\nTotal tools defined: {len(GAME_TOOLS)}")
    for tool in GAME_TOOLS:
        print(f"  - {tool['function']['name']}")

    # Test filtering
    available = get_tool_definitions(["vote", "discuss"])
    print(f"\nFiltered tools for ['vote', 'discuss']: {len(available)}")
    for tool in available:
        print(f"  - {tool['function']['name']}")

    assert len(available) == 2
    print("\nTool tests passed!")


if __name__ == "__main__":
    test_basic_game_flow()
    test_tools()
