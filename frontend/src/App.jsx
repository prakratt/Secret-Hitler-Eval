import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import GameBoard from './components/GameBoard'
import PlayersCircle from './components/PlayersCircle'
import GameLog from './components/GameLog'
import Header from './components/Header'
import { parseGameLog, extractRoles, formatDuration } from './utils/gameLogParser'

// Sample game state for demonstration when no log is loaded
const DEMO_GAME_STATE = {
  round: 4,
  phase: 'legislative_chancellor',
  liberalPolicies: 2,
  fascistPolicies: 3,
  electionTracker: 1,
  drawPileSize: 11,
  players: [
    { seat: 0, name: 'GPT-4o', role: 'liberal', team: 'liberal', isDead: false, isPresident: false, isChancellor: false },
    { seat: 1, name: 'GPT-5.1', role: 'fascist', team: 'fascist', isDead: false, isPresident: true, isChancellor: false },
    { seat: 2, name: 'Claude Opus 4.5', role: 'liberal', team: 'liberal', isDead: false, isPresident: false, isChancellor: true },
    { seat: 3, name: 'Claude Sonnet 4.5', role: 'hitler', team: 'fascist', isDead: false, isPresident: false, isChancellor: false },
    { seat: 4, name: 'Gemini 2.5 Flash', role: 'liberal', team: 'liberal', isDead: true, isPresident: false, isChancellor: false },
    { seat: 5, name: 'Llama 3.3 70B', role: 'liberal', team: 'liberal', isDead: false, isPresident: false, isChancellor: false },
    { seat: 6, name: 'Grok 4', role: 'fascist', team: 'fascist', isDead: false, isPresident: false, isChancellor: false },
  ],
  messages: [
    { seat: 1, name: 'GPT-5.1', content: 'I trust Claude Opus to make the right choice as Chancellor. We need a liberal policy here.' },
    { seat: 2, name: 'Claude Opus 4.5', content: 'I received two fascist policies from the President. I have no choice but to enact one.' },
    { seat: 5, name: 'Llama 3.3 70B', content: 'That seems suspicious. How can there be no liberal policies?' },
  ],
  events: [
    { type: 'round_start', data: { round: 4, president: 1 } },
    { type: 'nomination', data: { president: 'GPT-5.1', chancellor: 'Claude Opus 4.5' } },
    { type: 'election_passed', data: { ja: 4, nein: 2 } },
    { type: 'legislative_start', data: {} },
  ],
  winner: null,
  winCondition: null,
}

export default function App() {
  const [gameStates, setGameStates] = useState([])
  const [currentStateIndex, setCurrentStateIndex] = useState(0)
  const [gameState, setGameState] = useState(DEMO_GAME_STATE)
  const [showRoles, setShowRoles] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState(1000) // ms between states
  const [gameLoaded, setGameLoaded] = useState(false)
  const [gameDuration, setGameDuration] = useState(0)
  const [roles, setRoles] = useState({})

  // Playback effect
  useEffect(() => {
    if (!isPlaying || !gameLoaded || currentStateIndex >= gameStates.length - 1) {
      if (currentStateIndex >= gameStates.length - 1) {
        setIsPlaying(false)
      }
      return
    }

    const timer = setTimeout(() => {
      setCurrentStateIndex(prev => Math.min(prev + 1, gameStates.length - 1))
    }, playbackSpeed)

    return () => clearTimeout(timer)
  }, [isPlaying, currentStateIndex, gameStates.length, playbackSpeed, gameLoaded])

  // Update game state when index changes
  useEffect(() => {
    if (gameStates.length > 0 && gameStates[currentStateIndex]) {
      const state = gameStates[currentStateIndex]
      // Apply revealed roles if showRoles is true
      if (showRoles && Object.keys(roles).length > 0) {
        state.players = state.players.map(p => ({
          ...p,
          role: roles[p.seat]?.role || p.role,
          team: roles[p.seat]?.team || p.team,
        }))
      }
      setGameState(state)
    }
  }, [currentStateIndex, gameStates, showRoles, roles])

  // Load game from JSON file
  const loadGame = useCallback(async (file) => {
    try {
      const text = await file.text()
      const data = JSON.parse(text)

      const parsed = parseGameLog(data)
      const extractedRoles = extractRoles(data)

      setGameStates(parsed.states)
      setRoles(extractedRoles)
      setGameDuration(parsed.duration)
      setCurrentStateIndex(0)
      setGameLoaded(true)
      setIsPlaying(false)

      if (parsed.states.length > 0) {
        const initialState = { ...parsed.states[0] }
        // Apply roles
        if (Object.keys(extractedRoles).length > 0) {
          initialState.players = initialState.players.map(p => ({
            ...p,
            role: extractedRoles[p.seat]?.role || 'unknown',
            team: extractedRoles[p.seat]?.team || 'unknown',
          }))
        }
        setGameState(initialState)
      }

      console.log('Loaded game with', parsed.states.length, 'states')
    } catch (err) {
      console.error('Failed to load game:', err)
      alert('Failed to load game file. Please check the format.')
    }
  }, [])

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (file) {
      loadGame(file)
    }
  }

  const handleStepBack = () => {
    setCurrentStateIndex(prev => Math.max(0, prev - 1))
    setIsPlaying(false)
  }

  const handleStepForward = () => {
    setCurrentStateIndex(prev => Math.min(gameStates.length - 1, prev + 1))
    setIsPlaying(false)
  }

  const handleSeek = (index) => {
    setCurrentStateIndex(index)
    setIsPlaying(false)
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] relative overflow-hidden">
      {/* Background effects */}
      <div className="noise-overlay" />
      <div className="vignette" />

      {/* Decorative background pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0" style={{
          backgroundImage: `repeating-linear-gradient(
            45deg,
            transparent,
            transparent 40px,
            rgba(212, 167, 66, 0.1) 40px,
            rgba(212, 167, 66, 0.1) 41px
          )`
        }} />
      </div>

      {/* Main content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        <Header
          showRoles={showRoles}
          setShowRoles={setShowRoles}
          onFileUpload={handleFileUpload}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
          onStepBack={handleStepBack}
          onStepForward={handleStepForward}
          gameLoaded={gameLoaded}
          currentState={currentStateIndex}
          totalStates={gameStates.length}
          gameDuration={gameDuration}
        />

        <main className="flex-1 flex">
          {/* Game area */}
          <div className="flex-1 relative p-4">
            {/* Players arranged in circle with board in center */}
            <div className="h-full flex items-center justify-center">
              <PlayersCircle
                players={gameState.players}
                messages={gameState.messages}
                showRoles={showRoles}
              >
                <GameBoard
                  liberalPolicies={gameState.liberalPolicies}
                  fascistPolicies={gameState.fascistPolicies}
                  electionTracker={gameState.electionTracker}
                  drawPileSize={gameState.drawPileSize}
                  phase={gameState.phase}
                  round={gameState.round}
                />
              </PlayersCircle>
            </div>

            {/* Timeline scrubber */}
            {gameLoaded && gameStates.length > 1 && (
              <div className="absolute bottom-4 left-4 right-4">
                <div className="bg-black/60 backdrop-blur-sm rounded-lg p-4 border border-gold/20">
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-xs text-gold/60">
                      {currentStateIndex + 1} / {gameStates.length}
                    </span>
                    <input
                      type="range"
                      min="0"
                      max={gameStates.length - 1}
                      value={currentStateIndex}
                      onChange={(e) => handleSeek(parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-gold"
                    />
                    <span className="font-mono text-xs text-gold/60">
                      {formatDuration(gameDuration)}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Side panel - Game Log */}
          <aside className="w-80 border-l border-gold/20 bg-black/40 backdrop-blur-sm">
            <GameLog
              events={gameState.events}
              phase={gameState.phase}
              round={gameState.round}
              winner={gameState.winner}
              winCondition={gameState.winCondition}
            />
          </aside>
        </main>

        {/* Winner overlay */}
        <AnimatePresence>
          {gameState.winner && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
              onClick={() => {}} // Prevent closing for now
            >
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2, type: 'spring' }}
                className={`text-center p-12 ${
                  gameState.winner === 'liberal'
                    ? 'bg-gradient-to-b from-liberal-900 to-liberal-950'
                    : 'bg-gradient-to-b from-fascist-900 to-fascist-950'
                } rounded-lg border-4 ${
                  gameState.winner === 'liberal' ? 'border-liberal-500' : 'border-fascist-500'
                }`}
              >
                <h2 className="font-display text-6xl mb-4 tracking-wider">
                  {gameState.winner === 'liberal' ? 'LIBERALS' : 'FASCISTS'} WIN
                </h2>
                <p className="font-body text-xl text-gold/80">
                  {gameState.winCondition?.replace(/_/g, ' ')}
                </p>
                <button
                  onClick={() => setCurrentStateIndex(0)}
                  className="mt-6 px-6 py-2 bg-gold/20 hover:bg-gold/30 border border-gold/50 rounded-lg font-mono text-sm text-gold transition-colors"
                >
                  REPLAY FROM START
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Demo mode indicator */}
        {!gameLoaded && (
          <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40">
            <div className="bg-gold/10 border border-gold/30 rounded-lg px-4 py-2">
              <span className="font-mono text-sm text-gold/70">
                DEMO MODE — Load a game log to see real gameplay
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
