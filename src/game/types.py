"""Core types and enums for Secret Hitler game."""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
import random


class Team(Enum):
    LIBERAL = "liberal"
    FASCIST = "fascist"


class Role(Enum):
    LIBERAL = "liberal"
    FASCIST = "fascist"
    HITLER = "hitler"


class GamePhase(Enum):
    SETUP = "setup"
    NOMINATION = "nomination"
    ELECTION = "election"
    LEGISLATIVE_PRESIDENT = "legislative_president"
    LEGISLATIVE_CHANCELLOR = "legislative_chancellor"
    EXECUTIVE_ACTION = "executive_action"
    GAME_OVER = "game_over"


class ExecutiveAction(Enum):
    NONE = "none"
    INVESTIGATE_LOYALTY = "investigate_loyalty"
    SPECIAL_ELECTION = "special_election"
    POLICY_PEEK = "policy_peek"
    EXECUTION = "execution"


class Policy(Enum):
    LIBERAL = "liberal"
    FASCIST = "fascist"


class VoteChoice(Enum):
    JA = "ja"
    NEIN = "nein"


class WinCondition(Enum):
    LIBERAL_POLICIES = "five_liberal_policies"
    HITLER_KILLED = "hitler_executed"
    FASCIST_POLICIES = "six_fascist_policies"
    HITLER_CHANCELLOR = "hitler_elected_chancellor"


@dataclass
class Player:
    """Represents a player in the game."""
    seat: int
    name: str  # Model name/identifier
    role: Role
    team: Team
    is_dead: bool = False
    was_investigated: bool = False

    @property
    def is_hitler(self) -> bool:
        return self.role == Role.HITLER

    @property
    def is_fascist(self) -> bool:
        return self.team == Team.FASCIST

    @property
    def is_liberal(self) -> bool:
        return self.team == Team.LIBERAL


@dataclass
class Government:
    """Represents a government (president + chancellor)."""
    president_seat: int
    chancellor_seat: int


@dataclass
class PolicyDeck:
    """Manages the policy deck."""
    draw_pile: list[Policy] = field(default_factory=list)
    discard_pile: list[Policy] = field(default_factory=list)

    def initialize(self):
        """Initialize with 6 liberal and 11 fascist policies."""
        self.draw_pile = (
            [Policy.LIBERAL] * 6 +
            [Policy.FASCIST] * 11
        )
        random.shuffle(self.draw_pile)
        self.discard_pile = []

    def draw(self, count: int = 3) -> list[Policy]:
        """Draw policies from the deck."""
        if len(self.draw_pile) < count:
            self._reshuffle()

        drawn = self.draw_pile[:count]
        self.draw_pile = self.draw_pile[count:]
        return drawn

    def discard(self, policy: Policy):
        """Discard a policy."""
        self.discard_pile.append(policy)

    def _reshuffle(self):
        """Reshuffle discard pile into draw pile."""
        self.draw_pile.extend(self.discard_pile)
        self.discard_pile = []
        random.shuffle(self.draw_pile)

    @property
    def remaining(self) -> int:
        return len(self.draw_pile)


@dataclass
class GameBoard:
    """Tracks enacted policies and game state."""
    liberal_policies: int = 0
    fascist_policies: int = 0
    election_tracker: int = 0
    veto_unlocked: bool = False

    def enact_policy(self, policy: Policy) -> Optional[ExecutiveAction]:
        """Enact a policy and return any executive action triggered."""
        if policy == Policy.LIBERAL:
            self.liberal_policies += 1
            return None
        else:
            self.fascist_policies += 1
            if self.fascist_policies >= 5:
                self.veto_unlocked = True
            return None  # Executive action determined by game state

    def reset_election_tracker(self):
        self.election_tracker = 0

    def advance_election_tracker(self) -> bool:
        """Advance tracker, return True if chaos (3 failed elections)."""
        self.election_tracker += 1
        return self.election_tracker >= 3


# Player count configurations
PLAYER_CONFIGS = {
    5: {"liberals": 3, "fascists": 1, "hitler_knows_fascists": True},
    6: {"liberals": 4, "fascists": 1, "hitler_knows_fascists": True},
    7: {"liberals": 4, "fascists": 2, "hitler_knows_fascists": False},
    8: {"liberals": 5, "fascists": 2, "hitler_knows_fascists": False},
    9: {"liberals": 5, "fascists": 3, "hitler_knows_fascists": False},
    10: {"liberals": 6, "fascists": 3, "hitler_knows_fascists": False},
}

# Executive powers by player count and fascist policy number
# Key: (min_players, max_players), Value: list of powers for policies 1-5
EXECUTIVE_POWERS = {
    (5, 6): [
        ExecutiveAction.NONE,           # 1st fascist policy
        ExecutiveAction.NONE,           # 2nd fascist policy
        ExecutiveAction.POLICY_PEEK,    # 3rd fascist policy
        ExecutiveAction.EXECUTION,      # 4th fascist policy
        ExecutiveAction.EXECUTION,      # 5th fascist policy
    ],
    (7, 8): [
        ExecutiveAction.NONE,                    # 1st fascist policy
        ExecutiveAction.INVESTIGATE_LOYALTY,    # 2nd fascist policy
        ExecutiveAction.SPECIAL_ELECTION,       # 3rd fascist policy
        ExecutiveAction.EXECUTION,              # 4th fascist policy
        ExecutiveAction.EXECUTION,              # 5th fascist policy
    ],
    (9, 10): [
        ExecutiveAction.INVESTIGATE_LOYALTY,    # 1st fascist policy
        ExecutiveAction.INVESTIGATE_LOYALTY,    # 2nd fascist policy
        ExecutiveAction.SPECIAL_ELECTION,       # 3rd fascist policy
        ExecutiveAction.EXECUTION,              # 4th fascist policy
        ExecutiveAction.EXECUTION,              # 5th fascist policy
    ],
}


def get_executive_power(player_count: int, fascist_policy_count: int) -> ExecutiveAction:
    """Get the executive power for a given game state."""
    if fascist_policy_count == 0 or fascist_policy_count > 5:
        return ExecutiveAction.NONE

    for (min_p, max_p), powers in EXECUTIVE_POWERS.items():
        if min_p <= player_count <= max_p:
            return powers[fascist_policy_count - 1]

    return ExecutiveAction.NONE
