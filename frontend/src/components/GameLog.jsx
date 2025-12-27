import React, { useRef, useEffect } from 'react'
import { motion } from 'motion/react'

const EVENT_ICONS = {
  round_start: '🎯',
  nomination: '👆',
  election_passed: '✓',
  election_failed: '✕',
  policy_enacted: '📜',
  liberal_policy: '🔵',
  fascist_policy: '🔴',
  investigation: '🔍',
  execution: '💀',
  special_election: '⚡',
  veto: '🚫',
  game_over: '🏆',
  legislative_start: '📋',
}

const PHASE_LABELS = {
  nomination: 'Nomination',
  election: 'Election',
  legislative_president: 'President Choosing',
  legislative_chancellor: 'Chancellor Choosing',
  executive_action: 'Executive Action',
  game_over: 'Game Over',
}

function formatEventMessage(event) {
  switch (event.type) {
    case 'round_start':
      return `Round ${event.data.round} begins. President: Seat ${event.data.president + 1}`
    case 'nomination':
      return `${event.data.president} nominates ${event.data.chancellor} as Chancellor`
    case 'election_passed':
      return `Election passed (${event.data.ja} Ja, ${event.data.nein} Nein)`
    case 'election_failed':
      return `Election failed (${event.data.ja} Ja, ${event.data.nein} Nein)`
    case 'policy_enacted':
      return `${event.data.policy} policy enacted`
    case 'investigation':
      return `President investigates Seat ${event.data.target + 1}`
    case 'execution':
      return `Player in Seat ${event.data.target + 1} was executed`
    case 'special_election':
      return `Special election called for Seat ${event.data.target + 1}`
    case 'legislative_start':
      return 'Legislative session begins'
    case 'game_over':
      return `${event.data.winner} wins!`
    default:
      return event.type.replace(/_/g, ' ')
  }
}

export default function GameLog({ events, phase, round, winner, winCondition }) {
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [events])

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gold/20">
        <h2 className="font-display text-xl tracking-widest text-gold">GAME LOG</h2>
        <div className="flex items-center gap-4 mt-2">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-gray-500">ROUND</span>
            <span className="font-display text-lg text-white">{round}</span>
          </div>
          <div className="flex-1 h-px bg-gold/20" />
          <div className="px-2 py-1 bg-gold/10 rounded">
            <span className="font-mono text-xs text-gold">
              {PHASE_LABELS[phase] || phase}
            </span>
          </div>
        </div>
      </div>

      {/* Events list */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-3"
      >
        {events.map((event, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={`
              flex items-start gap-3 p-3 rounded-lg
              ${event.type.includes('liberal') || event.type === 'election_passed'
                ? 'bg-liberal-900/20 border-l-2 border-liberal-500'
                : event.type.includes('fascist') || event.type === 'election_failed' || event.type === 'execution'
                ? 'bg-fascist-900/20 border-l-2 border-fascist-500'
                : 'bg-white/5 border-l-2 border-gold/30'
              }
            `}
          >
            <span className="text-lg flex-shrink-0">
              {EVENT_ICONS[event.type] || '•'}
            </span>
            <div className="flex-1 min-w-0">
              <p className="font-body text-sm text-white/80 leading-relaxed">
                {formatEventMessage(event)}
              </p>
            </div>
          </motion.div>
        ))}

        {events.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p className="font-mono text-sm">Waiting for game events...</p>
          </div>
        )}
      </div>

      {/* Game stats footer */}
      <div className="p-4 border-t border-gold/20 bg-black/40">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="font-mono text-xs text-gray-500 mb-1">LIBERALS</div>
            <div className="font-display text-2xl text-liberal-400">
              {events.filter(e => e.type === 'liberal_policy').length}
            </div>
          </div>
          <div>
            <div className="font-mono text-xs text-gray-500 mb-1">FASCISTS</div>
            <div className="font-display text-2xl text-fascist-400">
              {events.filter(e => e.type === 'fascist_policy').length}
            </div>
          </div>
        </div>

        {/* Winner announcement */}
        {winner && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`
              mt-4 p-3 rounded-lg text-center
              ${winner === 'liberal'
                ? 'bg-liberal-900/50 border border-liberal-500'
                : 'bg-fascist-900/50 border border-fascist-500'
              }
            `}
          >
            <div className="font-display text-lg tracking-wider">
              {winner.toUpperCase()} VICTORY
            </div>
            <div className="font-mono text-xs text-gray-400 mt-1">
              {winCondition}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
