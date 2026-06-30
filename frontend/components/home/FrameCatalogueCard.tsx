'use client'

import { useState } from 'react'
import { ExternalLink } from 'lucide-react'
import type { CatalogueFrame } from '@/lib/types'

type Props = {
  frame: CatalogueFrame
}

const RETAILER_COLORS: Record<string, string> = {
  'Lenskart':     'bg-teal-50 text-teal-700',
  'Titan Eye+':   'bg-blue-50 text-blue-700',
  'John Jacobs':  'bg-purple-50 text-purple-700',
  'Rayban':       'bg-red-50 text-red-700',
  'Fastrack':     'bg-orange-50 text-orange-700',
}

export default function FrameCatalogueCard({ frame }: Props) {
  const retailerClass = RETAILER_COLORS[frame.retailer] || 'bg-stone-100 text-stone-600'
  const [imgFailed, setImgFailed] = useState(false)

  return (
    <div className="bg-white rounded-2xl border border-stone-100 overflow-hidden shadow-sm active:scale-[0.98] transition-transform">
      {/* Image */}
      <div className="relative bg-stone-50 aspect-square">
        {imgFailed ? (
          <div className="w-full h-full flex flex-col items-center justify-center gap-1.5 text-stone-300">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909M3.75 21h16.5M3 3l18 18" />
            </svg>
            <p className="text-xs capitalize text-stone-300">{frame.style}</p>
          </div>
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={frame.product_image_url}
            alt={frame.name}
            className="w-full h-full object-contain p-4"
            loading="lazy"
            onError={() => setImgFailed(true)}
          />
        )}
        <span className={`absolute top-2 left-2 text-xs font-semibold px-2 py-0.5 rounded-full ${retailerClass}`}>
          {frame.retailer}
        </span>
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-stone-900 font-semibold text-sm leading-tight line-clamp-1 mb-0.5">
          {frame.name}
        </p>
        <p className="text-stone-400 text-xs capitalize mb-2">
          {frame.style}{frame.colour ? ` · ${frame.colour}` : ''}
        </p>

        <div className="flex items-center justify-between">
          {frame.price_inr != null ? (
            <span className="text-stone-900 font-bold text-sm">
              ₹{frame.price_inr.toLocaleString('en-IN')}
            </span>
          ) : (
            <span className="text-stone-400 text-xs">Price unavailable</span>
          )}

          <a
            href={frame.buy_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={e => e.stopPropagation()}
            className="flex items-center gap-1 text-xs text-amber-600 font-semibold py-1 px-2 rounded-lg active:bg-amber-50 transition-colors"
          >
            View
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  )
}
