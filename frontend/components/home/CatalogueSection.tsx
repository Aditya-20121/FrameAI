'use client'

import { useEffect, useState, useRef } from 'react'
import { getCatalogue } from '@/lib/api'
import type { CatalogueFrame } from '@/lib/types'
import FrameCatalogueCard from './FrameCatalogueCard'
import { ChevronRight } from 'lucide-react'

const STYLE_TABS = [
  { label: 'All',         value: '' },
  { label: 'Round',       value: 'round' },
  { label: 'Square',      value: 'square' },
  { label: 'Oval',        value: 'oval' },
  { label: 'Rectangle',   value: 'rectangular' },
  { label: 'Wayfarer',    value: 'wayfarer' },
  { label: 'Cat-Eye',     value: 'cat-eye' },
  { label: 'Aviator',     value: 'aviator' },
  { label: 'Rimless',     value: 'rimless' },
]

const SKELETON_COUNT = 6

export default function CatalogueSection() {
  const [activeStyle, setActiveStyle] = useState('')
  const [frames, setFrames] = useState<CatalogueFrame[]>([])
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const tabsRef = useRef<HTMLDivElement>(null)

  const LIMIT = 12

  async function fetchFrames(style: string, newOffset: number, replace: boolean) {
    try {
      replace ? setLoading(true) : setLoadingMore(true)
      const res = await getCatalogue({ style: style || undefined, limit: LIMIT, offset: newOffset })
      setFrames(prev => replace ? res.frames : [...prev, ...res.frames])
      setHasMore(res.frames.length === LIMIT)
      setOffset(newOffset + res.frames.length)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : JSON.stringify(err)
      setFetchError(msg)
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

  return (
    <section id="catalogue" className="px-4 py-10">
      <div className="mb-5">
        <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-1">
          Catalogue
        </p>
        <div className="flex items-end justify-between">
          <h2 className="text-xl font-extrabold text-stone-900 tracking-tight">Browse frames</h2>
          <span className="text-stone-400 text-xs">400+ styles</span>
        </div>
      </div>

      {/* Style filter tabs — horizontal scroll */}
      <div
        ref={tabsRef}
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

      {/* Frame grid */}
      {fetchError ? (
        <div className="py-8 text-center">
          <p className="text-red-500 text-sm font-semibold mb-1">Could not load frames</p>
          <p className="text-stone-400 text-xs font-mono break-all">{fetchError}</p>
        </div>
      ) : loading ? (
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-stone-100 overflow-hidden">
              <div className="bg-stone-100 aspect-square animate-pulse" />
              <div className="p-3 space-y-2">
                <div className="h-3 bg-stone-100 rounded animate-pulse w-3/4" />
                <div className="h-3 bg-stone-100 rounded animate-pulse w-1/2" />
                <div className="h-4 bg-stone-100 rounded animate-pulse w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : frames.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-stone-400 text-sm">No frames found for this style.</p>
          <button
            onClick={() => setActiveStyle('')}
            className="mt-3 text-amber-600 text-sm font-medium underline underline-offset-2"
          >
            Show all frames
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {frames.map(frame => (
              <FrameCatalogueCard key={frame.frame_id} frame={frame} />
            ))}
          </div>

          {hasMore && (
            <button
              onClick={() => fetchFrames(activeStyle, offset, false)}
              disabled={loadingMore}
              className="mt-6 w-full py-3.5 border border-stone-200 rounded-xl text-stone-600 text-sm font-medium
                         flex items-center justify-center gap-2 active:bg-stone-100 transition-colors disabled:opacity-50"
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
    </section>

  )
}
