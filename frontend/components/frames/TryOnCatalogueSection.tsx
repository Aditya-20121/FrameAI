'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getCatalogue } from '@/lib/api'
import type { CatalogueFrame } from '@/lib/types'
import FrameCard from './FrameCard'
import { ChevronRight } from 'lucide-react'
import { fadeUp, stagger } from '@/lib/motion'

const STYLE_TABS = [
  { label: 'All',       value: '' },
  { label: 'Round',     value: 'round' },
  { label: 'Square',    value: 'square' },
  { label: 'Oval',      value: 'oval' },
  { label: 'Rectangle', value: 'rectangular' },
  { label: 'Wayfarer',  value: 'wayfarer' },
  { label: 'Cat-Eye',   value: 'cat-eye' },
  { label: 'Aviator',   value: 'aviator' },
  { label: 'Rimless',   value: 'rimless' },
]

const LIMIT = 10

type Props = {
  jobId: string
  generationsRemaining: number
  onGenerationComplete: (newRemaining: number) => void
}

export default function TryOnCatalogueSection({ jobId, generationsRemaining, onGenerationComplete }: Props) {
  const [activeStyle, setActiveStyle] = useState('')
  const [frames, setFrames]           = useState<CatalogueFrame[]>([])
  const [loading, setLoading]         = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [offset, setOffset]           = useState(0)
  const [hasMore, setHasMore]         = useState(true)
  const [fetchError, setFetchError]   = useState<string | null>(null)
  const [remaining, setRemaining]     = useState(generationsRemaining)

  useEffect(() => { setRemaining(generationsRemaining) }, [generationsRemaining])

  async function fetchFrames(style: string, newOffset: number, replace: boolean) {
    try {
      replace ? setLoading(true) : setLoadingMore(true)
      const res = await getCatalogue({ style: style || undefined, limit: LIMIT, offset: newOffset })
      setFrames(prev => replace ? res.frames : [...prev, ...res.frames])
      setHasMore(res.frames.length === LIMIT)
      setOffset(newOffset + res.frames.length)
    } catch (err: unknown) {
      setFetchError(err instanceof Error ? err.message : JSON.stringify(err))
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  useEffect(() => {
    setOffset(0)
    setFetchError(null)
    fetchFrames(activeStyle, 0, true)
  }, [activeStyle])

  function handleComplete(newRemaining: number) {
    setRemaining(newRemaining)
    onGenerationComplete(newRemaining)
  }

  return (
    <div className="mt-8">
      {/* Header */}
      <div className="mb-5">
        <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-1">
          Browse & Try On
        </p>
        <div className="flex items-end justify-between gap-3">
          <h2 className="text-xl font-extrabold text-stone-900 tracking-tight">
            Browse frames
          </h2>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full flex-shrink-0 ${
            remaining > 0
              ? 'bg-amber-50 text-amber-500 border border-amber-100'
              : 'bg-stone-100 text-stone-400'
          }`}>
            {remaining} try-on{remaining !== 1 ? 's' : ''} left
          </span>
        </div>
      </div>

      {remaining === 0 && (
        <div className="mb-5 p-4 bg-amber-50 border border-amber-100 rounded-2xl">
          <p className="text-amber-700 text-sm font-semibold">You've used all 3 free try-ons.</p>
          <p className="text-amber-700/70 text-xs mt-0.5 leading-relaxed">
            You can still browse and buy any frame using the link on each card.
          </p>
        </div>
      )}

      {/* Style filter tabs */}
      <div
        className="flex gap-2 overflow-x-auto scrollbar-none -mx-4 px-4 mb-6 pb-1"
        style={{ scrollbarWidth: 'none' }}
      >
        {STYLE_TABS.map(tab => (
          <button
            key={tab.value}
            onClick={() => setActiveStyle(tab.value)}
            className={`flex-shrink-0 px-4 py-2 rounded-full text-sm font-medium transition-all
              ${activeStyle === tab.value
                ? 'bg-stone-900 text-white'
                : 'bg-white text-stone-600 border border-stone-200 active:bg-stone-50'
              }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Cards */}
      {fetchError ? (
        <div className="py-8 text-center">
          <p className="text-red-500 text-sm font-semibold mb-1">Could not load frames</p>
          <p className="text-stone-400 text-xs font-mono break-all">{fetchError}</p>
        </div>
      ) : loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-stone-100 overflow-hidden">
              <div className="bg-stone-100 aspect-square animate-pulse" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-stone-100 rounded animate-pulse w-3/4" />
                <div className="h-3 bg-stone-100 rounded animate-pulse w-1/2" />
                <div className="h-10 bg-stone-100 rounded-xl animate-pulse mt-3" />
              </div>
            </div>
          ))}
        </div>
      ) : frames.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-stone-400 text-sm">No frames found for this style.</p>
          <button
            onClick={() => setActiveStyle('')}
            className="mt-3 text-amber-500 text-sm font-medium underline underline-offset-2"
          >
            Show all frames
          </button>
        </div>
      ) : (
        <>
          <motion.div
            key={activeStyle}
            className="space-y-4"
            initial="hidden"
            animate="show"
            variants={stagger(0.06)}
          >
            {frames.map(frame => (
              <motion.div key={frame.frame_id} variants={fadeUp}>
                <FrameCard
                  frame={frame}
                  jobId={jobId}
                  generationsRemaining={remaining}
                  onComplete={handleComplete}
                />
              </motion.div>
            ))}
          </motion.div>

          {hasMore && (
            <button
              onClick={() => fetchFrames(activeStyle, offset, false)}
              disabled={loadingMore}
              className="mt-6 w-full py-3.5 border border-stone-200 rounded-xl text-stone-600 text-sm font-medium
                         flex items-center justify-center gap-2 active:bg-stone-100 transition-colors disabled:opacity-50 bg-white min-h-[48px]"
            >
              {loadingMore ? (
                <><div className="w-4 h-4 border-2 border-stone-300 border-t-stone-600 rounded-full animate-spin" /> Loading…</>
              ) : (
                <>Load more frames <ChevronRight className="w-4 h-4" /></>
              )}
            </button>
          )}
        </>
      )}
    </div>
  )
}
