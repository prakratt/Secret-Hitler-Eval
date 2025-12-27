import React from 'react'
import { AnimatePresence } from 'motion/react'
import PlayerCard from './PlayerCard'
import SpeechBubble from './SpeechBubble'

export default function PlayersCircle({ players, messages, showRoles, children }) {
  // Oval/ellipse layout for players around the board
  const centerX = 400  // Center of the container
  const centerY = 320  // Center of the container
  const radiusX = 380  // Horizontal radius
  const radiusY = 280  // Vertical radius

  // Calculate positions for each player around the ellipse
  const getPlayerPosition = (index, total) => {
    // Start from top and go clockwise
    // Offset by half a slot to center the distribution
    const startAngle = -Math.PI / 2 // Start from top
    const angle = startAngle + (index / total) * 2 * Math.PI

    const x = centerX + radiusX * Math.cos(angle)
    const y = centerY + radiusY * Math.sin(angle)

    // Determine speech bubble position based on where player is
    let bubblePosition = 'bottom'
    if (angle > -Math.PI / 4 && angle < Math.PI / 4) {
      bubblePosition = 'left' // Right side of circle -> bubble on left
    } else if (angle > Math.PI * 3/4 || angle < -Math.PI * 3/4) {
      bubblePosition = 'right' // Left side of circle -> bubble on right
    } else if (angle >= Math.PI / 4 && angle <= Math.PI * 3/4) {
      bubblePosition = 'top' // Bottom of circle -> bubble on top
    } else {
      bubblePosition = 'bottom' // Top of circle -> bubble on bottom
    }

    return { x, y, bubblePosition }
  }

  // Get latest message for each player
  const latestMessages = {}
  messages.forEach(msg => {
    latestMessages[msg.seat] = msg
  })

  return (
    <div className="relative" style={{ width: centerX * 2, height: centerY * 2 }}>
      {/* Players */}
      {players.map((player, index) => {
        const pos = getPlayerPosition(index, players.length)
        const latestMessage = latestMessages[player.seat]

        return (
          <div key={player.seat}>
            <PlayerCard
              player={player}
              showRoles={showRoles}
              animationDelay={index * 0.1}
              style={{
                left: pos.x,
                top: pos.y,
                transform: 'translate(-50%, -50%)',
              }}
            />

            {/* Speech bubble for this player */}
            <AnimatePresence>
              {latestMessage && (
                <div
                  className="absolute pointer-events-none"
                  style={{
                    left: pos.x,
                    top: pos.y,
                    transform: 'translate(-50%, -50%)',
                  }}
                >
                  <SpeechBubble
                    message={latestMessage}
                    position={pos.bubblePosition}
                  />
                </div>
              )}
            </AnimatePresence>
          </div>
        )
      })}

      {/* Center content (Game Board) */}
      <div
        className="absolute"
        style={{
          left: centerX,
          top: centerY,
          transform: 'translate(-50%, -50%)',
        }}
      >
        {children}
      </div>

      {/* Decorative connecting lines (optional) */}
      <svg
        className="absolute inset-0 pointer-events-none"
        style={{ width: centerX * 2, height: centerY * 2 }}
      >
        <defs>
          <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#d4a742" stopOpacity="0" />
            <stop offset="50%" stopColor="#d4a742" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#d4a742" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Ellipse outline */}
        <ellipse
          cx={centerX}
          cy={centerY}
          rx={radiusX - 80}
          ry={radiusY - 80}
          fill="none"
          stroke="url(#lineGradient)"
          strokeWidth="1"
          strokeDasharray="8 4"
          opacity="0.5"
        />
      </svg>
    </div>
  )
}
