"""Game orchestrator that runs AI Secret Hitler games."""
from __future__ import annotations
import json
import time
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from .game import GameEngine, GameState, GamePhase, VoteChoice
from .ai import OpenRouterClient, AIPlayer
from .ai.openrouter import ModelConfig, AVAILABLE_MODELS


@dataclass
class GameLog:
    """Logs game events for replay and analysis."""
    events: list[dict] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0

    def add(self, event_type: str, data: dict):
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        })

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump({
                "events": self.events,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "duration": self.end_time - self.start_time
            }, f, indent=2)


class GameOrchestrator:
    """Orchestrates an AI Secret Hitler game."""

    def __init__(
        self,
        api_key: str,
        models: Optional[list[ModelConfig]] = None,
        on_event: Optional[Callable[[str, dict], None]] = None,
        max_rounds: int = 50,
        discussion_rounds: int = 2  # Number of discussion rounds before voting
    ):
        self.api_key = api_key
        self.models = models or AVAILABLE_MODELS[:7]
        self.on_event = on_event
        self.max_rounds = max_rounds
        self.discussion_rounds = discussion_rounds
        self.should_stop = False  # Flag to stop the game

        self.client = OpenRouterClient(api_key)
        self.engine: Optional[GameEngine] = None
        self.ai_players: dict[int, AIPlayer] = {}
        self.log = GameLog()
    
    def stop(self):
        """Signal the game to stop."""
        self.should_stop = True

    def emit(self, event_type: str, data: dict):
        """Emit an event."""
        self.log.add(event_type, data)
        if self.on_event:
            self.on_event(event_type, data)

    def setup_game(self):
        """Set up a new game."""
        # Create game engine
        state = GameState(player_count=len(self.models))
        self.engine = GameEngine(state)

        # Set up event forwarding
        self.engine.on_event = self.emit

        # Get model names
        model_names = [m.name for m in self.models]

        # Start the game
        self.engine.start_game(model_names)

        # Create AI players
        self.ai_players = {}
        for seat, model in enumerate(self.models):
            player = AIPlayer(
                seat=seat,
                model=model,
                client=self.client
            )

            # Set role info
            game_state = self.engine.state
            game_player = game_state.get_player(seat)
            knowledge = game_state.get_fascist_knowledge(seat)

            player.set_role_info(
                role=game_player.role.value,
                team=game_player.team.value,
                known_fascists=knowledge["known_fascists"],
                known_hitler=knowledge["known_hitler"]
            )

            self.ai_players[seat] = player

        self.emit("game_setup_complete", {
            "player_count": len(self.models),
            "players": [
                {
                    "seat": seat,
                    "model": model.name,
                    "model_id": model.id,
                    "name": model.name,
                    "role": game_state.get_player(seat).role.value,
                    "team": game_state.get_player(seat).team.value,
                    "is_dead": False
                }
                for seat, model in enumerate(self.models)
            ]
        })

    def run_game(self) -> dict:
        """Run the game to completion."""
        self.log.start_time = time.time()

        self.setup_game()

        round_count = 0
        while self.engine.state.phase != GamePhase.GAME_OVER and round_count < self.max_rounds and not self.should_stop:
            round_count += 1
            self._run_round()

        self.log.end_time = time.time()

        # Return results
        state = self.engine.state
        return {
            "winner": state.winner.value if state.winner else None,
            "win_condition": state.win_condition.value if state.win_condition else None,
            "rounds": state.round_number,
            "liberal_policies": state.board.liberal_policies,
            "fascist_policies": state.board.fascist_policies,
            "players": [
                {
                    "seat": p.seat,
                    "name": p.name,
                    "model": self.models[p.seat].id,
                    "role": p.role.value,
                    "team": p.team.value,
                    "is_dead": p.is_dead
                }
                for p in state.players
            ],
            "duration": self.log.end_time - self.log.start_time
        }

    def _run_round(self):
        """Run a single round of the game."""
        state = self.engine.state
        phase = state.phase

        self.emit("round_update", {
            "round": state.round_number,
            "phase": phase.value
        })

        if phase == GamePhase.NOMINATION:
            self._handle_nomination()
        elif phase == GamePhase.ELECTION:
            self._handle_election()
        elif phase == GamePhase.LEGISLATIVE_PRESIDENT:
            self._handle_president_legislative()
        elif phase == GamePhase.LEGISLATIVE_CHANCELLOR:
            self._handle_chancellor_legislative()
        elif phase == GamePhase.EXECUTIVE_ACTION:
            self._handle_executive_action()

    def _handle_nomination(self):
        """Handle the nomination phase."""
        state = self.engine.state
        president_seat = state.president_index
        president = self.ai_players[president_seat]

        # Run discussion first
        self._run_discussion("nomination")

        # Get president's action
        player_state = state.get_player_state(president_seat)
        available_actions = self.engine.get_available_actions(president_seat)

        action = president.get_action(player_state, available_actions)

        if action and action["name"] == "nominate_chancellor":
            chancellor_seat = int(action["arguments"]["player_seat"])
            result = self.engine.nominate_chancellor(chancellor_seat)

            self.emit("nomination_action", {
                "president": president_seat,
                "chancellor": chancellor_seat,
                "reasoning": action["arguments"].get("reasoning", ""),
                "result": result.message
            })

            # Notify all players
            for ai in self.ai_players.values():
                ai.add_event(f"President (seat {president_seat}) nominated seat {chancellor_seat} as Chancellor")
        else:
            # Fallback: nominate first eligible
            eligible = state.get_eligible_chancellors()
            if eligible:
                self.engine.nominate_chancellor(eligible[0])

    def _handle_election(self):
        """Handle the election phase."""
        state = self.engine.state

        # Run discussion
        self._run_discussion("election")

        # Collect votes from all living players
        for seat, ai in self.ai_players.items():
            if state.get_player(seat).is_dead:
                continue

            player_state = state.get_player_state(seat)
            available_actions = self.engine.get_available_actions(seat)

            action = ai.get_action(player_state, available_actions)

            if action and action["name"] == "vote":
                choice = VoteChoice.JA if action["arguments"]["choice"] == "ja" else VoteChoice.NEIN
                result = self.engine.cast_vote(seat, choice)

                self.emit("vote_action", {
                    "player": seat,
                    "vote": choice.value,
                    "reasoning": action["arguments"].get("reasoning", "")
                })
            else:
                # Fallback: random vote
                import random
                choice = random.choice([VoteChoice.JA, VoteChoice.NEIN])
                self.engine.cast_vote(seat, choice)

    def _handle_president_legislative(self):
        """Handle president's legislative phase."""
        state = self.engine.state
        president_seat = state.president_index
        president = self.ai_players[president_seat]

        player_state = state.get_player_state(president_seat)
        available_actions = self.engine.get_available_actions(president_seat)

        # Show president their cards
        policies = state.current_policies
        president.add_private_info(
            f"You drew 3 policies: {[p.value.upper() for p in policies]}. Choose one to discard."
        )

        action = president.get_action(player_state, available_actions)

        if action and action.get("name") == "discard_policy":
            arguments = action.get("arguments", {})
            discard_index = arguments.get("discard_index")
            
            if discard_index is not None:
                try:
                    discard_index = int(discard_index)
                    if not 0 <= discard_index < 3:
                        raise ValueError(f"Invalid discard_index: {discard_index}")
                    result = self.engine.president_discard(discard_index)

                    self.emit("president_discard_action", {
                        "president": president_seat,
                        "discard_index": discard_index,
                        "reasoning": arguments.get("reasoning", "")
                    })
                except (ValueError, TypeError) as e:
                    print(f"Warning: Invalid discard_index from {president.name}: {e}. Using fallback.")
                    # Fallback: discard first policy
                    self.engine.president_discard(0)
            else:
                print(f"Warning: Missing discard_index from {president.name}. Using fallback.")
                # Fallback: discard first policy
                self.engine.president_discard(0)
        else:
            # Fallback: discard first policy
            print(f"Warning: No valid discard_policy action from {president.name}. Using fallback.")
            self.engine.president_discard(0)

    def _handle_chancellor_legislative(self):
        """Handle chancellor's legislative phase."""
        state = self.engine.state
        chancellor_seat = state.chancellor_candidate_index
        chancellor = self.ai_players[chancellor_seat]

        player_state = state.get_player_state(chancellor_seat)
        available_actions = self.engine.get_available_actions(chancellor_seat)

        # Show chancellor their cards
        policies = state.policies_for_chancellor
        chancellor.add_private_info(
            f"You received 2 policies from President: {[p.value.upper() for p in policies]}. Choose one to enact."
        )

        action = chancellor.get_action(player_state, available_actions)

        if action:
            if action.get("name") == "enact_policy":
                arguments = action.get("arguments", {})
                enact_index = arguments.get("enact_index")
                
                if enact_index is not None:
                    try:
                        enact_index = int(enact_index)
                        if not 0 <= enact_index < 2:
                            raise ValueError(f"Invalid enact_index: {enact_index}")
                        result = self.engine.chancellor_enact(enact_index)

                        self.emit("chancellor_enact_action", {
                            "chancellor": chancellor_seat,
                            "enact_index": enact_index,
                            "reasoning": arguments.get("reasoning", "")
                        })

                        # Notify all players about enacted policy
                        for ai in self.ai_players.values():
                            ai.add_event(f"A {policies[enact_index].value.upper()} policy was enacted!")
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid enact_index from {chancellor.name}: {e}. Using fallback.")
                        # Fallback: enact first policy
                        self.engine.chancellor_enact(0)
                else:
                    print(f"Warning: Missing enact_index from {chancellor.name}. Using fallback.")
                    # Fallback: enact first policy
                    self.engine.chancellor_enact(0)

            elif action.get("name") == "propose_veto":
                self.engine.propose_veto()
                # Handle veto flow
                self._handle_veto()
        else:
            # Fallback: enact first policy
            print(f"Warning: No valid action from {chancellor.name}. Using fallback.")
            self.engine.chancellor_enact(0)

    def _handle_veto(self):
        """Handle veto proposal and response."""
        state = self.engine.state
        president_seat = state.president_index
        president = self.ai_players[president_seat]

        president.add_event("Chancellor has proposed to VETO the current agenda. Do you approve?")

        player_state = state.get_player_state(president_seat)
        available_actions = ["respond_to_veto"]

        action = president.get_action(player_state, available_actions)

        if action and action["name"] == "respond_to_veto":
            approve = action["arguments"]["approve"]
            self.engine.president_veto_response(approve)

            self.emit("veto_response", {
                "president": president_seat,
                "approved": approve,
                "reasoning": action["arguments"].get("reasoning", "")
            })
        else:
            # Fallback: reject veto
            self.engine.president_veto_response(False)

    def _handle_executive_action(self):
        """Handle executive action phase."""
        from .game.types import ExecutiveAction

        state = self.engine.state
        president_seat = state.president_index
        president = self.ai_players[president_seat]
        action_type = state.pending_executive_action

        player_state = state.get_player_state(president_seat)
        available_actions = self.engine.get_available_actions(president_seat)

        action = president.get_action(player_state, available_actions)

        # Handle the action or use fallback
        if action and action["name"] == "investigate_player":
            target = int(action["arguments"]["target_seat"])
            result = self.engine.investigate_player(target)

            target_player = state.get_player(target)
            president.add_private_info(
                f"Investigation result: Player in seat {target} is a {target_player.team.value.upper()}!"
            )

            self.emit("investigate_action", {
                "president": president_seat,
                "target": target,
                "result": target_player.team.value
            })

        elif action and action["name"] == "call_special_election":
            target = int(action["arguments"]["target_seat"])
            self.engine.call_special_election(target)

            self.emit("special_election_action", {
                "president": president_seat,
                "target": target
            })

            for ai in self.ai_players.values():
                ai.add_event(f"Special election called! Seat {target} is the new President.")

        elif action and action["name"] == "peek_policies":
            result = self.engine.peek_policies()
            top_policies = state.policy_deck.draw_pile[:3]
            president.add_private_info(
                f"Top 3 policies in deck: {[p.value.upper() for p in top_policies]}"
            )

            self.emit("peek_action", {
                "president": president_seat,
                "policies": [p.value for p in top_policies]
            })

        elif action and action["name"] == "execute_player":
            target = int(action["arguments"]["target_seat"])
            self.engine.execute_player(target)

            self.emit("execute_action", {
                "president": president_seat,
                "target": target
            })

            for ai in self.ai_players.values():
                ai.add_event(f"Player in seat {target} has been EXECUTED!")

        else:
            # Fallback: handle executive action automatically if AI didn't respond
            self.emit("executive_action_fallback", {
                "action_type": action_type.value,
                "president": president_seat
            })

            if action_type == ExecutiveAction.INVESTIGATE_LOYALTY:
                # Pick first uninvestigated player
                targets = [p.seat for p in state.players
                          if not p.is_dead and p.seat != president_seat and not p.was_investigated]
                if targets:
                    self.engine.investigate_player(targets[0])

            elif action_type == ExecutiveAction.SPECIAL_ELECTION:
                # Pick next player in order
                targets = [p.seat for p in state.players
                          if not p.is_dead and p.seat != president_seat]
                if targets:
                    self.engine.call_special_election(targets[0])

            elif action_type == ExecutiveAction.POLICY_PEEK:
                # Just peek (no choice needed)
                self.engine.peek_policies()

            elif action_type == ExecutiveAction.EXECUTION:
                # Pick a random non-president player (dangerous fallback!)
                import random
                targets = [p.seat for p in state.players
                          if not p.is_dead and p.seat != president_seat]
                if targets:
                    self.engine.execute_player(random.choice(targets))

    def _run_discussion(self, context: str):
        """Run a discussion phase where all players can talk."""
        state = self.engine.state

        for round_num in range(self.discussion_rounds):
            # Each living player gets a chance to speak
            for seat in range(len(self.ai_players)):
                player = state.get_player(seat)
                if player.is_dead:
                    continue

                ai = self.ai_players[seat]
                player_state = state.get_player_state(seat)
                available_actions = self.engine.get_available_actions(seat)

                # Only get discussion if it's available
                if "discuss" not in available_actions:
                    continue

                action = ai.get_action(player_state, ["discuss"])

                if action and action["name"] == "discuss":
                    message = action["arguments"]["message"]
                    self.engine.add_message(seat, message)

                    self.emit("discussion_message", {
                        "seat": seat,
                        "player": player.name,
                        "message": message
                    })

                    # Share message with all players
                    for other_ai in self.ai_players.values():
                        if other_ai.seat != seat:
                            other_ai.add_event(f"{player.name} (seat {seat}) says: \"{message}\"")

    def save_log(self, path: str):
        """Save the game log to a file."""
        self.log.save(path)

    def cleanup(self):
        """Clean up resources."""
        self.client.close()
