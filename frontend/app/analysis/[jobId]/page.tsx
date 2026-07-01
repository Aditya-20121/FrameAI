'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, RotateCcw } from 'lucide-react'
import { getAnalysis, getSession } from '@/lib/api'
import type { AnalysisResponse, SessionResponse } from '@/lib/types'
import AnalysisCard from '@/components/analysis/AnalysisCard'
import TryOnCatalogueSection from '@/components/frames/TryOnCatalogueSection'

const SHAPE_LABELS: Record<string, string> = {
  oval: 'Oval', round: 'Round', square: 'Square',
  heart: 'Heart', diamond: 'Diamond', oblong: 'Oblong',
}
const UNDERTONE_LABELS: Record<string, string> = {
  warm: 'Warm', cool: 'Cool', neutral: 'Neutral',
}

export default function AnalysisPage() {
  const params = useParams()
  const router = useRouter()
  const jobId  = params.jobId as string

  const [analysis, setAnalysis]         = useState<AnalysisResponse | null>(null)
  const [session, setSession]           = useState<SessionResponse | null>(null)
  const [analysisError, setAnalysisError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const result = await getAnalysis(jobId)
        if (cancelled) return
        setAnalysis(result)

        if (result.status === 'complete') {
          try {
            const sess = await getSession()
            if (!cancelled) setSession(sess)
          } catch { /* session fetch failing is non-fatal */ }
        } else if (result.status === 'processing') {
          setTimeout(poll, 1200)
        } else {
          setAnalysisError('Analysis failed. Please try again with a clearer front-facing photo.')
        }
      } catch {
        if (!cancelled) setAnalysisError('Failed to load analysis. Please check your connection.')
      }
    }

    poll()
    return () => { cancelled = true }
  }, [jobId])

  function handleGenerationComplete(newRemaining: number) {
    setSession(s =>
      s ? { ...s, generations_remaining: newRemaining, generations_used: s.limit - newRemaining } : s
    )
  }

  const isComplete      = analysis?.status === 'complete'
  const faceShape       = analysis?.face_shape
  const faceShapeLabel  = analysis?.face_shape_label ?? (faceShape ? SHAPE_LABELS[faceShape] : undefined)
  const undertone       = analysis?.undertone
  const sizeBand        = analysis?.size_band

  return (
    <main className="min-h-screen bg-stone-50">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-sm border-b border-stone-100">
        <div className="max-w-2xl mx-auto flex items-center gap-3 px-4 py-3.5">
          <button
            onClick={() => router.push('/')}
            className="text-stone-400 hover:text-stone-700 transition-colors p-1 -ml-1 rounded-lg"
            aria-label="Back to home"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-amber-500 rounded-md flex items-center justify-center">
              <span className="text-white text-[10px] font-black">F</span>
            </div>
            <span className="text-stone-900 font-bold">FrameAI</span>
          </div>
          {session && (
            <span className={`ml-auto text-xs font-semibold px-2.5 py-1 rounded-full ${
              session.generations_remaining > 0
                ? 'bg-amber-50 text-amber-600 border border-amber-100'
                : 'bg-stone-100 text-stone-400'
            }`}>
              {session.generations_remaining} try-on{session.generations_remaining !== 1 ? 's' : ''} left
            </span>
          )}
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 pb-16">

        {/* ── Error state ─────────────────────────────────────────── */}
        {analysisError ? (
          <div className="mt-8 p-5 bg-red-50 border border-red-200 rounded-2xl">
            <p className="text-red-700 font-semibold text-sm mb-1">Analysis failed</p>
            <p className="text-red-600/80 text-sm">{analysisError}</p>
            <Link
              href="/analyse"
              className="inline-flex items-center gap-1.5 mt-3 text-sm font-semibold text-red-600 underline underline-offset-2"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Try again with a new photo
            </Link>
          </div>
        ) : (
          <>
            {/* ── Results hero ────────────────────────────────────── */}
            {isComplete && faceShape && (
              <div className="mt-6 mb-1">
                <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-1">
                  Your results
                </p>
                <div className="flex items-baseline gap-3 flex-wrap">
                  <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight">
                    {faceShapeLabel} face
                  </h1>
                  <div className="flex items-center gap-2 text-stone-400 text-sm">
                    {undertone && (
                      <span className="capitalize">{UNDERTONE_LABELS[undertone]} undertone</span>
                    )}
                    {sizeBand && (
                      <>
                        <span className="text-stone-200">·</span>
                        <span className="capitalize">{sizeBand} fit</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ── Analysis card ───────────────────────────────────── */}
            <AnalysisCard analysis={analysis} />

            {/* ── Frame catalogue with try-on ─────────────────────── */}
            {isComplete && (
              <TryOnCatalogueSection
                jobId={jobId}
                generationsRemaining={session?.generations_remaining ?? 3}
                onGenerationComplete={handleGenerationComplete}
              />
            )}
          </>
        )}
      </div>
    </main>
  )
}
