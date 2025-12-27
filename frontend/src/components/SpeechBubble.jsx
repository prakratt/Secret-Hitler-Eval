import React from 'react'
import { motion } from 'motion/react'

export default function SpeechBubble({ message, position = 'bottom', style }) {
  const positionStyles = {
    top: {
      container: 'bottom-full mb-3',
      tail: 'top-full left-1/2 -translate-x-1/2 border-b-0 border-l-transparent border-r-transparent border-t-parchment/95',
    },
    bottom: {
      container: 'top-full mt-3',
      tail: 'bottom-full left-1/2 -translate-x-1/2 border-t-0 border-l-transparent border-r-transparent border-b-parchment/95',
    },
    left: {
      container: 'right-full mr-3',
      tail: 'left-full top-1/2 -translate-y-1/2 border-r-0 border-t-transparent border-b-transparent border-l-parchment/95',
    },
    right: {
      container: 'left-full ml-3',
      tail: 'right-full top-1/2 -translate-y-1/2 border-l-0 border-t-transparent border-b-transparent border-r-parchment/95',
    },
  }

  const pos = positionStyles[position]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8, y: position === 'bottom' ? -10 : 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      style={style}
      className={`absolute ${pos.container} z-30`}
    >
      <div className="speech-bubble relative max-w-[260px]">
        {/* Parchment texture effect */}
        <div className="absolute inset-0 opacity-50 rounded-lg overflow-hidden pointer-events-none">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' /%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.15'/%3E%3C/svg%3E")`,
          }} />
        </div>

        {/* Message content */}
        <div className="relative">
          <p className="text-ink font-body text-sm leading-relaxed italic">
            "{message.content}"
          </p>
          <div className="mt-2 pt-2 border-t border-ink/10 flex items-center justify-between">
            <span className="font-mono text-xs text-ink/50">
              — {message.name}
            </span>
          </div>
        </div>

        {/* Tail */}
        <div className={`
          absolute w-0 h-0
          border-[8px]
          ${pos.tail}
        `} />
      </div>
    </motion.div>
  )
}
