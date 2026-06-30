import type { AnalysisResponse } from '@/lib/types'
import QuoteLoader from '@/components/ui/QuoteLoader'

const SHAPE_LABELS: Record<string, string> = {
  oval: 'Oval', round: 'Round', square: 'Square',
  heart: 'Heart', diamond: 'Diamond', oblong: 'Oblong',
}
const UNDERTONE_LABELS: Record<string, string> = {
  warm: 'Warm', cool: 'Cool', neutral: 'Neutral',
}

type Props = { analysis: AnalysisResponse | null }

export default function AnalysisCard({ analysis }: Props) {
  const isLoading = !analysis || analysis.status === 'processing'

  if (isLoading) {
    return (
      <div className="mt-6 bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden">
        {/* Shimmer accent bar */}
        <div className="h-1 bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200 animate-pulse" />

        <div className="p-5">
          {/* Skeleton rows */}
          <div className="space-y-3 mb-4">
            <div className="h-5 bg-stone-100 rounded-lg animate-pulse w-2/5" />
            <div className="h-8 bg-stone-100 rounded-lg animate-pulse w-3/5" />
            <div className="h-4 bg-stone-100 rounded-lg animate-pulse w-full" />
            <div className="h-4 bg-stone-100 rounded-lg animate-pulse w-4/5" />
          </div>

          <div className="h-px bg-stone-100 my-4" />

          <div className="space-y-3">
            <div className="h-5 bg-stone-100 rounded-lg animate-pulse w-2/5" />
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-stone-100 animate-pulse flex-shrink-0" />
              <div className="h-7 bg-stone-100 rounded-lg animate-pulse w-24" />
            </div>
          </div>

          {/* Quote */}
          <div className="mt-4 pt-4 border-t border-stone-100">
            <QuoteLoader category="analysis" compact />
          </div>
        </div>
      </div>
    )
  }

  const { face_shape, face_shape_explanation, undertone, undertone_hex, ipd_mm, size_band } = analysis

  return (
    <div className="mt-6 bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden">
      {/* Top accent bar */}
      <div className="h-1 bg-gradient-to-r from-amber-400 to-amber-200" />

      <div className="p-5">
        <p className="text-xs font-semibold uppercase tracking-widest text-amber-500 mb-4">
          Your Face Analysis
        </p>

        <div className="space-y-5">
          {/* Face shape */}
          <div>
            <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">Face Shape</p>
            <p className="text-3xl font-extrabold text-stone-900 tracking-tight">
              {face_shape ? SHAPE_LABELS[face_shape] : '—'}
            </p>
            {face_shape_explanation && (
              <p className="text-stone-500 text-sm mt-2 leading-relaxed">
                {face_shape_explanation}
              </p>
            )}
          </div>

          <div className="h-px bg-stone-100" />

          {/* Undertone */}
          <div>
            <p className="text-xs text-stone-400 uppercase tracking-wider mb-2">Skin Undertone</p>
            <div className="flex items-center gap-3">
              {undertone_hex && (
                <div
                  className="w-10 h-10 rounded-full border-2 border-stone-100 shadow-sm flex-shrink-0"
                  style={{ backgroundColor: undertone_hex }}
                  title={undertone_hex}
                />
              )}
              <div>
                <p className="text-2xl font-bold text-stone-900">
                  {undertone ? UNDERTONE_LABELS[undertone] : '—'}
                </p>
                <p className="text-xs text-stone-400 mt-0.5">{undertone_hex}</p>
              </div>
            </div>
          </div>

          <div className="h-px bg-stone-100" />

          {/* IPD */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-stone-400 uppercase tracking-wider mb-1">IPD</p>
              <p className="text-2xl font-bold text-stone-900">
                {ipd_mm ? `${ipd_mm.toFixed(1)} mm` : '—'}
              </p>
            </div>
            {size_band && (
              <span className="bg-stone-100 text-stone-600 text-sm font-medium px-3 py-1.5 rounded-full capitalize">
                {size_band} fit
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
