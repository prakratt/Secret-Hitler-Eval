"""AI Player implementation."""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .openrouter import OpenRouterClient, ModelConfig
from .prompts import build_system_prompt, build_game_state_prompt
from ..tools.definitions import get_tool_definitions


@dataclass
class AIPlayer:
    """Represents an AI player in the game."""
    seat: int
    model: ModelConfig
    client: OpenRouterClient

    # Role info (set after game starts)
    role: str = ""
    team: str = ""
    known_fascists: List[int] = field(default_factory=list)
    known_hitler: Optional[int] = None

    # Conversation history
    messages: List[Dict[str, Any]] = field(default_factory=list)

    def set_role_info(
        self,
        role: str,
        team: str,
        known_fascists: List[int],
        known_hitler: Optional[int]
    ):
        """Set the player's role information after game starts."""
        self.role = role
        self.team = team
        self.known_fascists = known_fascists
        self.known_hitler = known_hitler

        # Build and set system prompt
        system_prompt = build_system_prompt(
            player_name=self.model.name,
            seat=self.seat,
            role=role,
            team=team,
            known_fascists=known_fascists,
            known_hitler=known_hitler
        )

        self.messages = [{"role": "system", "content": system_prompt}]

    def get_action(
        self,
        game_state: Dict[str, Any],
        available_actions: List[str],
        temperature: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """Get an action from the AI player."""
        if not available_actions:
            return None

        # Build state prompt
        state_prompt = build_game_state_prompt(game_state, self.seat)

        # Add to conversation
        self.messages.append({"role": "user", "content": state_prompt})

        # Get available tools
        tools = get_tool_definitions(available_actions)

        if not tools:
            return None

        try:
            # Request action from model (with retry for incomplete responses)
            max_retries = 2
            for attempt in range(max_retries + 1):
                result = self.client.get_tool_call(
                    model=self.model.id,
                    messages=self.messages,
                    tools=tools,
                    temperature=temperature
                )

                if result:
                    # Validate that required parameters are present
                    action_name = result.get("name")
                    arguments = result.get("arguments", {})
                    
                    # Check if this action requires specific parameters
                    if action_name == "discard_policy" and "discard_index" not in arguments:
                        if attempt < max_retries:
                            # Retry with a clarifying message
                            self.messages.append({
                                "role": "assistant",
                                "content": f"[Attempted to call {action_name} but missing required parameter 'discard_index']"
                            })
                            self.messages.append({
                                "role": "user",
                                "content": "ERROR: You called discard_policy but did not provide the required 'discard_index' parameter (must be 0, 1, or 2). Please call the function again with the discard_index parameter included."
                            })
                            continue
                        else:
                            print(f"Warning: {self.model.name} failed to provide discard_index after {max_retries + 1} attempts")
                            return None
                    elif action_name == "enact_policy" and "enact_index" not in arguments:
                        if attempt < max_retries:
                            self.messages.append({
                                "role": "assistant",
                                "content": f"[Attempted to call {action_name} but missing required parameter 'enact_index']"
                            })
                            self.messages.append({
                                "role": "user",
                                "content": "ERROR: You called enact_policy but did not provide the required 'enact_index' parameter (must be 0 or 1). Please call the function again with the enact_index parameter included."
                            })
                            continue
                        else:
                            print(f"Warning: {self.model.name} failed to provide enact_index after {max_retries + 1} attempts")
                            return None
                    
                    # Valid result - log and return
                    self.messages.append({
                        "role": "assistant",
                        "content": f"[Took action: {result['name']}]"
                    })
                    return result
                else:
                    # No tool call returned
                    break

            return result

        except Exception as e:
            print(f"Error getting action from {self.model.name}: {e}")
            return None

    def add_event(self, event_description: str):
        """Add a game event to the player's conversation history."""
        self.messages.append({
            "role": "user",
            "content": f"[Game Event] {event_description}"
        })

    def add_private_info(self, info: str):
        """Add private information visible only to this player."""
        self.messages.append({
            "role": "user",
            "content": f"[Private Info] {info}"
        })

    @property
    def name(self) -> str:
        return self.model.name
