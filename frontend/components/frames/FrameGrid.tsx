'use client'

import { useState } from 'react'
import Link from 'next/link'
import type { Frame } from '@/lib/types'
import FrameCard from './FrameCard'

type Props = {
  frames: Frame[]
  jobId: string
  generationsRemaining: number
  onGenerationComplete: (newRemaining: number) => void
}

export default function FrameGrid({ frames, jobId, generationsRemaining, onGenerationComplete }: Props) {
  const [showAll, setShowAll] = useState(false)
  const [remaining, setRemaining] = useState(generationsRemaining)

  function handleComplete(newRemaining: number) {
    setRemaining(newRemaining)
    onGenerationComplete(newRemaining)
  }

  const visible = showAll ? frames : frames.slice(0, 5)
  const hidden   = frames.length - 5

  return (
    <div className="mt-6 pb-4">
      {/* Section header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-stone-900">Your Top Frames</h2>
          <p className="text-stone-400 text-xs mt-0.5">Matched to your face shape and undertone</p>
        </div>
        <span className={`text-sm font-semibold px-3 py-1.5 rounded-full ${
          remaining > 0
            ? 'bg-amber-50 text-amber-600 border border-amber-100'
            : 'bg-stone-100 text-stone-400'
        }`}>
          {remaining} {remaining === 1 ? 'try' : 'tries'} left
        </span>
      </div>

      {/* Limit reached banner */}
      {remaining === 0 && (
        <div className="mb-4 p-4 bg-amber-50 border border-amber-100 rounded-2xl">
          <p className="text-amber-800 text-sm font-semibold">You've used all 3 free try-ons.</p>
          <p className="text-amber-700/70 text-xs mt-1">
            Recommendations and buy links are still active. Sign up to unlock more try-ons.
          </p>
        </div>
      )}

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

      {!showAll && hidden > 0 && (
        <button
          onClick={() => setShowAll(true)}
          className="mt-4 w-full py-4 border border-stone-200 rounded-2xl text-stone-600 text-sm font-medium
                     bg-white active:bg-stone-50 transition-colors"
        >
          Show {hidden} more frame{hidden > 1 ? 's' : ''}
        </button>
      )}

      {/* Browse more CTA */}
      <div className="mt-6 p-4 bg-stone-100 rounded-2xl text-center">
        <p className="text-stone-500 text-sm mb-2">Want to explore more frames?</p>
        <Link
          href="/#catalogue"
          className="text-amber-600 font-semibold text-sm underline underline-offset-2"
        >
          Browse the full catalogue →
        </Link>
      </div>
    </div>
  )
}
