'use client'

import { useState } from 'react'
import type { Frame, FaceShape, Undertone } from '@/lib/types'
import FrameCard from './FrameCard'

type Props = {
  frames: Frame[]
  jobId: string
  faceShape?: FaceShape | null
  undertone?: Undertone | null
  generationsRemaining: number
  onGenerationComplete: (newRemaining: number) => void
}

const SHAPE_LABELS: Record<string, string> = {
  oval: 'Oval', round: 'Round', square: 'Square',
  heart: 'Heart', diamond: 'Diamond', oblong: 'Oblong',
}

export default function FrameGrid({
  frames, jobId, faceShape, undertone,
  generationsRemaining, onGenerationComplete,
}: Props) {
  const [showAll, setShowAll]   = useState(false)
  const [remaining, setRemaining] = useState(generationsRemaining)

  function handleComplete(newRemaining: number) {
    setRemaining(newRemaining)
    onGenerationComplete(newRemaining)
  }

  const visible = showAll ? frames : frames.slice(0, 5)
  const hidden  = frames.length - 5

  const shapeLabel    = faceShape ? SHAPE_LABELS[faceShape] : null
  const undertoneLabel = undertone ? undertone.charAt(0).toUpperCase() + undertone.slice(1) : null
  const subtitle      = [shapeLabel && `${shapeLabel} face`, undertoneLabel && `${undertoneLabel} undertone`]
    .filter(Boolean).join(' · ')

  return (
    <div className="mt-8">

      {/* ── Section header ────────────────────────────────────────── */}
      <div className="mb-5">
        <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-1">
          Your matches
        </p>
        <div className="flex items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-extrabold text-stone-900 tracking-tight">
              Top {frames.length} frames
            </h2>
            {subtitle && (
              <p className="text-stone-400 text-xs mt-0.5">{subtitle}</p>
            )}
          </div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full flex-shrink-0 ${
            remaining > 0
              ? 'bg-amber-50 text-amber-600 border border-amber-100'
              : 'bg-stone-100 text-stone-400'
          }`}>
            {remaining} try-on{remaining !== 1 ? 's' : ''} left
          </span>
        </div>
      </div>

      {/* ── Limit reached banner ──────────────────────────────────── */}
      {remaining === 0 && (
        <div className="mb-5 p-4 bg-amber-50 border border-amber-100 rounded-2xl">
          <p className="text-amber-800 text-sm font-semibold">You've used all 3 free try-ons.</p>
          <p className="text-amber-700/70 text-xs mt-0.5 leading-relaxed">
            Recommendations and buy links still work — tap any frame to purchase.
          </p>
        </div>
      )}

      {/* ── Frame cards ───────────────────────────────────────────── */}
      <div className="space-y-4">
        {visible.map(frame => (
          <FrameCard
            key={frame.frame_id}
            frame={frame}
            jobId={jobId}
            generationsRemaining={remaining}
            onComplete={handleComplete}
          />
        ))}
      </div>

      {/* ── Show more ─────────────────────────────────────────────── */}
      {!showAll && hidden > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-4 w-full py-4 border border-stone-200 rounded-2xl text-stone-600 text-sm font-semibold
                     bg-white active:bg-stone-50 transition-colors"
        >
          Show {hidden} more frame{hidden > 1 ? 's' : ''}
        </button>
      )}

    </div>
  )
}
