'use client'

import { useState, useRef } from 'react'
import { ExternalLink, ShoppingBag } from 'lucide-react'
import type { Frame } from '@/lib/types'
import { postGenerate, getGenerateStatus } from '@/lib/api'
import GenerationModal from './GenerationModal'
import QuoteLoader from '@/components/ui/QuoteLoader'

type GenStatus = 'idle' | 'generating' | 'complete' | 'failed'

type Props = {
  frame: Frame
  jobId: string
  generationsRemaining: number
  onComplete: (newRemaining: number) => void
}

export default function FrameCard({ frame, jobId, generationsRemaining, onComplete }: Props) {
  const [status, setStatus]       = useState<GenStatus>('idle')
  const [imageUrl, setImageUrl]   = useState<string | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const [imgFailed, setImgFailed] = useState(false)
  const remainingAtClick          = useRef(generationsRemaining)

  async function startGeneration() {
    remainingAtClick.current = generationsRemaining
    setStatus('generating')
    setError(null)
    try {
      const res = await postGenerate(jobId, frame.frame_id)
      await pollStatus(res.task_id)
      onComplete(remainingAtClick.current - 1)
    } catch (err: unknown) {
      const apiErr = err as { error?: string; message?: string }
      if (apiErr.error === 'generation_limit_reached') {
        setStatus('idle')
        onComplete(0)
      } else {
        setStatus('failed')
        setError(apiErr.message || 'Generation failed. This try was not counted — you can retry.')
      }
    }
  }

  async function pollStatus(taskId: string): Promise<void> {
    const start = Date.now()
    while (Date.now() - start < 90_000) {
      await new Promise(r => setTimeout(r, 2500))
      const res = await getGenerateStatus(taskId)
      if (res.status === 'complete' && res.image_url) {
        setImageUrl(res.image_url)
        setStatus('complete')
        return
      }
      if (res.status === 'failed') {
        throw { message: res.message || 'Generation failed. This try was not counted — you can retry.' }
      }
    }
    throw { message: 'Generation timed out. This try was not counted — you can retry.' }
  }

  const canTryOn     = generationsRemaining > 0 && (status === 'idle' || status === 'failed')
  const isGenerating = status === 'generating'

  const RETAILER_COLORS: Record<string, string> = {
    'Lenskart':    'bg-teal-50 text-teal-700',
    'Titan Eye+':  'bg-blue-50 text-blue-700',
    'John Jacobs': 'bg-purple-50 text-purple-700',
    'Rayban':      'bg-red-50 text-red-700',
  }
  const retailerClass = RETAILER_COLORS[frame.retailer] || 'bg-stone-100 text-stone-500'

  return (
    <div className="bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden">

      {/* ── Image ────────────────────────────────────────────────── */}
      <div className="relative bg-stone-50 w-full aspect-square">
        {imgFailed && !imageUrl ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-stone-300">
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5M3 3l18 18" />
            </svg>
            <p className="text-xs capitalize">{frame.style}</p>
          </div>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={imageUrl ?? frame.product_image_url}
            alt={frame.name}
            className={`w-full h-full transition-all duration-500 ${
              imageUrl ? 'object-cover animate-fade-in' : 'object-contain p-6'
            }`}
            onError={() => setImgFailed(true)}
          />
        )}

        {/* Top-left: rank */}
        <div className="absolute top-2.5 left-2.5">
          <span className="bg-stone-900/70 backdrop-blur-sm text-white text-xs font-bold px-2 py-0.5 rounded-full">
            #{frame.rank}
          </span>
        </div>

        {/* Top-right: match % badge */}
        <div className="absolute top-2.5 right-2.5">
          <span className="bg-amber-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
            {Math.round(frame.score)}% match
          </span>
        </div>

        {/* Generation overlay */}
        {isGenerating && (
          <div className="absolute inset-0 bg-white/90 backdrop-blur-sm flex items-center justify-center">
            <QuoteLoader category="tryon" estimatedSeconds={20} />
          </div>
        )}

        {/* Try-on complete overlay badge */}
        {status === 'complete' && imageUrl && (
          <div className="absolute bottom-2.5 left-2.5 bg-green-500 text-white text-xs font-bold px-2.5 py-1 rounded-full">
            AI Try-On
          </div>
        )}
      </div>

      {/* ── Info ─────────────────────────────────────────────────── */}
      <div className="p-4">

        {/* Name + price */}
        <div className="flex items-start justify-between gap-2 mb-1">
          <p className="text-stone-900 font-semibold text-sm leading-snug flex-1">{frame.name}</p>
          {frame.price_inr != null && (
            <span className="text-stone-900 font-bold text-sm flex-shrink-0">
              ₹{frame.price_inr.toLocaleString('en-IN')}
            </span>
          )}
        </div>

        {/* Style · colour · material */}
        <p className="text-stone-400 text-xs mb-1.5 capitalize">
          {[frame.style, frame.colour, frame.material].filter(Boolean).join(' · ')}
        </p>

        {/* Retailer pill */}
        <span className={`inline-block text-[10px] font-semibold px-2 py-0.5 rounded-full mb-3 ${retailerClass}`}>
          {frame.retailer}
        </span>

        {/* Why this frame */}
        {frame.explanation && (
          <p className="text-stone-500 text-xs leading-relaxed line-clamp-2 mb-3">
            {frame.explanation}
          </p>
        )}

        {/* Error */}
        {error && (
          <p className="text-red-500 text-xs mb-3 leading-relaxed">{error}</p>
        )}

        {/* CTA row */}
        <div className="flex gap-2">
          <button
            onClick={() => canTryOn && setShowConfirm(true)}
            disabled={!canTryOn || isGenerating}
            className={`flex-1 py-3 rounded-xl text-sm font-bold transition-all active:scale-[0.97]
              ${canTryOn && !isGenerating
                ? 'bg-amber-500 text-white shadow-md shadow-amber-100'
                : status === 'complete'
                  ? 'bg-green-50 border border-green-200 text-green-600 cursor-default'
                  : 'bg-stone-100 text-stone-400 cursor-not-allowed'
              }`}
          >
            {isGenerating
              ? 'Generating…'
              : status === 'complete'
                ? 'Try-on complete'
                : status === 'failed'
                  ? 'Retry'
                  : generationsRemaining === 0
                    ? 'No tries left'
                    : 'Try this on'}
          </button>

          <a
            href={frame.buy_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-4 py-3 rounded-xl border border-stone-200 text-stone-600 text-sm font-medium active:bg-stone-50 transition-colors"
            title={`Buy at ${frame.retailer}`}
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            <ExternalLink className="w-3 h-3 text-stone-300" />
          </a>
        </div>
      </div>

      {showConfirm && (
        <GenerationModal
          frame={frame}
          generationsRemaining={generationsRemaining}
          onClose={() => setShowConfirm(false)}
          onConfirm={() => {
            setShowConfirm(false)
            startGeneration()
          }}
        />
      )}
    </div>
  )
}
