/**
 * Parses game log JSON files from the backend into visualization state
 */

export function parseGameLog(logData) {
  const events = logData.events || []
  const states = []

  // Initial state
  let currentState = {
    round: 1,
    phase: 'setup',
    liberalPolicies: 0,
    fascistPolicies: 0,
    electionTracker: 0,
    drawPileSize: 17,
    players: [],
    messages: [],
    events: [],
    winner: null,
    winCondition: null,
    presidentSeat: null,
    chancellorSeat: null,
  }

  // Process each event and build state snapshots
  for (const event of events) {
    const { type, data } = event

    // Clone current state
    currentState = JSON.parse(JSON.stringify(currentState))
    currentState.events.push({ type, data })

    switch (type) {
      case 'game_started':
        currentState.players = data.players.map(p => ({
          seat: p.seat,
          name: p.name,
          role: 'unknown',
          team: 'unknown',
          isDead: false,
          isPresident: false,
          isChancellor: false,
        }))
        currentState.presidentSeat = data.starting_president
        if (currentState.players[data.starting_president]) {
          currentState.players[data.starting_president].isPresident = true
        }
        break

      case 'game_setup_complete':
        // Update with model info if available
        if (data.players) {
          data.players.forEach(p => {
            if (currentState.players[p.seat]) {
              currentState.players[p.seat].model = p.model
              currentState.players[p.seat].modelId = p.model_id
            }
          })
        }
        break

      case 'round_update':
        currentState.round = data.round
        currentState.phase = data.phase
        break

      case 'chancellor_nominated':
      case 'nomination_action':
        currentState.phase = 'election'
        const chancSeat = data.chancellor_seat ?? data.chancellor
        currentState.chancellorSeat = chancSeat
        // Reset previous government markers
        currentState.players.forEach(p => {
          p.isChancellor = p.seat === chancSeat
        })
        break

      case 'vote_cast':
        // Individual vote - could track these
        break

      case 'election_result':
        if (data.passed) {
          currentState.phase = 'legislative_president'
          currentState.electionTracker = 0
        } else {
          currentState.electionTracker = Math.min(currentState.electionTracker + 1, 3)
          currentState.players.forEach(p => p.isChancellor = false)
        }
        break

      case 'legislative_session_start':
        currentState.phase = 'legislative_president'
        break

      case 'president_discarded':
      case 'president_discard_action':
        currentState.phase = 'legislative_chancellor'
        currentState.drawPileSize = Math.max(0, currentState.drawPileSize - 3)
        break

      case 'policy_enacted':
        if (data.policy === 'liberal') {
          currentState.liberalPolicies++
        } else {
          currentState.fascistPolicies++
        }
        break

      case 'new_round':
        currentState.round = data.round_number
        currentState.phase = 'nomination'
        // Update president
        currentState.players.forEach(p => {
          p.isPresident = p.seat === data.president_seat
          p.isChancellor = false
        })
        currentState.presidentSeat = data.president_seat
        currentState.chancellorSeat = null
        currentState.messages = [] // Clear messages for new round
        break

      case 'discussion_message':
        currentState.messages.push({
          seat: data.seat,
          name: data.player,
          content: data.message,
        })
        break

      case 'player_investigated':
      case 'investigate_action':
        currentState.phase = 'executive_action'
        break

      case 'special_election':
      case 'special_election_action':
        currentState.players.forEach(p => {
          p.isPresident = p.seat === data.new_president || p.seat === data.target
        })
        break

      case 'player_executed':
      case 'execute_action':
        const targetSeat = data.target
        if (currentState.players[targetSeat]) {
          currentState.players[targetSeat].isDead = true
        }
        break

      case 'game_over':
        currentState.phase = 'game_over'
        currentState.winner = data.winner
        currentState.winCondition = data.condition
        // Reveal all roles
        if (data.players) {
          data.players.forEach(p => {
            if (currentState.players[p.seat]) {
              currentState.players[p.seat].role = p.role
              currentState.players[p.seat].team = p.team
              currentState.players[p.seat].isDead = p.is_dead
            }
          })
        }
        break

      default:
        // Unknown event type, just record it
        break
    }

    // Save state snapshot
    states.push(JSON.parse(JSON.stringify(currentState)))
  }

  return {
    states,
    totalEvents: events.length,
    duration: logData.duration || 0,
    startTime: logData.start_time,
    endTime: logData.end_time,
  }
}

/**
 * Get role information from game_over event
 */
export function extractRoles(logData) {
  const gameOverEvent = logData.events?.find(e => e.type === 'game_over')
  if (gameOverEvent?.data?.players) {
    return gameOverEvent.data.players.reduce((acc, p) => {
      acc[p.seat] = { role: p.role, team: p.team }
      return acc
    }, {})
  }
  return {}
}

/**
 * Format duration for display
 */
export function formatDuration(seconds) {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
