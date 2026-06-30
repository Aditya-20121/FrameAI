'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { getAnalysis, getRecommendations, getSession } from '@/lib/api'
import type { AnalysisResponse, RecommendationsResponse, SessionResponse } from '@/lib/types'
import AnalysisCard from '@/components/analysis/AnalysisCard'
import FrameGrid from '@/components/frames/FrameGrid'

export default function AnalysisPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.jobId as string

  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null)
  const [session, setSession] = useState<SessionResponse | null>(null)
  const [recsError, setRecsError] = useState<string | null>(null)
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
            const [recs, sess] = await Promise.all([
              getRecommendations(jobId),
              getSession(),
            ])
            if (!cancelled) {
              setRecommendations(recs)
              setSession(sess)
            }
          } catch {
            if (!cancelled) setRecsError('Could not load recommendations. Please refresh.')
          }
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

  return (
    <main className="min-h-screen bg-stone-50">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-white border-b border-stone-100">
        <div className="max-w-2xl mx-auto flex items-center gap-3 px-4 py-3">
          <button
            onClick={() => router.push('/')}
            className="text-stone-400 hover:text-stone-700 transition-colors p-1 -ml-1"
            aria-label="Back to home"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <span className="text-stone-900 font-bold text-lg">FrameAI</span>
          {session && (
            <span className="ml-auto text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full">
              {session.generations_remaining} tr{session.generations_remaining === 1 ? 'y' : 'ies'} left
            </span>
          )}
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 pb-28 sm:pb-12">
        {analysisError ? (
          <div className="mt-8 p-5 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-sm">
            <p className="font-semibold mb-1">Analysis failed</p>
            <p>{analysisError}</p>
            <Link href="/analyse" className="block mt-3 text-red-600 underline underline-offset-2 text-xs font-medium">
              Try again with a new photo →
            </Link>
          </div>
        ) : (
          <>
            <AnalysisCard analysis={analysis} />

            {recsError && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm">
                {recsError}
              </div>
            )}

            {recommendations && session && (
              <FrameGrid
                frames={recommendations.frames}
                jobId={jobId}
                generationsRemaining={session.generations_remaining}
                onGenerationComplete={handleGenerationComplete}
              />
            )}

            {analysis?.status === 'complete' && !recommendations && !recsError && (
              <div className="mt-6 flex items-center gap-3 text-stone-400 text-sm">
                <div className="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin flex-shrink-0" />
                Loading your frame recommendations…
              </div>
            )}
          </>
        )}
      </div>
    </main>
  )
}
