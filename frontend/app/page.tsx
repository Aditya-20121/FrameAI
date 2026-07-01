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

const MARQUEE_ITEMS = [
  '6 Face Shapes Detected',
  'Warm · Cool · Neutral Undertones',
  '400+ Frame Styles',
  'AI Try-On — Photorealistic',
  'Results in Seconds',
  'No AR Overlays',
  'Indian Faces Included',
  '₹500 to ₹15,000',
]

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
            className="flex items-center gap-1.5 text-sm font-semibold bg-stone-900 text-white px-4 py-2 rounded-full active:scale-95 transition-transform hover:bg-stone-700"
          >
            Try free
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <section className="relative bg-white overflow-hidden px-4 pt-12 pb-14 border-b border-stone-100">

        {/* Decorative background blobs */}
        <div
          className="absolute -top-20 -right-20 w-72 h-72 rounded-full opacity-25 blur-3xl pointer-events-none animate-blob"
          style={{ background: 'radial-gradient(circle, #fbbf24 0%, #f59e0b 50%, transparent 70%)' }}
        />
        <div
          className="absolute bottom-0 -left-16 w-56 h-56 rounded-full opacity-10 blur-2xl pointer-events-none"
          style={{ background: 'radial-gradient(circle, #fed7aa 0%, transparent 70%)' }}
        />

        <div className="max-w-2xl mx-auto relative">

          <span
            className="inline-block text-xs font-bold uppercase tracking-widest text-amber-600 bg-amber-50 border border-amber-100 px-3 py-1.5 rounded-full mb-6 animate-fade-up"
            style={{ animationDelay: '0ms' }}
          >
            AI-powered · Free to try
          </span>

          <h1
            className="font-extrabold text-stone-900 leading-[1.1] tracking-tight mb-5 animate-fade-up"
            style={{ fontSize: 'clamp(2.4rem, 8vw, 3.2rem)', animationDelay: '70ms' }}
          >
            Frames that are
            <br />
            <span className="font-display italic text-amber-500">
              built for your face.
            </span>
          </h1>

          <p
            className="text-stone-500 text-base leading-relaxed mb-8 max-w-xs animate-fade-up"
            style={{ animationDelay: '140ms' }}
          >
            One selfie. Face shape analysis, undertone detection, and
            recommendations scored for your features.
          </p>

          <div
            className="flex flex-col sm:flex-row gap-3 mb-10 animate-fade-up"
            style={{ animationDelay: '210ms' }}
          >
            <Link
              href="/analyse"
              className="flex items-center justify-center gap-2 bg-amber-500 text-white font-bold text-base px-7 py-4 rounded-2xl active:scale-95 transition-all shadow-lg shadow-amber-200 hover:bg-amber-400 hover:shadow-amber-300 hover:-translate-y-0.5"
            >
              Analyse My Face
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#catalogue"
              className="flex items-center justify-center gap-2 bg-white text-stone-700 font-semibold text-base px-6 py-4 rounded-2xl border border-stone-200 active:scale-95 transition-all hover:border-stone-300 hover:shadow-sm hover:-translate-y-0.5"
            >
              Browse frames
            </a>
          </div>

          {/* Skin tone inclusivity */}
          <div
            className="flex items-center gap-3 animate-fade-up"
            style={{ animationDelay: '280ms' }}
          >
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

      {/* ── Marquee strip ──────────────────────────────────────────── */}
      <div className="bg-amber-500 overflow-hidden py-2.5">
        <div className="flex animate-marquee whitespace-nowrap">
          {[...MARQUEE_ITEMS, ...MARQUEE_ITEMS].map((item, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-4 px-6 text-white text-xs font-semibold tracking-wide"
            >
              {item}
              <span className="text-amber-200 text-sm select-none">✦</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── Feature cards ──────────────────────────────────────────── */}
      <section className="bg-stone-50 px-4 py-8 border-b border-stone-100">
        <div className="max-w-2xl mx-auto grid grid-cols-3 gap-3">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div
              key={title}
              className="group bg-white rounded-2xl p-4 border border-stone-100 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-default"
            >
              <div className="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center mb-3 group-hover:bg-amber-100 transition-colors">
                <Icon className="w-[18px] h-[18px] text-amber-500" strokeWidth={2} />
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
      <footer className="mt-auto border-t border-stone-100 bg-white">
        <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-amber-500 rounded-md flex items-center justify-center">
              <span className="text-white text-[9px] font-black">F</span>
            </div>
            <span className="text-stone-900 font-bold text-sm">FrameAI</span>
          </div>
          <div className="flex flex-col items-center gap-1.5 text-center">
            <p className="text-stone-400 text-xs">
              Frames sourced from Lenskart & John Jacobs India.
              Affiliate links keep this free.
            </p>
            <Link href="/privacy" className="text-stone-400 text-xs underline underline-offset-2 hover:text-stone-600 transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>
      </footer>

    </div>
  )
}
