'use client'

import { useState, useEffect, useRef } from 'react'
import { LOADING_QUOTES, type QuoteCategory } from '@/lib/quotes'

type Props = {
  category?: QuoteCategory
  estimatedSeconds?: number
  dark?: boolean
  compact?: boolean
}

export default function QuoteLoader({
  category,
  estimatedSeconds,
  dark = false,
  compact = false,
}: Props) {
  const pool = category
    ? LOADING_QUOTES.filter(q => q.category === category || q.category === 'general')
    : LOADING_QUOTES

  const [index, setIndex] = useState(() => Math.floor(Math.random() * pool.length))
  const [visible, setVisible] = useState(true)
  const [progress, setProgress] = useState(0)
  const startRef = useRef(Date.now())

  useEffect(() => {
    startRef.current = Date.now()
    setProgress(0)
  }, [])

  useEffect(() => {
    const INTERVAL = 3500
    const id = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setIndex(i => (i + 1) % pool.length)
        setVisible(true)
      }, 300)
    }, INTERVAL)
    return () => clearInterval(id)
  }, [pool.length])

  useEffect(() => {
    if (!estimatedSeconds) return
    const id = setInterval(() => {
      const elapsed = (Date.now() - startRef.current) / 1000
      setProgress(Math.min(93, (elapsed / estimatedSeconds) * 100))
    }, 150)
    return () => clearInterval(id)
  }, [estimatedSeconds])

  const quote = pool[index].text

  const mutedText  = dark ? 'text-stone-400' : 'text-stone-400'
  const bodyText   = dark ? 'text-stone-300' : 'text-stone-500'
  const barTrack   = dark ? 'bg-stone-700'   : 'bg-stone-200'

  if (compact) {
    return (
      <div className="flex flex-col items-center gap-2.5 py-5 px-4 text-center">
        <div className="w-5 h-5 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
        <p
          className={`text-xs leading-relaxed italic transition-opacity duration-300 max-w-[220px] ${bodyText} ${
            visible ? 'opacity-100' : 'opacity-0'
          }`}
        >
          "{quote}"
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-5 py-8 px-6 text-center w-full max-w-xs mx-auto">
      {/* Spinner */}
      <div className="w-10 h-10 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />

      {/* Quote */}
      <p
        className={`text-sm leading-relaxed italic transition-opacity duration-300 ${bodyText} ${
          visible ? 'opacity-100' : 'opacity-0'
        }`}
      >
        "{quote}"
      </p>

      {/* Progress bar + time hint */}
      {estimatedSeconds && (
        <div className="w-full">
          <div className={`h-1 ${barTrack} rounded-full overflow-hidden`}>
            <div
              className="h-full bg-amber-400 rounded-full transition-all duration-200 ease-linear"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className={`text-xs mt-2 ${mutedText}`}>
            ~{estimatedSeconds}s
          </p>
        </div>
      )}
    </div>
  )
}
