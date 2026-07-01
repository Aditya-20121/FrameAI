'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import CameraView from '@/components/camera/CameraView'
import UploadFallback from '@/components/camera/UploadFallback'
import QuoteLoader from '@/components/ui/QuoteLoader'
import { uploadPhoto } from '@/lib/api'

type Mode = 'camera' | 'upload'

export default function AnalysePage() {
  const router = useRouter()
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
        no_face_detected: "We couldn't find a face. Please use a clearer front-facing photo.",
        multiple_faces:   'We found more than one face. Please use a solo photo.',
        face_too_small:   'Your face is too small. Move closer to the camera.',
        resolution_too_low: 'Photo resolution is too low. Please use a clearer image.',
        image_too_blurry: 'Photo is too blurry. Try again in better lighting.',
      }
      setError(apiErr.error && friendly[apiErr.error]
        ? friendly[apiErr.error]
        : apiErr.message || 'Upload failed. Please try again.')
    }
  }

  return (
    <main className="relative flex flex-col h-[100dvh] bg-stone-900 overflow-hidden">
      {/* Dark header for camera screen */}
      <header className="flex items-center gap-3 px-4 py-3 z-10 flex-shrink-0">
        <Link href="/" className="text-stone-400 p-1 -ml-1 active:text-white transition-colors">
          <ArrowLeft className="w-5 h-5" />
        </Link>
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

      {uploading && (
        <div className="absolute inset-0 bg-stone-900/92 flex flex-col items-center justify-center z-50 px-6">
          <p className="text-white font-bold text-xl mb-1">Reading your face…</p>
          <QuoteLoader
            category="analysis"
            estimatedSeconds={5}
            dark
          />
        </div>
      )}

      {error && (
        <div className="absolute inset-x-4 bottom-6 p-4 bg-red-950/95 border border-red-700/60 rounded-2xl
                        text-red-300 text-sm z-50 shadow-xl">
          <p className="font-semibold mb-1">Upload failed</p>
          <p>{error}</p>
        </div>
      )}
    </main>
  )
}
