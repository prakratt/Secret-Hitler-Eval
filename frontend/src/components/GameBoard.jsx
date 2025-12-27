import React from 'react'
import { motion } from 'motion/react'

export default function GameBoard({
  liberalPolicies,
  fascistPolicies,
  electionTracker,
  drawPileSize,
  phase,
  round
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative w-[500px] h-[320px] bg-gradient-to-b from-[#1a1a1a] to-[#0f0f0f] rounded-xl border-2 border-gold/40 shadow-2xl"
    >
      {/* Decorative corners */}
      <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-gold/60 rounded-tl-xl" />
      <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-gold/60 rounded-tr-xl" />
      <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-gold/60 rounded-bl-xl" />
      <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-gold/60 rounded-br-xl" />

      <div className="p-6 h-full flex flex-col justify-between">
        {/* Liberal Track */}
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-3 h-3 rounded-full bg-liberal-500" />
            <span className="font-display text-lg tracking-widest text-liberal-400">LIBERAL</span>
          </div>
          <div className="flex gap-2">
            {[0, 1, 2, 3, 4].map((i) => (
              <motion.div
                key={`liberal-${i}`}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`policy-slot ${i < liberalPolicies ? 'liberal filled' : 'empty'}`}
              >
                {i < liberalPolicies && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-8 h-12 bg-gradient-to-b from-liberal-600 to-liberal-800 rounded flex items-center justify-center"
                  >
                    <svg className="w-6 h-6 text-liberal-200" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                    </svg>
                  </motion.div>
                )}
                {i >= liberalPolicies && (
                  <span className="font-mono text-xs text-gray-600">{i + 1}</span>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        {/* Center info */}
        <div className="flex items-center justify-between px-8">
          {/* Draw pile */}
          <div className="text-center">
            <div className="relative w-12 h-16 mx-auto mb-2">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="absolute inset-0 bg-gradient-to-b from-gray-700 to-gray-900 rounded border border-gray-600"
                  style={{
                    transform: `translateY(${-i * 2}px) translateX(${-i * 1}px)`,
                    zIndex: 3 - i
                  }}
                />
              ))}
            </div>
            <span className="font-mono text-xs text-gold/60">{drawPileSize} CARDS</span>
          </div>

          {/* Round and Phase indicator */}
          <div className="text-center">
            <div className="font-display text-2xl text-gold tracking-wider mb-1">
              ROUND {round}
            </div>
            <div className="font-mono text-xs text-gold/50 uppercase">
              {phase.replace(/_/g, ' ')}
            </div>
          </div>

          {/* Election tracker */}
          <div className="text-center">
            <div className="flex gap-2 mb-2 justify-center">
              {[0, 1, 2].map((i) => (
                <motion.div
                  key={`election-${i}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.5 + i * 0.1 }}
                  className={`w-8 h-8 rounded-full border-2 flex items-center justify-center ${
                    i < electionTracker
                      ? 'bg-fascist-700 border-fascist-500 shadow-lg shadow-fascist-500/50'
                      : 'border-gray-600 bg-gray-900'
                  }`}
                >
                  {i < electionTracker && (
                    <span className="text-fascist-200 font-bold text-sm">✕</span>
                  )}
                </motion.div>
              ))}
            </div>
            <span className="font-mono text-xs text-gray-500">ELECTION TRACKER</span>
          </div>
        </div>

        {/* Fascist Track */}
        <div className="flex flex-col items-center">
          <div className="flex gap-2 mb-3">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <motion.div
                key={`fascist-${i}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`policy-slot relative ${i < fascistPolicies ? 'fascist filled' : 'empty'}`}
              >
                {/* Power indicator */}
                {i >= 2 && i < fascistPolicies && (
                  <div className="absolute -top-6 left-1/2 -translate-x-1/2">
                    <span className="text-xs text-fascist-400">
                      {i === 2 && '🔍'}
                      {i === 3 && '🎯'}
                      {i === 4 && '💀'}
                    </span>
                  </div>
                )}

                {i < fascistPolicies && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-8 h-12 bg-gradient-to-b from-fascist-600 to-fascist-900 rounded flex items-center justify-center"
                  >
                    <svg className="w-6 h-6 text-fascist-200" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2L4 7v10l8 5 8-5V7l-8-5zm0 2.5L18 8v8l-6 3.5L6 16V8l6-3.5z"/>
                    </svg>
                  </motion.div>
                )}
                {i >= fascistPolicies && (
                  <span className="font-mono text-xs text-gray-600">{i + 1}</span>
                )}
              </motion.div>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-fascist-600" />
            <span className="font-display text-lg tracking-widest text-fascist-400">FASCIST</span>
          </div>
        </div>
      </div>

      {/* Veto power indicator */}
      {fascistPolicies >= 5 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-fascist-900 border border-fascist-500 rounded-full"
        >
          <span className="font-mono text-xs text-fascist-300 tracking-wider">VETO POWER UNLOCKED</span>
        </motion.div>
      )}
    </motion.div>
  )
}
