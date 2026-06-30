'use client'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import type { Frame } from '@/lib/types'

type Props = {
  frame: Frame
  generationsRemaining: number
  onClose: () => void
  onConfirm: () => void
}

export default function GenerationModal({ frame, generationsRemaining, onClose, onConfirm }: Props) {
  const afterThis = generationsRemaining - 1

  return (
    <Dialog open onOpenChange={open => !open && onClose()}>
      <DialogContent className="bg-white border-stone-200 text-stone-900 max-w-sm mx-4 rounded-2xl shadow-xl">
        <DialogHeader>
          <DialogTitle className="text-stone-900 text-lg">Use 1 try?</DialogTitle>
        </DialogHeader>

        <div className="py-1 space-y-3">
          <p className="text-stone-500 text-sm leading-relaxed">
            Generate a photorealistic try-on for{' '}
            <span className="text-stone-900 font-semibold">{frame.name}</span>.
          </p>

          <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
            <div className="flex items-center justify-between">
              <p className="text-amber-700 font-semibold text-sm">
                {generationsRemaining} {generationsRemaining === 1 ? 'try' : 'tries'} remaining
              </p>
              <div className="flex gap-0.5">
                {[0, 1, 2].map(i => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full ${i < generationsRemaining ? 'bg-amber-400' : 'bg-stone-200'}`}
                  />
                ))}
              </div>
            </div>
            <p className="text-amber-600/70 text-xs mt-1">
              {afterThis <= 0 ? 'This is your last free try.' : `${afterThis} remaining after this.`}
            </p>
          </div>
        </div>

        <DialogFooter className="flex-row gap-2 pt-1">
          <Button
            variant="outline"
            onClick={onClose}
            className="flex-1 border-stone-200 text-stone-600 hover:bg-stone-50 rounded-xl h-12"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            className="flex-1 bg-amber-500 text-white hover:bg-amber-400 font-bold rounded-xl h-12 shadow-md shadow-amber-100"
          >
            Generate →
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
