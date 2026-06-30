import { Camera, Brain, Shirt } from 'lucide-react'

const STEPS = [
  {
    icon: Camera,
    step: '01',
    title: 'Take a selfie',
    desc: 'Use your camera or upload any front-facing photo. One shot is all it takes.',
  },
  {
    icon: Brain,
    step: '02',
    title: 'Get your analysis',
    desc: 'We detect your face shape, jawline, undertone, and skin depth — all in seconds.',
  },
  {
    icon: Shirt,
    step: '03',
    title: 'Try frames on',
    desc: 'See top-matched frames on your actual face. Photorealistic, not AR overlays.',
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
          From selfie to your perfect frame
        </h2>
      </div>

      <div className="flex flex-col gap-0 max-w-2xl mx-auto">
        {STEPS.map(({ icon: Icon, step, title, desc }, i) => (
          <div key={step} className="flex gap-5">
            {/* Left: number + connector line */}
            <div className="flex flex-col items-center flex-shrink-0">
              <div className="w-11 h-11 rounded-2xl bg-amber-50 border-2 border-amber-200 flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5 text-amber-500" strokeWidth={2} />
              </div>
              {i < STEPS.length - 1 && (
                <div className="w-px flex-1 bg-stone-100 my-2 min-h-[32px]" />
              )}
            </div>

            {/* Right: content */}
            <div className={`pb-8 ${i === STEPS.length - 1 ? '' : ''}`}>
              <span className="text-[10px] font-bold text-amber-400 tracking-widest uppercase">{step}</span>
              <h3 className="text-stone-900 font-bold text-base mt-0.5 mb-1">{title}</h3>
              <p className="text-stone-500 text-sm leading-relaxed">{desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
