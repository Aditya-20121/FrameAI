'use client'

import type { AnalysisResponse, Jawline, Cheekbones, EyeSet, SkinDepth } from '@/lib/types'
import { deriveStyleGuide } from '@/lib/styleGuide'
import QuoteLoader from '@/components/ui/QuoteLoader'

// ── Display label maps ────────────────────────────────────────────────────────

const SHAPE_LABELS: Record<string, string> = {
  oval: 'Oval', round: 'Round', square: 'Square',
  heart: 'Heart', diamond: 'Diamond', oblong: 'Oblong',
}
const UNDERTONE_SUBTITLES: Record<string, string> = {
  warm:    'golden & peachy tones',
  cool:    'pink & rosy tones',
  neutral: 'balanced — warm and cool mix',
}
const JAWLINE_LABELS: Record<Jawline, string>      = { angular: 'Angular', soft: 'Soft', tapered: 'Tapered' }
const CHEEKBONE_LABELS: Record<Cheekbones, string> = { high: 'High', normal: 'Normal', low: 'Low' }
const EYE_SET_LABELS: Record<EyeSet, string>       = { close: 'Close-set', average: 'Average', wide: 'Wide-set' }
const SKIN_DEPTH_LABELS: Record<SkinDepth, string> = { fair: 'Fair', light: 'Light', medium: 'Medium', olive: 'Olive', deep: 'Deep' }

// ── Small reusable pieces ─────────────────────────────────────────────────────

function Divider() {
  return <div className="h-px bg-stone-100" />
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <p className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mb-3">{children}</p>
}

function Pill({ label, tone = 'stone' }: { label: string; tone?: 'stone' | 'amber' | 'blue' | 'rose' | 'red' }) {
  const colors = {
    stone: 'bg-stone-100 text-stone-600',
    amber: 'bg-amber-50  text-amber-700',
    blue:  'bg-blue-50   text-blue-700',
    rose:  'bg-rose-50   text-rose-700',
    red:   'bg-red-50    text-red-500',
  }
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${colors[tone]}`}>
      {label}
    </span>
  )
}

function FeatureRow({ label, value, tone }: { label: string; value: string; tone?: 'stone' | 'amber' | 'blue' | 'rose' }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-stone-50 last:border-0">
      <span className="text-stone-400 text-sm">{label}</span>
      <Pill label={value} tone={tone} />
    </div>
  )
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="mt-6 bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden">
      <div className="h-1 bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200 animate-pulse" />
      <div className="p-5 space-y-4">
        <div className="h-3.5 bg-stone-100 rounded animate-pulse w-1/3" />
        <div className="h-9   bg-stone-100 rounded-lg animate-pulse w-2/5" />
        <div className="h-3.5 bg-stone-100 rounded animate-pulse w-full" />
        <div className="h-3.5 bg-stone-100 rounded animate-pulse w-4/5" />
        <div className="h-px bg-stone-100" />
        <div className="h-3.5 bg-stone-100 rounded animate-pulse w-1/3" />
        <div className="flex gap-2">
          <div className="h-8 w-24 bg-stone-100 rounded-full animate-pulse" />
          <div className="h-8 w-20 bg-stone-100 rounded-full animate-pulse" />
          <div className="h-8 w-16 bg-stone-100 rounded-full animate-pulse" />
        </div>
        <div className="h-px bg-stone-100" />
        <div className="flex gap-3 items-center">
          <div className="w-10 h-10 rounded-full bg-stone-100 animate-pulse" />
          <div className="flex gap-2">
            <div className="h-7 w-20 bg-stone-100 rounded-full animate-pulse" />
            <div className="h-7 w-20 bg-stone-100 rounded-full animate-pulse" />
            <div className="h-7 w-20 bg-stone-100 rounded-full animate-pulse" />
          </div>
        </div>
        <div className="h-px bg-stone-100" />
        <div className="h-3.5 bg-stone-100 rounded animate-pulse w-1/3" />
        <div className="h-6 bg-stone-100 rounded animate-pulse w-3/5" />
        <div className="pt-3 border-t border-stone-100">
          <QuoteLoader category="analysis" compact />
        </div>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

type Props = { analysis: AnalysisResponse | null }

export default function AnalysisCard({ analysis }: Props) {
  const isLoading = !analysis || analysis.status === 'processing'
  if (isLoading) return <LoadingSkeleton />

  const {
    face_shape, face_shape_confidence, face_shape_explanation,
    jawline, cheekbones, eye_set,
    undertone, undertone_hex, skin_depth,
    size_band,
  } = analysis

  const guide = deriveStyleGuide(analysis)
  const confPct = face_shape_confidence ? Math.round(face_shape_confidence * 100) : null
  const hasFeatures = jawline || cheekbones || eye_set

  return (
    <div className="mt-6 bg-white rounded-2xl border border-stone-100 shadow-sm overflow-hidden">
      {/* Accent bar */}
      <div className="h-1 bg-gradient-to-r from-amber-400 to-amber-200" />

      <div className="p-5 space-y-5">

        {/* Section header */}
        <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500">
          Your Face Analysis
        </p>

        {/* ── 1. FACE SHAPE ─────────────────────────────────────── */}
        <div>
          <SectionTitle>Face Shape</SectionTitle>

          <div className="flex items-baseline justify-between mb-2">
            <p className="text-3xl font-extrabold text-stone-900 tracking-tight">
              {face_shape ? SHAPE_LABELS[face_shape] : '—'}
            </p>
            {confPct !== null && (
              <span className="text-xs text-stone-400 font-medium">{confPct}% confidence</span>
            )}
          </div>

          {face_shape_explanation && (
            <p className="text-stone-500 text-sm leading-relaxed mb-4">
              {face_shape_explanation}
            </p>
          )}

          {/* Best styles for this face shape */}
          {guide && guide.bestStyles.length > 0 && (
            <div className="bg-stone-50 rounded-xl p-3.5">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-2.5">
                Best frame styles for you
              </p>
              <div className="flex flex-wrap gap-1.5 mb-2.5">
                {guide.bestStyles.map(s => (
                  <div key={s.slug} className="flex flex-col items-center gap-0.5">
                    <span className="bg-amber-500 text-white text-xs font-bold px-3 py-1.5 rounded-full">
                      {s.name}
                    </span>
                    <span className="text-[9px] text-stone-400 text-center leading-tight px-1">{s.why}</span>
                  </div>
                ))}
              </div>
              {guide.avoidStyles.length > 0 && (
                <p className="text-[10px] text-stone-400 mt-1">
                  Avoid: <span className="text-stone-500 font-medium">{guide.avoidStyles.join(', ')}</span>
                </p>
              )}
              {guide.styleNote && (
                <p className="text-[10px] text-amber-600 font-medium mt-1.5 leading-snug">
                  ↳ {guide.styleNote}
                </p>
              )}
            </div>
          )}
        </div>

        {/* ── 2. FACIAL FEATURES ────────────────────────────────── */}
        {hasFeatures && (
          <>
            <Divider />
            <div>
              <SectionTitle>Facial Features</SectionTitle>
              <div className="divide-y divide-stone-50">
                {jawline && (
                  <FeatureRow label="Jawline" value={JAWLINE_LABELS[jawline]} tone="stone" />
                )}
                {cheekbones && (
                  <FeatureRow label="Cheekbones" value={CHEEKBONE_LABELS[cheekbones]} tone={cheekbones === 'high' ? 'amber' : 'stone'} />
                )}
                {eye_set && (
                  <FeatureRow label="Eye spacing" value={EYE_SET_LABELS[eye_set]} tone="stone" />
                )}
              </div>
            </div>
          </>
        )}

        {/* ── 3. SKIN TONE + COLOURS ────────────────────────────── */}
        {undertone && (
          <>
            <Divider />
            <div>
              <SectionTitle>Skin Tone</SectionTitle>

              {/* Undertone swatch row */}
              <div className="flex items-center gap-3 mb-4">
                {undertone_hex && (
                  <div
                    className="w-11 h-11 rounded-full border-2 border-stone-100 shadow-sm flex-shrink-0"
                    style={{ backgroundColor: undertone_hex }}
                    title={undertone_hex}
                  />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <p className="text-lg font-bold text-stone-900 capitalize">{undertone}</p>
                    {skin_depth && (
                      <span className="text-xs font-medium text-stone-400 capitalize">
                        · {SKIN_DEPTH_LABELS[skin_depth]}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-stone-400 leading-snug">{UNDERTONE_SUBTITLES[undertone]}</p>
                  {undertone_hex && (
                    <p className="text-[10px] text-stone-300 font-mono mt-0.5">{undertone_hex}</p>
                  )}
                </div>
              </div>

              {/* Colour swatches */}
              {guide && guide.bestColours.length > 0 && (
                <div className="bg-stone-50 rounded-xl p-3.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-2.5">
                    Best frame colours for you
                  </p>
                  <div className="flex gap-3 mb-2.5">
                    {guide.bestColours.map(c => (
                      <div key={c.name} className="flex flex-col items-center gap-1.5">
                        <div
                          className="w-9 h-9 rounded-full border-2 border-white shadow-md"
                          style={{ backgroundColor: c.hex }}
                          title={c.name}
                        />
                        <span className="text-[9px] text-stone-500 font-medium text-center leading-tight">
                          {c.name}
                        </span>
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] text-stone-500 leading-snug">{guide.colourNote}</p>
                  {guide.avoidColours.length > 0 && (
                    <p className="text-[10px] text-stone-400 mt-1">
                      Avoid: <span className="text-stone-500 font-medium">{guide.avoidColours.join(', ')}</span>
                    </p>
                  )}
                </div>
              )}
            </div>
          </>
        )}

        {/* ── 4. FRAME SIZE ─────────────────────────────────────── */}
        {size_band && (
          <>
            <Divider />
            <div>
              <SectionTitle>Frame Size</SectionTitle>

              <div className="flex items-start justify-between mb-3">
                <div />
                {guide && (
                  <span className="bg-stone-100 text-stone-600 text-sm font-semibold px-3 py-1.5 rounded-full">
                    {guide.sizeLabel}
                  </span>
                )}
              </div>

              {guide && (
                <div className="bg-stone-50 rounded-xl p-3.5 space-y-1.5">
                  <p className="text-sm font-semibold text-stone-700">
                    Look for {guide.sizeSpec}
                  </p>
                  <p className="text-[11px] text-stone-500 leading-relaxed">
                    {SIZE_FULL[size_band ?? 'standard']}
                  </p>
                  {guide.sizeNote && (
                    <p className="text-[10px] text-amber-600 font-medium mt-1 leading-snug">
                      ↳ {guide.sizeNote}
                    </p>
                  )}
                </div>
              )}
            </div>
          </>
        )}

      </div>
    </div>
  )
}

// ── Static helpers ────────────────────────────────────────────────────────────

const SIZE_FULL: Record<string, string> = {
  narrow:   'Look for frames tagged "S" or "XS", or a total frame width under 130mm.',
  standard: 'Standard fit — the majority of frames in any catalogue will suit you.',
  wide:     'Look for frames tagged "L" or "W", or a total frame width above 138mm.',
}
