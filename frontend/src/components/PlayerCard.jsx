import React from 'react'
import { motion } from 'motion/react'

// Model provider icons/colors
const MODEL_STYLES = {
  'GPT': { color: '#10a37f', icon: '◆' },
  'Claude': { color: '#d4a27f', icon: '◇' },
  'Gemini': { color: '#4285f4', icon: '✦' },
  'Llama': { color: '#7c3aed', icon: '◈' },
  'Grok': { color: '#1da1f2', icon: '✧' },
}

function getModelStyle(name) {
  for (const [key, style] of Object.entries(MODEL_STYLES)) {
    if (name.includes(key)) return style
  }
  return { color: '#888', icon: '●' }
}

export default function PlayerCard({ player, showRoles, style, animationDelay = 0 }) {
  const modelStyle = getModelStyle(player.name)

  const roleColors = {
    liberal: {
      bg: 'from-liberal-900/80 to-liberal-950/90',
      border: 'border-liberal-600',
      badge: 'bg-liberal-700 text-liberal-100',
      glow: 'shadow-liberal-500/30'
    },
    fascist: {
      bg: 'from-fascist-900/80 to-fascist-950/90',
      border: 'border-fascist-600',
      badge: 'bg-fascist-700 text-fascist-100',
      glow: 'shadow-fascist-500/30'
    },
    hitler: {
      bg: 'from-gray-900/80 to-black/90',
      border: 'border-gold',
      badge: 'bg-black text-gold border border-gold',
      glow: 'shadow-gold/30'
    }
  }

  const colors = showRoles ? roleColors[player.role] : {
    bg: 'from-gray-800/80 to-gray-900/90',
    border: 'border-gray-600',
    badge: 'bg-gray-700 text-gray-300',
    glow: 'shadow-gray-500/20'
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: animationDelay, type: 'spring', stiffness: 200 }}
      style={style}
      className={`
        player-card absolute
        ${player.isPresident ? 'president' : ''}
        ${player.isChancellor ? 'chancellor' : ''}
        ${player.isDead ? 'dead' : ''}
      `}
    >
      <div className={`
        relative w-36 bg-gradient-to-b ${colors.bg}
        rounded-lg border-2 ${colors.border}
        shadow-lg ${colors.glow}
        overflow-hidden backdrop-blur-sm
        transition-all duration-300
      `}>
        {/* Dead overlay */}
        {player.isDead && (
          <div className="absolute inset-0 bg-black/60 z-20 flex items-center justify-center">
            <span className="font-display text-2xl text-fascist-500 rotate-[-15deg]">DEAD</span>
          </div>
        )}

        {/* President/Chancellor badge */}
        {(player.isPresident || player.isChancellor) && (
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className={`
              absolute -top-1 left-1/2 -translate-x-1/2 z-10
              px-2 py-0.5 rounded-b text-xs font-mono tracking-wider
              ${player.isPresident ? 'bg-gold text-black' : 'bg-gray-300 text-black'}
            `}
          >
            {player.isPresident ? 'PRESIDENT' : 'CHANCELLOR'}
          </motion.div>
        )}

        {/* Model icon header */}
        <div
          className="h-10 flex items-center justify-center relative overflow-hidden"
          style={{ backgroundColor: modelStyle.color + '20' }}
        >
          <span
            className="text-2xl"
            style={{ color: modelStyle.color }}
          >
            {modelStyle.icon}
          </span>
          {/* Decorative line */}
          <div
            className="absolute bottom-0 left-0 right-0 h-px"
            style={{ background: `linear-gradient(90deg, transparent, ${modelStyle.color}, transparent)` }}
          />
        </div>

        {/* Content */}
        <div className="p-3">
          {/* Seat number */}
          <div className="absolute top-12 right-2">
            <span className="font-mono text-xs text-gray-500">#{player.seat + 1}</span>
          </div>

          {/* Name */}
          <h3 className="font-body font-bold text-sm text-white/90 mb-2 pr-6 leading-tight">
            {player.name}
          </h3>

          {/* Role badge */}
          {showRoles && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: animationDelay + 0.2 }}
              className={`
                inline-block px-2 py-0.5 rounded text-xs font-mono uppercase tracking-wide
                ${colors.badge}
              `}
            >
              {player.role === 'hitler' ? '☠ HITLER' : player.role === 'fascist' ? '✕ FASCIST' : '✓ LIBERAL'}
            </motion.div>
          )}

          {/* Hidden role indicator */}
          {!showRoles && (
            <div className="inline-block px-2 py-0.5 rounded text-xs font-mono text-gray-500 bg-gray-800">
              HIDDEN
            </div>
          )}
        </div>

        {/* Team indicator bar */}
        {showRoles && (
          <div className={`
            h-1
            ${player.team === 'liberal' ? 'bg-liberal-500' : 'bg-fascist-500'}
          `} />
        )}
      </div>
    </motion.div>
  )
}
