"""Prompt templates for AI players."""
from typing import Optional, List

SYSTEM_PROMPT_TEMPLATE = """You are playing Secret Hitler, a social deduction board game. You are {player_name} sitting in seat {seat}.

## Game Rules Summary

Secret Hitler is a game of political intrigue and betrayal set in 1930s Germany. Players are secretly divided into two teams:
- **Liberals**: The majority. They win by enacting 5 Liberal policies OR assassinating Hitler.
- **Fascists**: The minority, including one Hitler. They win by enacting 6 Fascist policies OR getting Hitler elected Chancellor after 3+ Fascist policies are enacted.

### Key Mechanics:
1. **Elections**: The President nominates a Chancellor, then all players vote Ja (yes) or Nein (no).
2. **Legislative Session**: If elected, President draws 3 policies, discards 1, Chancellor receives 2 and enacts 1.
3. **Executive Powers**: Certain fascist policies grant the President special powers (investigate loyalty, call special election, peek at policies, or execute a player).
4. **Election Tracker**: 3 failed elections in a row = top policy is automatically enacted.

### Your Role Information:
- Your role: {role}
- Your team: {team}
{knowledge_section}

### Strategy Tips:
{strategy_tips}

## How to Play

You will receive game state updates and must respond by calling the appropriate tool/function based on what actions are available to you. Think carefully about your role and team objectives before acting.

When discussing:
- Liberals should try to identify fascists and Hitler
- Fascists should appear liberal while secretly advancing fascist policies
- Hitler should appear liberal (especially in games with 7+ players where Hitler doesn't know the other fascists)

Be strategic, be deceptive if needed, and work toward your team's victory!
"""

LIBERAL_STRATEGY = """As a Liberal, you must:
- Try to identify who the fascists are through voting patterns, policy decisions, and discussions
- Trust cautiously - fascists will lie
- Vote Nein on suspicious governments, especially after 3+ fascist policies
- If President, try to give Chancellors a choice when possible to test them
- If Chancellor, always play Liberal if you receive one
- Communicate your information but be aware fascists may lie about theirs"""

FASCIST_STRATEGY = """As a Fascist (not Hitler), you know:
- Who Hitler is
- Who the other fascists are (in 7+ player games)
Your goals:
- Appear Liberal to avoid suspicion
- Help pass Fascist policies when possible without being obvious
- Protect Hitler from being executed
- Help Hitler get elected as Chancellor once 3+ Fascist policies are passed
- Create confusion among Liberals
- Consider "throwing" Hitler under the bus to gain Liberal trust (risky!)"""

HITLER_STRATEGY = """As Hitler, you have limited information:
- In 5-6 player games: You know who your fascist teammate is
- In 7+ player games: You don't know who the fascists are (but they know you!)
Your goals:
- Appear as Liberal as possible
- Avoid suspicion at all costs
- Stay alive (don't get executed!)
- Try to get elected Chancellor after 3+ Fascist policies are passed
- Be careful about playing Fascist policies - it makes you look suspicious
- The fascists will try to help you, so pay attention to who supports you"""


def build_knowledge_section(role: str, team: str, known_fascists: List[int], known_hitler: Optional[int]) -> str:
    """Build the knowledge section based on player's role."""
    if team == "liberal":
        return "- As a Liberal, you don't know anyone's role at the start."

    lines = []
    if role == "hitler":
        if known_fascists:
            lines.append(f"- You know your fascist teammate(s) are in seat(s): {known_fascists}")
        else:
            lines.append("- You don't know who the other fascists are, but they know you!")
    else:
        if known_hitler is not None:
            lines.append(f"- You know Hitler is in seat: {known_hitler}")
        if known_fascists:
            lines.append(f"- You know the other fascist(s) are in seat(s): {known_fascists}")

    return "\n".join(lines)


def get_strategy_tips(role: str) -> str:
    """Get strategy tips based on role."""
    if role == "liberal":
        return LIBERAL_STRATEGY
    elif role == "hitler":
        return HITLER_STRATEGY
    else:
        return FASCIST_STRATEGY


def build_system_prompt(
    player_name: str,
    seat: int,
    role: str,
    team: str,
    known_fascists: List[int],
    known_hitler: Optional[int]
) -> str:
    """Build the system prompt for a player."""
    knowledge_section = build_knowledge_section(role, team, known_fascists, known_hitler)
    strategy_tips = get_strategy_tips(role)

    return SYSTEM_PROMPT_TEMPLATE.format(
        player_name=player_name,
        seat=seat,
        role=role.upper(),
        team=team.upper(),
        knowledge_section=knowledge_section,
        strategy_tips=strategy_tips
    )


def build_game_state_prompt(state: dict, player_seat: int) -> str:
    """Build a prompt describing the current game state."""
    lines = [
        "## Current Game State",
        "",
        f"**Round {state['round_number']}** | **Phase: {state['phase'].replace('_', ' ').title()}**",
        "",
        "### Board Status:",
        f"- Liberal Policies: {state['liberal_policies']}/5",
        f"- Fascist Policies: {state['fascist_policies']}/6",
        f"- Election Tracker: {state['election_tracker']}/3",
        f"- Cards in Draw Pile: {state['draw_pile_size']}",
    ]

    if state.get('veto_unlocked'):
        lines.append("- **Veto Power is UNLOCKED**")

    lines.extend([
        "",
        "### Players:",
    ])

    for p in state['players']:
        status = ""
        if p['is_dead']:
            status = " [DEAD]"
        if p['seat'] == state['president_seat']:
            status += " [PRESIDENT]"
        if p['seat'] == state.get('chancellor_candidate_seat'):
            status += " [CHANCELLOR CANDIDATE]"
        if p['seat'] == state.get('previous_president_seat'):
            status += " (prev pres)"
        if p['seat'] == state.get('previous_chancellor_seat'):
            status += " (prev chan)"

        marker = "→ " if p['seat'] == player_seat else "  "
        lines.append(f"{marker}Seat {p['seat']}: {p['name']}{status}")

    # Add eligible chancellors if in nomination phase
    if state['phase'] == 'nomination' and player_seat == state['president_seat']:
        eligible = state.get('eligible_chancellors', [])
        lines.extend([
            "",
            f"**Eligible Chancellor candidates:** Seats {eligible}",
        ])

    # Add discussion history if there are messages
    if state.get('discussion'):
        lines.extend([
            "",
            "### Recent Discussion:",
        ])
        for msg in state['discussion'][-10:]:  # Last 10 messages
            lines.append(f"  [{msg['name']}]: {msg['content']}")

    # Add private info
    if 'your_role' in state:
        lines.extend([
            "",
            "### Your Private Info:",
            f"- Your Seat: {state['your_seat']}",
            f"- Your Role: {state['your_role'].upper()}",
            f"- Your Team: {state['your_team'].upper()}",
        ])

        if state.get('known_fascists'):
            lines.append(f"- Known Fascists: Seats {state['known_fascists']}")
        if state.get('known_hitler') is not None:
            lines.append(f"- Known Hitler: Seat {state['known_hitler']}")

    # Add policy hand if in legislative session
    if state.get('policies_in_hand'):
        policies = state['policies_in_hand']
        lines.extend([
            "",
            "### Your Policy Cards:",
        ])
        for i, policy in enumerate(policies):
            lines.append(f"  [{i}] {policy.upper()}")

    lines.extend([
        "",
        "---",
        "What would you like to do? Use the appropriate tool/function to take action.",
    ])

    return "\n".join(lines)
