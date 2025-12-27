"""Game state management for Secret Hitler."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import random

from .types import (
    Team, Role, GamePhase, ExecutiveAction, Policy, VoteChoice, WinCondition,
    Player, Government, PolicyDeck, GameBoard,
    PLAYER_CONFIGS, get_executive_power
)


@dataclass
class Message:
    """A chat message from a player."""
    player_seat: int
    player_name: str
    content: str
    timestamp: float = 0.0


@dataclass
class GameEvent:
    """Records a game event for history."""
    event_type: str
    data: dict
    round_number: int


@dataclass
class GameState:
    """Complete state of a Secret Hitler game."""
    # Game setup
    player_count: int
    players: list[Player] = field(default_factory=list)
    model_names: list[str] = field(default_factory=list)

    # Game progression
    phase: GamePhase = GamePhase.SETUP
    round_number: int = 0
    turn_number: int = 0

    # Current government
    president_index: int = 0
    chancellor_candidate_index: Optional[int] = None
    previous_president_index: Optional[int] = None
    previous_chancellor_index: Optional[int] = None

    # Voting
    votes: dict[int, VoteChoice] = field(default_factory=dict)

    # Board state
    board: GameBoard = field(default_factory=GameBoard)
    policy_deck: PolicyDeck = field(default_factory=PolicyDeck)

    # Legislative session
    current_policies: list[Policy] = field(default_factory=list)
    policies_for_chancellor: list[Policy] = field(default_factory=list)
    veto_proposed: bool = False

    # Executive action state
    pending_executive_action: ExecutiveAction = ExecutiveAction.NONE
    special_election_president: Optional[int] = None

    # Discussion
    discussion_messages: list[Message] = field(default_factory=list)
    max_messages_per_player: int = 5

    # Win state
    winner: Optional[Team] = None
    win_condition: Optional[WinCondition] = None

    # Event log
    events: list[GameEvent] = field(default_factory=list)

    def initialize_game(self, model_names: list[str]):
        """Set up a new game with the given AI models as players."""
        self.player_count = len(model_names)
        self.model_names = model_names

        if self.player_count < 5 or self.player_count > 10:
            raise ValueError(f"Player count must be 5-10, got {self.player_count}")

        config = PLAYER_CONFIGS[self.player_count]

        # Create role list
        roles = (
            [Role.LIBERAL] * config["liberals"] +
            [Role.FASCIST] * config["fascists"] +
            [Role.HITLER]
        )
        random.shuffle(roles)

        # Assign players to seats
        self.players = []
        for seat, (name, role) in enumerate(zip(model_names, roles)):
            team = Team.LIBERAL if role == Role.LIBERAL else Team.FASCIST
            self.players.append(Player(
                seat=seat,
                name=name,
                role=role,
                team=team
            ))

        # Initialize deck
        self.policy_deck.initialize()

        # Choose random starting president
        self.president_index = random.randint(0, self.player_count - 1)

        # Set phase
        self.phase = GamePhase.NOMINATION
        self.round_number = 1

        self._log_event("game_started", {
            "player_count": self.player_count,
            "starting_president": self.president_index
        })

    def get_player(self, seat: int) -> Player:
        """Get player by seat number."""
        return self.players[seat]

    def get_living_players(self) -> list[Player]:
        """Get all living players."""
        return [p for p in self.players if not p.is_dead]

    def get_eligible_chancellors(self) -> list[int]:
        """Get seats of players eligible to be chancellor."""
        ineligible = set()

        # Dead players can't be chancellor
        for p in self.players:
            if p.is_dead:
                ineligible.add(p.seat)

        # Current president can't be chancellor
        ineligible.add(self.president_index)

        # Previous government can't be chancellor (with exceptions)
        if self.previous_chancellor_index is not None:
            ineligible.add(self.previous_chancellor_index)

        # In games with 5 players, only previous chancellor is ineligible
        # In larger games, previous president is also ineligible
        if self.player_count > 5 and self.previous_president_index is not None:
            ineligible.add(self.previous_president_index)

        return [p.seat for p in self.players if p.seat not in ineligible]

    def advance_president(self):
        """Move to the next president in order."""
        if self.special_election_president is not None:
            # After special election, return to normal order
            next_idx = self.special_election_president
            self.special_election_president = None
        else:
            next_idx = (self.president_index + 1) % self.player_count

        # Skip dead players
        while self.players[next_idx].is_dead:
            next_idx = (next_idx + 1) % self.player_count

        self.president_index = next_idx

    def get_fascist_knowledge(self, player_seat: int) -> dict:
        """Get what a player knows about fascists based on their role."""
        player = self.get_player(player_seat)
        knowledge = {
            "your_role": player.role.value,
            "your_team": player.team.value,
            "known_fascists": [],
            "known_hitler": None
        }

        if player.role == Role.LIBERAL:
            return knowledge

        config = PLAYER_CONFIGS[self.player_count]
        hitler_knows = config["hitler_knows_fascists"]

        if player.role == Role.HITLER:
            if hitler_knows:
                # Hitler knows fascists in 5-6 player games
                for p in self.players:
                    if p.role == Role.FASCIST:
                        knowledge["known_fascists"].append(p.seat)
        else:
            # Regular fascists know Hitler and each other
            for p in self.players:
                if p.role == Role.HITLER:
                    knowledge["known_hitler"] = p.seat
                elif p.role == Role.FASCIST and p.seat != player_seat:
                    knowledge["known_fascists"].append(p.seat)

        return knowledge

    def check_win_condition(self) -> Optional[tuple[Team, WinCondition]]:
        """Check if the game has been won."""
        # Liberal win: 5 liberal policies
        if self.board.liberal_policies >= 5:
            return (Team.LIBERAL, WinCondition.LIBERAL_POLICIES)

        # Fascist win: 6 fascist policies
        if self.board.fascist_policies >= 6:
            return (Team.FASCIST, WinCondition.FASCIST_POLICIES)

        # Hitler killed (checked elsewhere when execution happens)
        # Hitler elected (checked elsewhere when election passes)

        return None

    def get_executive_action(self) -> ExecutiveAction:
        """Get the executive action for the current fascist policy count."""
        return get_executive_power(self.player_count, self.board.fascist_policies)

    def _log_event(self, event_type: str, data: dict):
        """Log a game event."""
        self.events.append(GameEvent(
            event_type=event_type,
            data=data,
            round_number=self.round_number
        ))

    def get_public_state(self) -> dict:
        """Get state visible to all players."""
        return {
            "phase": self.phase.value,
            "round_number": self.round_number,
            "turn_number": self.turn_number,
            "president_seat": self.president_index,
            "chancellor_candidate_seat": self.chancellor_candidate_index,
            "previous_president_seat": self.previous_president_index,
            "previous_chancellor_seat": self.previous_chancellor_index,
            "liberal_policies": self.board.liberal_policies,
            "fascist_policies": self.board.fascist_policies,
            "election_tracker": self.board.election_tracker,
            "veto_unlocked": self.board.veto_unlocked,
            "draw_pile_size": self.policy_deck.remaining,
            "players": [
                {
                    "seat": p.seat,
                    "name": p.name,
                    "is_dead": p.is_dead,
                }
                for p in self.players
            ],
            "eligible_chancellors": self.get_eligible_chancellors(),
            "discussion": [
                {"seat": m.player_seat, "name": m.player_name, "content": m.content}
                for m in self.discussion_messages
            ]
        }

    def get_player_state(self, player_seat: int) -> dict:
        """Get state visible to a specific player (includes role info)."""
        public = self.get_public_state()
        knowledge = self.get_fascist_knowledge(player_seat)
        player = self.get_player(player_seat)

        private_info = {
            **public,
            "your_seat": player_seat,
            "your_role": player.role.value,
            "your_team": player.team.value,
            "known_fascists": knowledge["known_fascists"],
            "known_hitler": knowledge["known_hitler"],
        }

        # Add policy hand info if in legislative session
        if self.phase == GamePhase.LEGISLATIVE_PRESIDENT and player_seat == self.president_index:
            private_info["policies_in_hand"] = [p.value for p in self.current_policies]
        elif self.phase == GamePhase.LEGISLATIVE_CHANCELLOR and player_seat == self.chancellor_candidate_index:
            private_info["policies_in_hand"] = [p.value for p in self.policies_for_chancellor]

        return private_info
