'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, ShieldCheck } from 'lucide-react'
import CameraView from '@/components/camera/CameraView'
import UploadFallback from '@/components/camera/UploadFallback'
import QuoteLoader from '@/components/ui/QuoteLoader'
import { uploadPhoto } from '@/lib/api'
import { fadeUp, fadeUpSm, stagger } from '@/lib/motion'

type Mode = 'camera' | 'upload'

export default function AnalysePage() {
  const router = useRouter()
  const [consentGiven, setConsentGiven] = useState(false)
  const [termsChecked, setTermsChecked] = useState(false)
  const [mode, setMode] = useState<Mode>('camera')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handlePhoto(fileOrBlob: File | Blob) {
    setUploading(true)
    setError(null)
    try {
      const file =
        fileOrBlob instanceof File
          ? fileOrBlob
          : new File([fileOrBlob], 'selfie', { type: fileOrBlob.type || 'image/webp' })
      const result = await uploadPhoto(file)
      router.push(`/analysis/${result.job_id}`)
    } catch (err: unknown) {
      setUploading(false)
      const apiErr = err as { message?: string; error?: string }
      const friendly: Record<string, string> = {
        no_face_detected:   "We couldn't find a face. Please use a clearer front-facing photo.",
        multiple_faces:     'We found more than one face. Please use a solo photo.',
        face_too_small:     'Your face is too small. Move closer to the camera.',
        resolution_too_low: 'Photo resolution is too low. Please use a clearer image.',
        image_too_blurry:   'Photo is too blurry. Try again in better lighting.',
      }
      setError(apiErr.error && friendly[apiErr.error]
        ? friendly[apiErr.error]
        : apiErr.message || 'Upload failed. Please try again.')
    }
  }

  // ── Consent gate — shown before camera access ─────────────────────────────
  if (!consentGiven) {
    return (
      <main className="flex flex-col min-h-[100dvh] bg-stone-50 overflow-y-auto">
        <header className="flex items-center gap-3 px-4 py-3.5 bg-white border-b border-stone-100">
          <Link href="/" className="text-stone-400 p-1 -ml-1 hover:text-stone-700 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-1.5">
            <div className="w-6 h-6 bg-amber-500 rounded-md flex items-center justify-center flex-shrink-0">
              <span className="text-white text-[10px] font-black">F</span>
            </div>
            <span className="text-stone-900 font-bold">FrameAI</span>
          </div>
        </header>

        <div className="flex-1 flex flex-col px-5 py-8 max-w-md mx-auto w-full">

          {/* Icon + heading */}
          <motion.div initial="hidden" animate="show" variants={stagger(0.07)}>
            <motion.div
              variants={fadeUp}
              className="w-14 h-14 bg-amber-50 border-2 border-amber-200 rounded-2xl flex items-center justify-center mb-5"
            >
              <ShieldCheck className="w-7 h-7 text-amber-500" strokeWidth={1.8} />
            </motion.div>

            <motion.p variants={fadeUpSm} className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-1">
              Before we start
            </motion.p>
            <motion.h1 variants={fadeUp} className="text-2xl font-extrabold text-stone-900 tracking-tight mb-2 text-balance">
              Your data, explained simply
            </motion.h1>
            <motion.p variants={fadeUp} className="text-stone-500 text-sm leading-relaxed mb-6">
              FrameAI uses your selfie to analyse your face shape and skin tone.
              Under Indian law, we need your explicit consent before processing biometric data.
            </motion.p>

            {/* What we collect */}
            <motion.div variants={fadeUp} className="space-y-2 mb-6">
              {[
                {
                  icon: '📸',
                  title: 'Your selfie',
                  detail: 'Sent to our AI for face analysis. Deleted from servers in 24 hours.',
                },
                {
                  icon: '🤖',
                  title: 'Face measurements',
                  detail: 'Shape, undertone, jawline — stored anonymously to recommend frames.',
                },
                {
                  icon: '✨',
                  title: 'Try-on images',
                  detail: 'AI try-on generation is temporarily paused — face analysis and recommendations are fully available.',
                },
              ].map(({ icon, title, detail }) => (
                <div key={title} className="flex gap-3 bg-white border border-stone-100 rounded-xl p-3.5">
                  <span className="text-xl flex-shrink-0 leading-none mt-0.5">{icon}</span>
                  <div>
                    <p className="text-stone-800 font-semibold text-sm">{title}</p>
                    <p className="text-stone-400 text-xs leading-snug mt-0.5">{detail}</p>
                  </div>
                </div>
              ))}
            </motion.div>

            {/* What we DON'T do */}
            <motion.div variants={fadeUp} className="bg-stone-50 border border-stone-100 rounded-xl px-4 py-3 mb-6">
              <p className="text-stone-500 text-xs leading-relaxed">
                We <strong className="text-stone-700">do not</strong> share your photo with advertisers,
                build a profile on you, or link your face to any identity. No account required.
              </p>
            </motion.div>

            {/* Checkbox */}
            <motion.label variants={fadeUp} className="flex items-start gap-3 cursor-pointer group">
              <div className="relative flex-shrink-0 mt-0.5">
                <input
                  type="checkbox"
                  checked={termsChecked}
                  onChange={e => setTermsChecked(e.target.checked)}
                  className="sr-only"
                />
                <motion.div
                  animate={{ scale: termsChecked ? [1, 1.15, 1] : 1 }}
                  transition={{ duration: 0.25, ease: 'easeOut' }}
                  className={`w-5 h-5 rounded-md border-2 flex items-center justify-center
                    ${termsChecked
                      ? 'bg-amber-500 border-amber-500'
                      : 'bg-white border-stone-300 group-hover:border-amber-400'
                    }`}
                >
                  {termsChecked && (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 12 12" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2 6l3 3 5-5" />
                    </svg>
                  )}
                </motion.div>
              </div>
              <p className="text-stone-600 text-sm leading-relaxed">
                I have read and agree to the{' '}
                <Link
                  href="/terms"
                  target="_blank"
                  className="text-amber-500 underline underline-offset-2 font-semibold"
                  onClick={e => e.stopPropagation()}
                >
                  Terms &amp; Conditions
                </Link>{' '}
                and{' '}
                <Link
                  href="/privacy"
                  target="_blank"
                  className="text-amber-500 underline underline-offset-2 font-semibold"
                  onClick={e => e.stopPropagation()}
                >
                  Privacy Policy
                </Link>
                , and I consent to FrameAI processing my facial photograph for frame recommendations.
              </p>
            </motion.label>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="pt-6 mt-auto"
          >
            <motion.button
              whileTap={termsChecked ? { scale: 0.98 } : {}}
              disabled={!termsChecked}
              onClick={() => setConsentGiven(true)}
              className={`w-full py-4 rounded-2xl font-bold text-base transition-colors min-h-[56px]
                ${termsChecked
                  ? 'bg-amber-500 text-white shadow-lg shadow-amber-200 hover:bg-amber-400'
                  : 'bg-stone-100 text-stone-400 cursor-not-allowed'
                }`}
            >
              Continue to camera
            </motion.button>
            <p className="text-center text-stone-400 text-xs mt-3">
              You must accept to proceed. Your consent is logged per session.
            </p>
          </motion.div>
        </div>
      </main>
    )
  }

  // ── Camera / upload flow ──────────────────────────────────────────────────
  return (
    <main className="relative flex flex-col h-[100dvh] bg-stone-900 overflow-hidden">
      <header className="flex items-center gap-3 px-4 py-3 z-10 flex-shrink-0">
        <button
          onClick={() => setConsentGiven(false)}
          className="text-stone-400 p-1 -ml-1 active:text-white transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-1.5">
          <div className="w-6 h-6 bg-amber-500 rounded-md flex items-center justify-center flex-shrink-0">
            <span className="text-white text-[10px] font-black">F</span>
          </div>
          <span className="text-white font-bold">FrameAI</span>
        </div>
        {mode === 'camera' && (
          <button
            onClick={() => setMode('upload')}
            className="ml-auto text-stone-400 text-sm"
          >
            Upload instead
          </button>
        )}
      </header>

      <div className="flex-1 flex flex-col">
        {mode === 'camera' ? (
          <CameraView
            onCapture={handlePhoto}
            onSwitchToUpload={() => setMode('upload')}
            onNoCameraAvailable={() => setMode('upload')}
            disabled={uploading}
          />
        ) : (
          <div className="flex-1 bg-stone-50">
            <UploadFallback
              onUpload={handlePhoto}
              onSwitchToCamera={() => setMode('camera')}
              disabled={uploading}
            />
          </div>
        )}
      </div>

      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-stone-900/92 flex flex-col items-center justify-center z-50 px-6"
          >
            <p className="text-white font-bold text-xl mb-1">Reading your face…</p>
            <QuoteLoader category="analysis" estimatedSeconds={5} dark />
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute inset-x-4 bottom-6 p-4 bg-red-950/95 border border-red-700/60 rounded-2xl
                        text-red-300 text-sm z-50 shadow-xl"
          >
            <p className="font-semibold mb-1">Upload failed</p>
            <p>{error}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  )
}
