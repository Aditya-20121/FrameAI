const STEPS = [
  {
    icon: '📸',
    title: 'Snap',
    desc: 'Take a quick selfie using your camera, or upload any front-facing photo',
  },
  {
    icon: '🎯',
    title: 'Analyse',
    desc: 'Our AI reads your face shape and skin undertone in seconds',
  },
  {
    icon: '✨',
    title: 'Try On',
    desc: 'See yourself wearing recommended frames — photorealistic, not plasticky',
  },
]

export default function HowItWorks() {
  return (
    <section className="px-4 py-12 bg-white border-y border-stone-100">
      <p className="text-xs font-semibold uppercase tracking-widest text-amber-600 text-center mb-2">
        How it works
      </p>
      <h2 className="text-2xl font-bold text-stone-900 text-center mb-8">
        Three steps to your perfect frame
      </h2>

      <div className="flex flex-col sm:flex-row gap-4 max-w-2xl mx-auto">
        {STEPS.map((step, i) => (
          <div key={step.title} className="flex-1 flex flex-col items-center text-center">
            {/* Step line connector */}
            <div className="flex items-center w-full mb-4 sm:flex-col sm:w-auto">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-2xl flex-shrink-0">
                {step.icon}
              </div>
              {i < STEPS.length - 1 && (
                <div className="flex-1 h-px bg-stone-200 mx-3 sm:hidden" />
              )}
            </div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xs font-bold text-amber-500 bg-amber-50 rounded-full px-2 py-0.5">
                {i + 1}
              </span>
              <p className="text-stone-900 font-semibold text-base">{step.title}</p>
            </div>
            <p className="text-stone-500 text-sm leading-relaxed">{step.desc}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
