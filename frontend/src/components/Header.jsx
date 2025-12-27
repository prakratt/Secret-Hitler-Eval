import React from 'react'
import { motion } from 'motion/react'

export default function Header({
  showRoles,
  setShowRoles,
  onFileUpload,
  isPlaying,
  setIsPlaying,
  onStepBack,
  onStepForward,
  gameLoaded,
  currentState,
  totalStates,
}) {
  return (
    <header className="relative z-20 border-b border-gold/30 bg-black/60 backdrop-blur-md">
      {/* Art deco top border */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-gold to-transparent" />

      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo / Title */}
          <div className="flex items-center gap-4">
            {/* Eagle emblem */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-12 h-12 relative"
            >
              <svg viewBox="0 0 100 80" className="w-full h-full fill-gold">
                <path d="M50 10 L60 25 L85 22 L70 35 L78 55 L50 42 L22 55 L30 35 L15 22 L40 25 Z" />
                <circle cx="50" cy="30" r="8" fill="#0a0a0a" />
                <circle cx="50" cy="30" r="5" fill="#d4a742" />
              </svg>
            </motion.div>

            <div>
              <motion.h1
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="font-display text-4xl tracking-[0.2em] text-gold"
              >
                SECRET HITLER
              </motion.h1>
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="font-mono text-xs text-gold/50 tracking-widest"
              >
                AI ARENA • SPECTATOR MODE
              </motion.p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-6">
            {/* Playback controls */}
            <div className="flex items-center gap-2 bg-black/40 rounded-lg p-2 border border-gold/20">
              {/* Step back */}
              <button
                onClick={onStepBack}
                disabled={!gameLoaded || currentState === 0}
                className="w-10 h-10 flex items-center justify-center rounded bg-gold/10 hover:bg-gold/20 transition-colors text-gold disabled:opacity-30 disabled:cursor-not-allowed"
                title="Step back"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z" />
                </svg>
              </button>

              {/* Play/Pause */}
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                disabled={!gameLoaded}
                className="w-10 h-10 flex items-center justify-center rounded bg-gold/10 hover:bg-gold/20 transition-colors text-gold disabled:opacity-30 disabled:cursor-not-allowed"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <rect x="6" y="4" width="4" height="16" />
                    <rect x="14" y="4" width="4" height="16" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>

              {/* Step forward */}
              <button
                onClick={onStepForward}
                disabled={!gameLoaded || currentState >= totalStates - 1}
                className="w-10 h-10 flex items-center justify-center rounded bg-gold/10 hover:bg-gold/20 transition-colors text-gold disabled:opacity-30 disabled:cursor-not-allowed"
                title="Step forward"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 18l8.5-6L6 6v12zm2 0V6l6.5 6L8 18zm8-12v12h2V6h-2z" />
                </svg>
              </button>

              {/* Progress indicator */}
              {gameLoaded && (
                <div className="ml-2 px-2 border-l border-gold/20">
                  <span className="font-mono text-xs text-gold/60">
                    {currentState + 1}/{totalStates}
                  </span>
                </div>
              )}
            </div>

            {/* Role visibility toggle */}
            <button
              onClick={() => setShowRoles(!showRoles)}
              className={`px-4 py-2 rounded-lg font-mono text-sm tracking-wide transition-all ${
                showRoles
                  ? 'bg-gold/20 text-gold border border-gold/40'
                  : 'bg-black/40 text-gold/50 border border-gold/20 hover:border-gold/40'
              }`}
            >
              {showRoles ? '👁 ROLES VISIBLE' : '👁‍🗨 ROLES HIDDEN'}
            </button>

            {/* Load game */}
            <label className="px-4 py-2 rounded-lg font-mono text-sm tracking-wide bg-gold/10 text-gold border border-gold/30 hover:bg-gold/20 transition-colors cursor-pointer">
              <input
                type="file"
                accept=".json"
                onChange={onFileUpload}
                className="hidden"
              />
              LOAD GAME
            </label>
          </div>
        </div>
      </div>

      {/* Art deco bottom border */}
      <div className="absolute bottom-0 left-1/4 right-1/4 h-px bg-gradient-to-r from-transparent via-gold/50 to-transparent" />
    </header>
  )
}
