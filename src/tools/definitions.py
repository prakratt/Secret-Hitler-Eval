"""Tool definitions for AI models to interact with the game."""

GAME_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "discuss",
            "description": "Send a message to all players during the discussion phase. Use this to share information, make accusations, defend yourself, strategize, or deceive other players. You have a maximum of 5 messages per discussion phase. Be strategic about what you say - your words can reveal or conceal your true role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Your message to share with all players. This should be your in-character statement as a player in the game. Keep it concise but meaningful."
                    }
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "nominate_chancellor",
            "description": "As President, nominate another player to be your Chancellor. Only available when you are the President during the nomination phase. Choose wisely - if your ticket gets elected, you'll be working together to pass policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "player_seat": {
                        "type": "integer",
                        "description": "The seat number (0-indexed) of the player you want to nominate as Chancellor. Must be an eligible player (not in previous government, not dead)."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're choosing this player (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["player_seat"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vote",
            "description": "Vote Ja (yes) or Nein (no) on the proposed government (President + Chancellor). Vote Ja if you want this government to be elected, Nein if you want to reject it. Consider who the candidates are and what their election would mean for your team.",
            "parameters": {
                "type": "object",
                "properties": {
                    "choice": {
                        "type": "string",
                        "enum": ["ja", "nein"],
                        "description": "Your vote: 'ja' to approve the government, 'nein' to reject it."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're voting this way (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["choice"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "discard_policy",
            "description": "As President during the legislative session, you've drawn 3 policy cards. You must discard one and pass the remaining two to the Chancellor. The Chancellor will then choose which one to enact. Consider your team's goals and what options you want to give the Chancellor. IMPORTANT: You MUST provide the discard_index parameter (0, 1, or 2) indicating which card to discard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "discard_index": {
                        "type": "integer",
                        "enum": [0, 1, 2],
                        "description": "REQUIRED: The index (0, 1, or 2) of the policy card to discard. Index 0 is the first card, index 1 is the second card, index 2 is the third card. The other two will be passed to the Chancellor."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're discarding this policy (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["discard_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enact_policy",
            "description": "As Chancellor during the legislative session, you've received 2 policy cards from the President. You must choose one to enact. The enacted policy will be placed on the corresponding track (Liberal or Fascist). Consider your team's goals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enact_index": {
                        "type": "integer",
                        "enum": [0, 1],
                        "description": "The index (0 or 1) of the policy card to enact. The other will be discarded."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're enacting this policy (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["enact_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_veto",
            "description": "As Chancellor, propose to veto the current agenda (discard both policies). This is only available after 5 fascist policies have been enacted. If the President agrees, both policies are discarded and the election tracker advances. Use this strategically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're proposing a veto (for logging purposes, not shared with other players)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "respond_to_veto",
            "description": "As President, respond to the Chancellor's veto proposal. If you approve, both policies are discarded and the election tracker advances. If you reject, the Chancellor must enact one of the policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "approve": {
                        "type": "boolean",
                        "description": "True to approve the veto (discard both policies), False to reject it (Chancellor must enact a policy)."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of your decision (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["approve"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "investigate_player",
            "description": "As President after the Investigate Loyalty power is triggered, secretly look at another player's party membership card. You will learn if they are Liberal or Fascist (but not if they are Hitler specifically). You can then share or lie about this information to other players.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_seat": {
                        "type": "integer",
                        "description": "The seat number of the player you want to investigate. Cannot be yourself or a previously investigated player."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're investigating this player (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["target_seat"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_special_election",
            "description": "As President after the Special Election power is triggered, choose any other living player to be the next Presidential Candidate. The normal rotation resumes after this special election. Use this to give power to an ally or take it from an enemy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_seat": {
                        "type": "integer",
                        "description": "The seat number of the player you want to become the next President. Cannot be yourself."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're choosing this player (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["target_seat"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "peek_policies",
            "description": "As President after the Policy Peek power is triggered, look at the top 3 cards of the policy deck. You can then share or lie about this information to other players. This helps you plan for future legislative sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "Any notes about what you plan to do with this information (for logging purposes)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_player",
            "description": "As President after the Execution power is triggered, choose a player to execute. That player is removed from the game and cannot speak, vote, or hold office. If you execute Hitler, Liberals win immediately! Choose carefully - you can't undo this.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_seat": {
                        "type": "integer",
                        "description": "The seat number of the player you want to execute. Cannot be yourself."
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of why you're executing this player (for logging purposes, not shared with other players)."
                    }
                },
                "required": ["target_seat"]
            }
        }
    }
]


def get_tool_definitions(available_actions: list[str]) -> list[dict]:
    """Get tool definitions for only the currently available actions."""
    action_to_tool = {
        "discuss": "discuss",
        "nominate_chancellor": "nominate_chancellor",
        "vote": "vote",
        "discard_policy": "discard_policy",
        "enact_policy": "enact_policy",
        "propose_veto": "propose_veto",
        "respond_to_veto": "respond_to_veto",
        "investigate_player": "investigate_player",
        "call_special_election": "call_special_election",
        "peek_policies": "peek_policies",
        "execute_player": "execute_player",
    }

    available_tools = set()
    for action in available_actions:
        if action in action_to_tool:
            available_tools.add(action_to_tool[action])

    return [
        tool for tool in GAME_TOOLS
        if tool["function"]["name"] in available_tools
    ]
