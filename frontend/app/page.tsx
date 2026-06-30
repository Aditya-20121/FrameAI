import Link from 'next/link'
import { Scan, Target, Sparkles, ArrowRight } from 'lucide-react'
import HowItWorks from '@/components/home/HowItWorks'
import CatalogueSection from '@/components/home/CatalogueSection'

const FEATURES = [
  {
    icon: Scan,
    title: 'Face Analysis',
    desc: 'Shape + undertone detected from a single selfie',
  },
  {
    icon: Target,
    title: 'Smart Match',
    desc: 'Every frame scored against your unique face',
  },
  {
    icon: Sparkles,
    title: 'AI Try-On',
    desc: 'Photorealistic — not AR plastic overlays',
  },
]

const SKIN_TONES = ['#C8956C', '#8B5E52', '#F5CBA7', '#D5A97A', '#6B3A2A']

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-stone-50">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-sm border-b border-stone-100">
        <div className="max-w-2xl mx-auto flex items-center justify-between px-4 py-3.5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-amber-500 rounded-lg flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-black">F</span>
            </div>
            <span className="text-stone-900 font-bold text-xl tracking-tight">FrameAI</span>
          </div>
          <Link
            href="/analyse"
            className="flex items-center gap-1.5 text-sm font-semibold bg-stone-900 text-white px-4 py-2 rounded-full active:scale-95 transition-transform"
          >
            Try free
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className="bg-white px-4 pt-10 pb-12 border-b border-stone-100">
        <div className="max-w-2xl mx-auto">

          <span className="inline-block text-xs font-bold uppercase tracking-widest text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full mb-5">
            AI-powered · Free to try
          </span>

          <h1 className="text-[2.75rem] sm:text-5xl font-extrabold text-stone-900 leading-[1.08] tracking-tight mb-5">
            Frames that are
            <br />
            <span className="text-amber-500">built for your face.</span>
          </h1>

          <p className="text-stone-500 text-base leading-relaxed mb-8 max-w-xs">
            One selfie. Face shape analysis, undertone detection, and
            recommendations scored for your features.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 mb-8">
            <Link
              href="/analyse"
              className="flex items-center justify-center gap-2 bg-amber-500 text-white font-bold text-base px-7 py-4 rounded-2xl active:scale-95 transition-transform shadow-lg shadow-amber-200"
            >
              Analyse My Face
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#catalogue"
              className="flex items-center justify-center gap-2 bg-white text-stone-700 font-semibold text-base px-6 py-4 rounded-2xl border border-stone-200 active:scale-95 transition-transform"
            >
              Browse frames
            </a>
          </div>

          {/* Skin tone inclusivity */}
          <div className="flex items-center gap-3">
            <div className="flex -space-x-1.5">
              {SKIN_TONES.map((c, i) => (
                <div
                  key={i}
                  className="w-7 h-7 rounded-full border-2 border-white shadow-sm"
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
            <p className="text-stone-400 text-xs">
              Works for <strong className="text-stone-600">all skin tones</strong> · Indian faces included
            </p>
          </div>
        </div>
      </section>

      {/* ── Feature pills ──────────────────────────────────────────── */}
      <section className="bg-stone-50 px-4 py-8 border-b border-stone-100">
        <div className="max-w-2xl mx-auto grid grid-cols-3 gap-3">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white rounded-2xl p-4 border border-stone-100 shadow-sm">
              <div className="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center mb-3">
                <Icon className="w-4.5 h-4.5 text-amber-500" strokeWidth={2} />
              </div>
              <p className="text-stone-900 font-semibold text-xs mb-1 leading-snug">{title}</p>
              <p className="text-stone-400 text-xs leading-snug">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────────────── */}
      <div className="max-w-2xl mx-auto w-full">
        <HowItWorks />
      </div>

      {/* ── Frame catalogue ────────────────────────────────────────── */}
      <div className="max-w-2xl mx-auto w-full">
        <CatalogueSection />
      </div>

      {/* ── Footer ─────────────────────────────────────────────────── */}
      <footer className="pb-28 sm:pb-8 mt-auto border-t border-stone-100 bg-white">
        <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-amber-500 rounded-md flex items-center justify-center">
              <span className="text-white text-[9px] font-black">F</span>
            </div>
            <span className="text-stone-900 font-bold text-sm">FrameAI</span>
          </div>
          <p className="text-stone-400 text-xs text-center">
            Frames sourced from Lenskart & John Jacobs India.
            Affiliate links keep this free.
          </p>
        </div>
      </footer>

      {/* ── Sticky mobile CTA ──────────────────────────────────────── */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden z-40">
        <div className="bg-white/95 backdrop-blur-sm border-t border-stone-100 px-4 pt-3 pb-5">
          <Link
            href="/analyse"
            className="flex items-center justify-center gap-2 w-full bg-amber-500 text-white font-bold text-base py-4 rounded-2xl active:scale-[0.98] transition-transform shadow-lg shadow-amber-200"
          >
            Analyse My Face — Free
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

    </div>
  )
}
