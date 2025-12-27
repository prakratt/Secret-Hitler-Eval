"""Game engine that manages game flow and phases."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Callable, List, Dict, Any
import time

from .types import (
    Team, Role, GamePhase, ExecutiveAction, Policy, VoteChoice, WinCondition,
    Player, get_executive_power
)
from .state import GameState, Message


@dataclass
class ActionResult:
    """Result of a game action."""
    success: bool
    message: str
    data: Optional[dict] = None


class GameEngine:
    """Manages the flow of a Secret Hitler game."""

    def __init__(self, state: Optional[GameState] = None):
        self.state = state or GameState(player_count=0)
        self.on_event: Optional[Callable[[str, dict], None]] = None

    def emit(self, event: str, data: dict):
        """Emit a game event."""
        if self.on_event:
            self.on_event(event, data)

    # ============ SETUP ============

    def start_game(self, model_names: list[str]) -> ActionResult:
        """Initialize and start a new game."""
        try:
            self.state.initialize_game(model_names)
            self.emit("game_started", {
                "players": [
                    {"seat": p.seat, "name": p.name}
                    for p in self.state.players
                ],
                "starting_president": self.state.president_index
            })
            return ActionResult(True, "Game started successfully")
        except ValueError as e:
            return ActionResult(False, str(e))

    # ============ NOMINATION PHASE ============

    def nominate_chancellor(self, chancellor_seat: int) -> ActionResult:
        """President nominates a chancellor candidate."""
        if self.state.phase != GamePhase.NOMINATION:
            return ActionResult(False, f"Wrong phase: {self.state.phase.value}")

        eligible = self.state.get_eligible_chancellors()
        if chancellor_seat not in eligible:
            return ActionResult(False, f"Seat {chancellor_seat} is not eligible for chancellor")

        self.state.chancellor_candidate_index = chancellor_seat
        self.state.votes = {}
        self.state.phase = GamePhase.ELECTION
        self.state.discussion_messages = []

        self.emit("chancellor_nominated", {
            "president_seat": self.state.president_index,
            "chancellor_seat": chancellor_seat
        })

        return ActionResult(True, f"Player {chancellor_seat} nominated as chancellor")

    # ============ ELECTION PHASE ============

    def cast_vote(self, player_seat: int, vote: VoteChoice) -> ActionResult:
        """A player casts their vote."""
        if self.state.phase != GamePhase.ELECTION:
            return ActionResult(False, f"Wrong phase: {self.state.phase.value}")

        player = self.state.get_player(player_seat)
        if player.is_dead:
            return ActionResult(False, "Dead players cannot vote")

        if player_seat in self.state.votes:
            return ActionResult(False, "Already voted")

        self.state.votes[player_seat] = vote

        self.emit("vote_cast", {
            "player_seat": player_seat,
            "total_votes": len(self.state.votes)
        })

        # Check if all living players have voted
        living_count = len(self.state.get_living_players())
        if len(self.state.votes) >= living_count:
            return self._resolve_election()

        return ActionResult(True, "Vote recorded")

    def _resolve_election(self) -> ActionResult:
        """Resolve the election after all votes are cast."""
        ja_votes = sum(1 for v in self.state.votes.values() if v == VoteChoice.JA)
        nein_votes = sum(1 for v in self.state.votes.values() if v == VoteChoice.NEIN)
        passed = ja_votes > nein_votes

        self.emit("election_result", {
            "passed": passed,
            "ja_votes": ja_votes,
            "nein_votes": nein_votes,
            "votes": {seat: v.value for seat, v in self.state.votes.items()}
        })

        if passed:
            return self._election_passed()
        else:
            return self._election_failed()

    def _election_passed(self) -> ActionResult:
        """Handle a passed election."""
        # Check Hitler win condition
        if (self.state.board.fascist_policies >= 3 and
            self.state.get_player(self.state.chancellor_candidate_index).is_hitler):
            return self._end_game(Team.FASCIST, WinCondition.HITLER_CHANCELLOR)

        # Update government
        self.state.previous_president_index = self.state.president_index
        self.state.previous_chancellor_index = self.state.chancellor_candidate_index

        # Reset election tracker
        self.state.board.reset_election_tracker()

        # Draw policies
        self.state.current_policies = self.state.policy_deck.draw(3)
        self.state.phase = GamePhase.LEGISLATIVE_PRESIDENT

        self.emit("legislative_session_start", {
            "president_seat": self.state.president_index,
            "chancellor_seat": self.state.chancellor_candidate_index
        })

        return ActionResult(True, "Election passed, legislative session begins")

    def _election_failed(self) -> ActionResult:
        """Handle a failed election."""
        chaos = self.state.board.advance_election_tracker()

        if chaos:
            return self._chaos_policy()

        # Move to next president
        self.state.advance_president()
        self.state.chancellor_candidate_index = None
        self.state.phase = GamePhase.NOMINATION
        self.state.turn_number += 1

        self.emit("election_failed", {
            "election_tracker": self.state.board.election_tracker,
            "next_president": self.state.president_index
        })

        return ActionResult(True, "Election failed")

    def _chaos_policy(self) -> ActionResult:
        """Enact top policy due to 3 failed elections."""
        self.state.board.reset_election_tracker()

        # Draw and enact top policy
        policies = self.state.policy_deck.draw(1)
        policy = policies[0]

        self.emit("chaos_policy", {"policy": policy.value})

        return self._enact_policy(policy, is_chaos=True)

    # ============ LEGISLATIVE PHASE ============

    def president_discard(self, discard_index: int) -> ActionResult:
        """President discards one of three policies."""
        if self.state.phase != GamePhase.LEGISLATIVE_PRESIDENT:
            return ActionResult(False, f"Wrong phase: {self.state.phase.value}")

        if not 0 <= discard_index < 3:
            return ActionResult(False, "Invalid discard index (must be 0, 1, or 2)")

        if len(self.state.current_policies) != 3:
            return ActionResult(False, "No policies to discard")

        # Discard the selected policy
        discarded = self.state.current_policies.pop(discard_index)
        self.state.policy_deck.discard(discarded)

        # Pass remaining 2 to chancellor
        self.state.policies_for_chancellor = self.state.current_policies
        self.state.current_policies = []
        self.state.phase = GamePhase.LEGISLATIVE_CHANCELLOR

        self.emit("president_discarded", {
            "discarded": discarded.value
        })

        return ActionResult(True, "Policy discarded, chancellor's turn")

    def chancellor_enact(self, enact_index: int) -> ActionResult:
        """Chancellor enacts one of two policies."""
        if self.state.phase != GamePhase.LEGISLATIVE_CHANCELLOR:
            return ActionResult(False, f"Wrong phase: {self.state.phase.value}")

        if not 0 <= enact_index < 2:
            return ActionResult(False, "Invalid enact index (must be 0 or 1)")

        if len(self.state.policies_for_chancellor) != 2:
            return ActionResult(False, "No policies to enact")

        # Enact the selected policy
        enacted = self.state.policies_for_chancellor[enact_index]
        discarded = self.state.policies_for_chancellor[1 - enact_index]
        self.state.policy_deck.discard(discarded)
        self.state.policies_for_chancellor = []

        return self._enact_policy(enacted)

    def propose_veto(self) -> ActionResult:
        """Chancellor proposes to veto the current agenda."""
        if self.state.phase != GamePhase.LEGISLATIVE_CHANCELLOR:
            return ActionResult(False, f"Wrong phase: {self.state.phase.value}")

        if not self.state.board.veto_unlocked:
            return ActionResult(False, "Veto power is not yet unlocked")

        self.state.veto_proposed = True
        self.emit("veto_proposed", {"chancellor_seat": self.state.chancellor_candidate_index})

        return ActionResult(True, "Veto proposed, waiting for president's decision")

    def president_veto_response(self, approve: bool) -> ActionResult:
        """President responds to veto proposal."""
        if not self.state.veto_proposed:
            return ActionResult(False, "No veto has been proposed")

        if approve:
            # Discard both policies
            for policy in self.state.policies_for_chancellor:
                self.state.policy_deck.discard(policy)
            self.state.policies_for_chancellor = []
            self.state.veto_proposed = False

            # Advance election tracker
            chaos = self.state.board.advance_election_tracker()

            self.emit("veto_approved", {
                "election_tracker": self.state.board.election_tracker
            })

            if chaos:
                return self._chaos_policy()

            # Move to next round
            return self._next_round()
        else:
            self.state.veto_proposed = False
            self.emit("veto_rejected", {})
            return ActionResult(True, "Veto rejected, chancellor must enact a policy")

    def _enact_policy(self, policy: Policy, is_chaos: bool = False) -> ActionResult:
        """Enact a policy and handle consequences."""
        self.state.board.enact_policy(policy)

        self.emit("policy_enacted", {
            "policy": policy.value,
            "liberal_count": self.state.board.liberal_policies,
            "fascist_count": self.state.board.fascist_policies,
            "is_chaos": is_chaos
        })

        # Check win conditions
        win = self.state.check_win_condition()
        if win:
            return self._end_game(win[0], win[1])

        # Check for executive action (only if not chaos and fascist policy)
        if not is_chaos and policy == Policy.FASCIST:
            action = self.state.get_executive_action()
            if action != ExecutiveAction.NONE:
                self.state.pending_executive_action = action
                self.state.phase = GamePhase.EXECUTIVE_ACTION
                self.emit("executive_action_required", {
                    "action": action.value,
                    "president_seat": self.state.president_index
                })
                return ActionResult(True, f"Executive action required: {action.value}")

        return self._next_round()

    def _next_round(self) -> ActionResult:
        """Move to the next round."""
        self.state.advance_president()
        self.state.chancellor_candidate_index = None
        self.state.phase = GamePhase.NOMINATION
        self.state.round_number += 1
        self.state.turn_number += 1
        self.state.discussion_messages = []

        self.emit("new_round", {
            "round_number": self.state.round_number,
            "president_seat": self.state.president_index
        })

        return ActionResult(True, f"Round {self.state.round_number} begins")

    # ============ EXECUTIVE ACTIONS ============

    def investigate_player(self, target_seat: int) -> ActionResult:
        """President investigates a player's party membership."""
        if self.state.pending_executive_action != ExecutiveAction.INVESTIGATE_LOYALTY:
            return ActionResult(False, "Not the right executive action")

        target = self.state.get_player(target_seat)
        if target.is_dead:
            return ActionResult(False, "Cannot investigate dead player")
        if target.was_investigated:
            return ActionResult(False, "Player was already investigated")
        if target_seat == self.state.president_index:
            return ActionResult(False, "Cannot investigate yourself")

        target.was_investigated = True

        # Return party membership (not exact role!)
        party = target.team.value

        self.emit("player_investigated", {
            "investigator": self.state.president_index,
            "target": target_seat,
            "party": party
        })

        self.state.pending_executive_action = ExecutiveAction.NONE
        return self._next_round()

    def call_special_election(self, target_seat: int) -> ActionResult:
        """President calls a special election."""
        if self.state.pending_executive_action != ExecutiveAction.SPECIAL_ELECTION:
            return ActionResult(False, "Not the right executive action")

        target = self.state.get_player(target_seat)
        if target.is_dead:
            return ActionResult(False, "Cannot elect dead player")
        if target_seat == self.state.president_index:
            return ActionResult(False, "Cannot elect yourself")

        # Remember where to return after special election
        self.state.special_election_president = (self.state.president_index + 1) % self.state.player_count
        while self.state.players[self.state.special_election_president].is_dead:
            self.state.special_election_president = (self.state.special_election_president + 1) % self.state.player_count

        # Set new president
        self.state.president_index = target_seat
        self.state.chancellor_candidate_index = None
        self.state.phase = GamePhase.NOMINATION
        self.state.pending_executive_action = ExecutiveAction.NONE

        self.emit("special_election", {
            "new_president": target_seat
        })

        return ActionResult(True, f"Special election called, player {target_seat} is now president")

    def peek_policies(self) -> ActionResult:
        """President peeks at the top 3 policies."""
        if self.state.pending_executive_action != ExecutiveAction.POLICY_PEEK:
            return ActionResult(False, "Not the right executive action")

        # Peek at top 3 without removing
        top_policies = self.state.policy_deck.draw_pile[:3]

        self.emit("policies_peeked", {
            "president_seat": self.state.president_index,
            "policies": [p.value for p in top_policies]
        })

        self.state.pending_executive_action = ExecutiveAction.NONE
        return self._next_round()

    def execute_player(self, target_seat: int) -> ActionResult:
        """President executes a player."""
        if self.state.pending_executive_action != ExecutiveAction.EXECUTION:
            return ActionResult(False, "Not the right executive action")

        target = self.state.get_player(target_seat)
        if target.is_dead:
            return ActionResult(False, "Player is already dead")
        if target_seat == self.state.president_index:
            return ActionResult(False, "Cannot execute yourself")

        target.is_dead = True

        self.emit("player_executed", {
            "executor": self.state.president_index,
            "target": target_seat,
            "was_hitler": target.is_hitler
        })

        # Check if Hitler was killed
        if target.is_hitler:
            return self._end_game(Team.LIBERAL, WinCondition.HITLER_KILLED)

        self.state.pending_executive_action = ExecutiveAction.NONE
        return self._next_round()

    # ============ DISCUSSION ============

    def add_message(self, player_seat: int, content: str) -> ActionResult:
        """Add a discussion message from a player."""
        player = self.state.get_player(player_seat)
        if player.is_dead:
            return ActionResult(False, "Dead players cannot speak")

        # Count messages from this player
        player_messages = sum(1 for m in self.state.discussion_messages if m.player_seat == player_seat)
        if player_messages >= self.state.max_messages_per_player:
            return ActionResult(False, f"Maximum messages ({self.state.max_messages_per_player}) reached")

        message = Message(
            player_seat=player_seat,
            player_name=player.name,
            content=content,
            timestamp=time.time()
        )
        self.state.discussion_messages.append(message)

        self.emit("message", {
            "player_seat": player_seat,
            "player_name": player.name,
            "content": content
        })

        return ActionResult(True, "Message added")

    # ============ GAME END ============

    def _end_game(self, winner: Team, condition: WinCondition) -> ActionResult:
        """End the game with a winner."""
        self.state.winner = winner
        self.state.win_condition = condition
        self.state.phase = GamePhase.GAME_OVER

        self.emit("game_over", {
            "winner": winner.value,
            "condition": condition.value,
            "players": [
                {
                    "seat": p.seat,
                    "name": p.name,
                    "role": p.role.value,
                    "team": p.team.value,
                    "is_dead": p.is_dead
                }
                for p in self.state.players
            ]
        })

        return ActionResult(True, f"Game over! {winner.value} wins by {condition.value}")

    def get_available_actions(self, player_seat: int) -> list[str]:
        """Get the actions available to a player in the current state."""
        player = self.state.get_player(player_seat)
        if player.is_dead:
            return []

        actions = []

        # Discussion is always available when alive
        player_messages = sum(1 for m in self.state.discussion_messages if m.player_seat == player_seat)
        if player_messages < self.state.max_messages_per_player:
            actions.append("discuss")

        if self.state.phase == GamePhase.NOMINATION:
            if player_seat == self.state.president_index:
                actions.append("nominate_chancellor")

        elif self.state.phase == GamePhase.ELECTION:
            if player_seat not in self.state.votes:
                actions.append("vote")

        elif self.state.phase == GamePhase.LEGISLATIVE_PRESIDENT:
            if player_seat == self.state.president_index:
                actions.append("discard_policy")

        elif self.state.phase == GamePhase.LEGISLATIVE_CHANCELLOR:
            if player_seat == self.state.chancellor_candidate_index:
                if self.state.veto_proposed:
                    pass  # Wait for president
                else:
                    actions.append("enact_policy")
                    if self.state.board.veto_unlocked:
                        actions.append("propose_veto")

            if player_seat == self.state.president_index and self.state.veto_proposed:
                actions.append("respond_to_veto")

        elif self.state.phase == GamePhase.EXECUTIVE_ACTION:
            if player_seat == self.state.president_index:
                action = self.state.pending_executive_action
                if action == ExecutiveAction.INVESTIGATE_LOYALTY:
                    actions.append("investigate_player")
                elif action == ExecutiveAction.SPECIAL_ELECTION:
                    actions.append("call_special_election")
                elif action == ExecutiveAction.POLICY_PEEK:
                    actions.append("peek_policies")
                elif action == ExecutiveAction.EXECUTION:
                    actions.append("execute_player")

        return actions
