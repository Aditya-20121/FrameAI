'use client'

import { useState, useRef } from 'react'
import { Upload, X, Camera } from 'lucide-react'

type Props = {
  onUpload: (file: File) => void
  onSwitchToCamera: () => void
  disabled: boolean
}

export default function UploadFallback({ onUpload, onSwitchToCamera, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)

  function handleFile(file: File) {
    setFileError(null)
    if (!file.type.startsWith('image/')) {
      setFileError('Please select a JPG, PNG, or WEBP image.')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setFileError('File is too large. Maximum size is 10 MB.')
      return
    }
    if (preview) URL.revokeObjectURL(preview)
    setSelectedFile(file)
    setPreview(URL.createObjectURL(file))
  }

  function clearFile() {
    setSelectedFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
    setFileError(null)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="flex-1 flex flex-col px-4 py-6">
      {/* Tips */}
      <div className="mb-6 p-4 bg-amber-50 border border-amber-100 rounded-2xl">
        <p className="text-amber-800 text-sm font-semibold mb-1">For best results:</p>
        <ul className="text-amber-700/80 text-xs space-y-0.5">
          <li>· Front-facing photo, face centred</li>
          <li>· Remove glasses, look straight ahead</li>
          <li>· Good lighting, no harsh shadows</li>
        </ul>
      </div>

      {!preview ? (
        <>
          {/* Drop zone */}
          <div
            onDrop={handleDrop}
            onDragOver={e => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onClick={() => inputRef.current?.click()}
            className={`flex-1 min-h-[260px] flex flex-col items-center justify-center gap-3
              border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-200
              ${isDragging
                ? 'border-amber-400 bg-amber-50'
                : 'border-stone-300 bg-stone-50 active:bg-stone-100'
              }`}
          >
            <div className="w-14 h-14 bg-white rounded-2xl border border-stone-200 shadow-sm flex items-center justify-center">
              <Upload className="w-6 h-6 text-stone-400" />
            </div>
            <div className="text-center">
              <p className="text-stone-700 text-sm font-semibold">Drop a photo here</p>
              <p className="text-stone-400 text-xs mt-1">or tap to browse</p>
            </div>
            <p className="text-stone-300 text-xs">JPG · PNG · WEBP · Max 10 MB</p>
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
          </div>

          {fileError && <p className="text-red-500 text-sm mt-3">{fileError}</p>}

          {/* Camera option */}
          <button
            onClick={onSwitchToCamera}
            className="mt-4 flex items-center justify-center gap-2 w-full py-3.5 border border-stone-200 rounded-xl text-stone-600 text-sm font-medium bg-white active:bg-stone-50 transition-colors"
          >
            <Camera className="w-4 h-4" />
            Use camera instead
          </button>
        </>
      ) : (
        <div className="flex-1 flex flex-col">
          {/* Preview */}
          <div className="relative flex-1 rounded-2xl overflow-hidden bg-stone-100 min-h-[300px]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={preview} alt="Preview" className="w-full h-full object-cover" />
            <button
              onClick={clearFile}
              className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-full p-2 shadow-md active:scale-90 transition-transform"
              aria-label="Remove photo"
            >
              <X className="w-4 h-4 text-stone-700" />
            </button>
          </div>

          <button
            onClick={() => selectedFile && onUpload(selectedFile)}
            disabled={disabled}
            className="mt-4 w-full py-4 bg-amber-500 text-white font-bold rounded-2xl text-base
                       active:scale-[0.98] transition-transform disabled:opacity-50 disabled:cursor-not-allowed
                       shadow-md shadow-amber-100"
          >
            {disabled ? 'Analysing…' : 'Analyse this photo →'}
          </button>
        </div>
      )}
    </div>
  )
}
