import Link from 'next/link'
import HowItWorks from '@/components/home/HowItWorks'
import CatalogueSection from '@/components/home/CatalogueSection'

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-stone-50">
      {/* Sticky header */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-sm border-b border-stone-100">
        <div className="max-w-2xl mx-auto flex items-center justify-between px-4 py-3">
          <span className="text-stone-900 font-bold text-xl tracking-tight">FrameAI</span>
          <Link
            href="/analyse"
            className="text-sm font-semibold bg-stone-900 text-white px-4 py-2 rounded-full active:scale-95 transition-transform"
          >
            Analyse My Face
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-white px-4 pt-10 pb-12 border-b border-stone-100">
        <div className="max-w-2xl mx-auto">
          <span className="inline-block text-xs font-semibold uppercase tracking-widest text-amber-600 bg-amber-50 px-3 py-1 rounded-full mb-4">
            AI-powered · Free to try
          </span>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-stone-900 leading-[1.1] tracking-tight mb-4">
            Find frames that
            <br />
            <span className="text-amber-500">fit YOUR face.</span>
          </h1>

          <p className="text-stone-500 text-base leading-relaxed mb-8 max-w-sm">
            AI face shape analysis + skin undertone detection + photorealistic try-on.
            400+ frames from Lenskart, Titan Eye+, John Jacobs & more.
          </p>

          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              href="/analyse"
              className="flex items-center justify-center gap-2 bg-amber-500 text-white font-bold text-base px-6 py-4 rounded-2xl active:scale-95 transition-transform shadow-md shadow-amber-100"
            >
              <span>📸</span>
              Analyse My Face
            </Link>
            <a
              href="#catalogue"
              className="flex items-center justify-center gap-2 bg-white text-stone-800 font-semibold text-base px-6 py-4 rounded-2xl border border-stone-200 active:scale-95 transition-transform"
            >
              Browse Frames ↓
            </a>
          </div>

          {/* Trust signals */}
          <div className="flex items-center gap-4 mt-6">
            <div className="flex -space-x-1">
              {['#C8956C', '#8B5E52', '#F5CBA7', '#D5A97A'].map((c, i) => (
                <div
                  key={i}
                  className="w-7 h-7 rounded-full border-2 border-white"
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

      {/* Feature cards */}
      <section className="bg-white px-4 py-8 border-b border-stone-100">
        <div className="max-w-2xl mx-auto grid grid-cols-3 gap-3">
          {[
            { icon: '🔍', title: 'Face Analysis', desc: 'Shape + undertone in seconds' },
            { icon: '🎯', title: 'Smart Match',   desc: 'Frames scored for your face' },
            { icon: '✨', title: 'Try On',        desc: 'Photorealistic, not AR plastic' },
          ].map(feat => (
            <div key={feat.title} className="bg-stone-50 rounded-2xl p-3 text-center border border-stone-100">
              <div className="text-2xl mb-2">{feat.icon}</div>
              <p className="text-stone-900 font-semibold text-xs mb-0.5">{feat.title}</p>
              <p className="text-stone-400 text-xs leading-snug">{feat.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <div className="max-w-2xl mx-auto w-full">
        <HowItWorks />
      </div>

      {/* Frame catalogue */}
      <div className="max-w-2xl mx-auto w-full">
        <CatalogueSection />
      </div>

      {/* Footer */}
      <footer className="pb-28 sm:pb-8 mt-4 border-t border-stone-100 bg-white px-4 py-6">
        <div className="max-w-2xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span className="text-stone-900 font-bold">FrameAI</span>
          <p className="text-stone-400 text-xs text-center">
            Frames sourced from Lenskart, Titan Eye+, John Jacobs & Rayban India.
            Affiliate links help us keep this free.
          </p>
        </div>
      </footer>

      {/* Sticky bottom CTA — mobile only */}
      <div className="fixed bottom-0 left-0 right-0 sm:hidden z-40 safe-bottom">
        <div className="bg-white border-t border-stone-100 px-4 pt-3 pb-4">
          <Link
            href="/analyse"
            className="flex items-center justify-center gap-2 w-full bg-amber-500 text-white font-bold text-base py-4 rounded-2xl active:scale-[0.98] transition-transform shadow-lg shadow-amber-100"
          >
            📸 Analyse My Face — Free
          </Link>
        </div>
      </div>
    </div>
  )
}
