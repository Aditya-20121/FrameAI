import { Camera, Brain, Shirt } from 'lucide-react'

const STEPS = [
  {
    icon: Camera,
    step: '01',
    title: 'Take a selfie',
    desc: 'Use your camera or upload any front-facing photo. Our oval guide ensures the perfect angle — one shot is all it takes.',
  },
  {
    icon: Brain,
    step: '02',
    title: 'Get your analysis',
    desc: 'AI detects your face shape, jawline, undertone, and skin depth — all in seconds, with no manual input.',
  },
  {
    icon: Shirt,
    step: '03',
    title: 'Try frames on',
    desc: 'See your top-matched frames on your actual face. Photorealistic AI compositing — not the plastic AR overlays you\'re used to.',
  },
]

export default function HowItWorks() {
  return (
    <section className="px-4 py-12 bg-white border-y border-stone-100">

      <div className="text-center mb-10">
        <p className="text-xs font-bold uppercase tracking-widest text-amber-600 mb-2">
          How it works
        </p>
        <h2 className="text-2xl font-extrabold text-stone-900 tracking-tight">
          From selfie to your{' '}
          <span className="font-display italic text-amber-500">perfect frame</span>
        </h2>
      </div>

      <div className="flex flex-col gap-0 max-w-2xl mx-auto">
        {STEPS.map(({ icon: Icon, step, title, desc }, i) => (
          <div key={step} className="flex gap-5">
            {/* Icon + connector line */}
            <div className="flex flex-col items-center flex-shrink-0">
              <div className="relative w-11 h-11 rounded-2xl bg-amber-50 border-2 border-amber-200 flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5 text-amber-500" strokeWidth={2} />
                {/* Step number badge */}
                <span className="absolute -top-2 -right-2 w-[18px] h-[18px] bg-amber-500 text-white text-[8px] font-black rounded-full flex items-center justify-center leading-none shadow-sm">
                  {i + 1}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="w-px flex-1 bg-gradient-to-b from-amber-200 via-amber-100 to-stone-100 my-2 min-h-[36px]" />
              )}
            </div>

            {/* Content */}
            <div className="pb-8 pt-0.5">
              <h3 className="text-stone-900 font-bold text-base mb-1">{title}</h3>
              <p className="text-stone-500 text-sm leading-relaxed">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
