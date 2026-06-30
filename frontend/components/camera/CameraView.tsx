'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import OvalGuide from './OvalGuide'
import { Camera } from 'lucide-react'

type Props = {
  onCapture: (blob: Blob) => void
  onSwitchToUpload: () => void
  onNoCameraAvailable: () => void
  disabled: boolean
}

export default function CameraView({ onCapture, onSwitchToUpload, onNoCameraAvailable, disabled }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const modelRef = useRef<unknown>(null)
  const detectionRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const alignedSinceRef = useRef<number | null>(null)
  const capturedRef = useRef(false)

  const [cameraError, setCameraError] = useState<string | null>(null)
  const [isAligned, setIsAligned] = useState(false)
  const [modelReady, setModelReady] = useState(false)
  const [countdown, setCountdown] = useState(0)

  // Load BlazeFace (non-blocking; camera works without it)
  useEffect(() => {
    let cancelled = false
    async function loadModel() {
      try {
        const tf = await import('@tensorflow/tfjs')
        await tf.ready()
        const blazeface = await import('@tensorflow-models/blazeface')
        const model = await blazeface.load()
        if (!cancelled) {
          modelRef.current = model
          setModelReady(true)
        }
      } catch {
        // Alignment guidance unavailable — camera still works
      }
    }
    loadModel()
    return () => { cancelled = true }
  }, [])

  // Start camera stream
  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        })
        streamRef.current = stream
        if (videoRef.current) videoRef.current.srcObject = stream
      } catch (err: unknown) {
        const e = err as { name?: string }
        if (e.name === 'NotAllowedError') {
          setCameraError('Camera access was denied. Allow camera access in your browser, or upload a photo.')
        } else if (e.name === 'NotFoundError') {
          onNoCameraAvailable()
        } else {
          setCameraError('Camera unavailable on this device.')
          onNoCameraAvailable()
        }
      }
    }
    startCamera()
    return () => {
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
      if (detectionRef.current) clearInterval(detectionRef.current)
    }
  }, [onNoCameraAvailable])

  // Face detection loop — only runs when model is ready
  useEffect(() => {
    if (!modelReady) return

    detectionRef.current = setInterval(async () => {
      const video = videoRef.current
      const model = modelRef.current as {
        estimateFaces: (v: HTMLVideoElement, b: boolean) => Promise<Array<{
          topLeft: [number, number]
          bottomRight: [number, number]
        }>>
      } | null

      if (!video || !model || video.readyState < 2 || capturedRef.current || disabled) return

      const preds = await model.estimateFaces(video, false)

      if (!preds || preds.length === 0) {
        setIsAligned(false)
        alignedSinceRef.current = null
        setCountdown(0)
        return
      }

      const vw = video.videoWidth
      const vh = video.videoHeight
      const ovalCx = vw * 0.5
      const ovalCy = vh * 0.5
      const ovalRx = vw * 0.28
      const ovalRy = vh * 0.38

      const face = preds[0]
      const [x1, y1] = face.topLeft
      const [x2, y2] = face.bottomRight
      const faceCx = (x1 + x2) / 2
      const faceCy = (y1 + y2) / 2
      const faceW = x2 - x1
      const faceH = y2 - y1

      const dx = (faceCx - ovalCx) / ovalRx
      const dy = (faceCy - ovalCy) / ovalRy
      const centered = dx * dx + dy * dy <= 1.1
      const sizeOk = faceW >= ovalRx * 1.1 && faceH >= ovalRy * 0.9
      const aligned = centered && sizeOk

      setIsAligned(aligned)

      if (aligned) {
        if (!alignedSinceRef.current) alignedSinceRef.current = Date.now()
        const elapsed = Date.now() - alignedSinceRef.current
        setCountdown(Math.min(100, (elapsed / 1500) * 100))
        if (elapsed >= 1500) capturePhoto()
      } else {
        alignedSinceRef.current = null
        setCountdown(0)
      }
    }, 120)

    return () => { if (detectionRef.current) clearInterval(detectionRef.current) }
  }, [modelReady, disabled])

  const capturePhoto = useCallback(() => {
    if (capturedRef.current || disabled) return
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    capturedRef.current = true
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')!.drawImage(video, 0, 0)
    canvas.toBlob(blob => { if (blob) onCapture(blob) }, 'image/webp', 0.92)
  }, [disabled, onCapture])

  if (cameraError) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 text-center gap-4">
        <div className="text-5xl">📷</div>
        <p className="text-neutral-300 text-sm leading-relaxed max-w-xs">{cameraError}</p>
        <button
          onClick={onSwitchToUpload}
          className="bg-amber-400 text-neutral-950 font-semibold px-6 py-3 rounded-full text-sm"
        >
          Upload a photo instead
        </button>
      </div>
    )
  }

  return (
    <div className="flex-1 relative flex flex-col overflow-hidden">
      {/* Instruction pill */}
      <div className="absolute top-3 left-0 right-0 flex justify-center z-10 pointer-events-none">
        <div className="bg-neutral-900/80 backdrop-blur-sm px-4 py-2 rounded-full border border-neutral-700/50">
          <p className="text-white text-sm text-center">
            Remove glasses · Look straight ahead · Relax your face
          </p>
        </div>
      </div>

      {/* Camera feed — mirrored so it feels like a mirror to the user */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
        style={{ transform: 'scaleX(-1)' }}
      />

      {/* Oval overlay */}
      <div className="absolute inset-0 pointer-events-none">
        <OvalGuide isAligned={isAligned} countdown={countdown} />
      </div>

      {/* Hold-still indicator */}
      {isAligned && countdown > 0 && (
        <div className="absolute bottom-36 left-0 right-0 flex justify-center z-10 pointer-events-none">
          <div className="bg-green-900/60 border border-green-600/60 backdrop-blur-sm px-4 py-1.5 rounded-full">
            <p className="text-green-400 text-sm font-medium">Hold still…</p>
          </div>
        </div>
      )}

      {/* Manual capture + upload link */}
      <div className="absolute bottom-6 left-0 right-0 flex flex-col items-center gap-3 z-10">
        <button
          onClick={capturePhoto}
          disabled={disabled}
          className="w-16 h-16 rounded-full bg-white border-4 border-neutral-300 flex items-center justify-center
                     shadow-lg active:scale-95 transition-transform disabled:opacity-40"
          aria-label="Take photo"
        >
          <Camera className="w-7 h-7 text-neutral-800" />
        </button>
        <button
          onClick={onSwitchToUpload}
          className="text-neutral-400 text-sm underline underline-offset-2"
        >
          Upload a photo instead
        </button>
      </div>

      <canvas ref={canvasRef} className="hidden" />
    </div>
  )
}
