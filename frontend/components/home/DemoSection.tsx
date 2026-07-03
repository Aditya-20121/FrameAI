'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import {
  motion,
  useMotionValue,
  useMotionTemplate,
  useSpring,
  useTransform,
  useReducedMotion,
  animate,
} from 'framer-motion'
import { EASE_OUT_EXPO } from '@/lib/motion'

/* ── Geometry ─────────────────────────────────────────────────────────────── */

const ORBIT_R    = 178   // px — radius of the orbit ring
const CARD_D     = 96    // px — orbit photo diameter
const CENTER_D   = 108   // px — center person circle diameter
const CONTAINER  = 460   // px — square canvas size
const ROTATE_SECS = 38   // one full revolution

/* ── Data — the 4 frames Aditya picked + 1 sunglasses pick ─────────────────── */

const FRAMES = [
  { label: 'Square · Clear',       dot: '#d1d5db', src: '/demo/tryon_1.jpg' },
  { label: 'Geometric · Brown',    dot: '#7c4f1e', src: '/demo/tryon_2.jpg' },
  { label: 'Browline · Tortoiseshell', dot: '#4a3728', src: '/demo/tryon_3.jpg' },
  { label: 'Rimless · Purple',     dot: '#7c3aed', src: '/demo/tryon_4.jpg' },
  { label: 'Aviator · Silver',     dot: '#9ca3af', src: '/demo/tryon_5.jpg' },
]

/* ── Orbit photo — position driven by a live motion value, not re-renders ──── */

function OrbitPhoto({
  frame,
  index,
  progress,
  entered,
  delay,
}: {
  frame: (typeof FRAMES)[number]
  index: number
  progress: ReturnType<typeof useMotionValue<number>>
  entered: boolean
  delay: number
}) {
  const baseAngle = index * (360 / FRAMES.length)
  const x = useTransform(progress, (p) => {
    const rad = ((p + baseAngle) * Math.PI) / 180
    return Math.cos(rad) * ORBIT_R
  })
  const y = useTransform(progress, (p) => {
    const rad = ((p + baseAngle) * Math.PI) / 180
    return Math.sin(rad) * ORBIT_R
  })
  // Combine the live orbit offset with a fixed -50%/-50% centering offset into
  // ONE transform string — mixing motion values with raw translateX/Y style
  // keys does not compose reliably, this is the supported way to do it.
  const transform = useMotionTemplate`translate(-50%, -50%) translate(${x}px, ${y}px)`

  return (
    <motion.div
      className="absolute group"
      style={{ width: CARD_D, height: CARD_D, top: '50%', left: '50%', transform }}
      initial={{ scale: 0, opacity: 0 }}
      animate={entered ? { scale: 1, opacity: 1 } : {}}
      transition={{ duration: 0.6, ease: [0.34, 1.56, 0.64, 1], delay }}
    >
      <motion.div
        whileHover={{ scale: 1.15, zIndex: 30 }}
        className="relative overflow-hidden rounded-full border-2 border-white/10 bg-stone-900 shadow-xl
                   transition-colors duration-300 group-hover:border-amber-400"
        style={{ width: CARD_D, height: CARD_D }}
      >
        <Image src={frame.src} alt={frame.label} fill sizes="96px" className="object-cover" />
        <div
          className="absolute bottom-1 right-1 h-3 w-3 rounded-full border-2 border-stone-900"
          style={{ background: frame.dot }}
        />
      </motion.div>
      <div className="pointer-events-none absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap
                      rounded-full bg-stone-800 px-2 py-0.5 text-[9px] font-medium text-stone-300
                      opacity-0 transition-opacity group-hover:opacity-100 z-40">
        {frame.label}
      </div>
    </motion.div>
  )
}

/* ── Component ────────────────────────────────────────────────────────────── */

export default function DemoSection() {
  const [entered, setEntered] = useState(false)
  const reduceMotion = useReducedMotion()
  const progress = useMotionValue(0)

  const rawTiltX = useMotionValue(0)
  const rawTiltY = useMotionValue(0)
  const tiltX = useSpring(rawTiltX, { stiffness: 100, damping: 20 })
  const tiltY = useSpring(rawTiltY, { stiffness: 100, damping: 20 })
  const rotateX = useTransform(tiltY, (v) => v * -10)
  const rotateY = useTransform(tiltX, (v) => v * 10)

  function handleEnter() {
    if (entered) return
    setEntered(true)
  }

  useEffect(() => {
    if (!entered) return
    // Slow, ambient rotation — kept even under prefers-reduced-motion since it's
    // gentle and continuous rather than a large/fast/disorienting effect; only
    // the mouse-follow tilt below is skipped for reduced-motion users.
    const controls = animate(progress, 360, {
      duration: ROTATE_SECS,
      repeat: Infinity,
      ease: 'linear',
    })
    return () => controls.stop()
  }, [entered, progress])

  function handleMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (reduceMotion) return
    const rect = e.currentTarget.getBoundingClientRect()
    rawTiltX.set((e.clientX - rect.left) / rect.width - 0.5)
    rawTiltY.set((e.clientY - rect.top) / rect.height - 0.5)
  }
  function handleMouseLeave() {
    rawTiltX.set(0)
    rawTiltY.set(0)
  }

  return (
    <motion.section
      onViewportEnter={handleEnter}
      viewport={{ once: true, amount: 0.3, margin: '0px 0px -80px 0px' }}
      className="relative overflow-hidden bg-stone-950 py-14 px-4 sm:py-16"
    >

      {/* Ambient amber glow behind the orbit */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-end pr-16">
        <div className="h-96 w-96 rounded-full bg-amber-500/8 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-5xl">
        <div className="flex flex-col items-center gap-10 lg:flex-row lg:items-center lg:gap-12">

          {/* ── Text column ───────────────────────────────────────────────── */}
          <motion.div
            className="flex-1 text-center lg:text-left"
            initial={{ opacity: 0, y: 20 }}
            animate={entered ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.5, ease: EASE_OUT_EXPO }}
          >
            <p className="mb-2 text-[10px] font-bold uppercase tracking-widest text-amber-500">
              Live demo
            </p>
            <h2 className="mb-4 text-3xl font-extrabold leading-tight tracking-tight text-white sm:text-4xl text-balance">
              See what AI try-on<br />
              <span className="font-display italic text-amber-500">actually looks like</span>
            </h2>
            <p className="mx-auto mb-8 max-w-xs text-base leading-relaxed text-stone-400 lg:mx-0 lg:max-w-sm">
              One selfie. Five frames. Photorealistic rendering — not AR stickers pasted over your face.
            </p>

            <motion.div whileTap={{ scale: 0.97 }} whileHover={{ y: -2 }} className="inline-block">
              <Link
                href="/analyse"
                className="inline-flex items-center gap-2 rounded-2xl bg-amber-500 px-6 py-3.5
                           font-bold text-white shadow-lg shadow-amber-900/40
                           transition-colors hover:bg-amber-400 min-h-[52px]"
              >
                Try it on your face →
              </Link>
            </motion.div>

            {/* Frame style pills */}
            <div className="mt-6 flex flex-wrap justify-center gap-2 lg:justify-start">
              {FRAMES.map((f) => (
                <span
                  key={f.label}
                  className="flex items-center gap-1.5 rounded-full bg-stone-800/80 px-2.5 py-1 text-[11px] font-medium text-stone-400"
                >
                  <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ background: f.dot }} />
                  {f.label}
                </span>
              ))}
            </div>
          </motion.div>

          {/* ── Rotating orbit — desktop only ─────────────────────────────── */}
          <div className="hidden flex-shrink-0 lg:block">
            <div
              className="relative"
              style={{ width: CONTAINER, height: CONTAINER, perspective: 900 }}
              onMouseMove={handleMouseMove}
              onMouseLeave={handleMouseLeave}
            >
              <motion.div
                className="absolute inset-0"
                style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
              >
                {/* Subtle orbit ring */}
                <div
                  className="pointer-events-none absolute rounded-full border border-stone-700/40"
                  style={{
                    width: ORBIT_R * 2 + CARD_D,
                    height: ORBIT_R * 2 + CARD_D,
                    top: '50%', left: '50%',
                    transform: 'translate(-50%,-50%)',
                  }}
                />

                {/* Pulse ring around the center photo */}
                <div
                  className="pointer-events-none absolute rounded-full border-2 border-amber-400/40"
                  style={{
                    width: CENTER_D + 20,
                    height: CENTER_D + 20,
                    top: '50%',
                    left: '50%',
                    marginTop: -(CENTER_D + 20) / 2,
                    marginLeft: -(CENTER_D + 20) / 2,
                    animation: entered ? 'demo-pulse 2.8s ease-out infinite' : 'none',
                  }}
                />

                {/* Center person photo */}
                <motion.div
                  className="absolute overflow-hidden rounded-full border-2 border-amber-400 shadow-2xl shadow-amber-950/50"
                  style={{ width: CENTER_D, height: CENTER_D, top: '50%', left: '50%', zIndex: 20 }}
                  initial={{ x: '-50%', y: '-50%', scale: 0.3, opacity: 0 }}
                  animate={entered ? { x: '-50%', y: '-50%', scale: 1, opacity: 1 } : {}}
                  transition={{ duration: 0.65, ease: [0.34, 1.56, 0.64, 1] }}
                >
                  <Image src="/demo/person.jpg" alt="Sample face" fill sizes="108px" className="object-cover object-top" />
                </motion.div>

                {/* Orbiting try-on photos */}
                {FRAMES.map((frame, i) => (
                  <OrbitPhoto
                    key={frame.label}
                    frame={frame}
                    index={i}
                    progress={progress}
                    entered={entered}
                    delay={0.3 + i * 0.12}
                  />
                ))}
              </motion.div>
            </div>
          </div>

          {/* ── Mobile: person photo + auto-scrolling photo strip ──────────── */}
          <div className="w-full lg:hidden">
            <motion.div
              className="mb-5 flex justify-center"
              initial={{ opacity: 0, scale: 0.85 }}
              animate={entered ? { opacity: 1, scale: 1 } : {}}
              transition={{ duration: 0.5, ease: EASE_OUT_EXPO }}
            >
              <div className="h-24 w-24 overflow-hidden rounded-full border-2 border-amber-500/60 shadow-xl relative">
                <Image src="/demo/person.jpg" alt="Sample face" fill sizes="96px" className="object-cover object-top" />
              </div>
            </motion.div>

            <motion.div
              className="overflow-hidden"
              initial={{ opacity: 0 }}
              animate={entered ? { opacity: 1 } : {}}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <div className={`flex w-max gap-4 ${reduceMotion ? '' : 'animate-demo-marquee'}`}>
                {[...FRAMES, ...FRAMES].map((frame, i) => (
                  <div
                    key={i}
                    className="flex-shrink-0 overflow-hidden rounded-full border-2 border-white/10 bg-stone-900 shadow-lg relative"
                    style={{ width: 88, height: 88 }}
                  >
                    <Image src={frame.src} alt={frame.label} fill sizes="88px" className="object-cover" />
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

        </div>
      </div>
    </motion.section>
  )
}
