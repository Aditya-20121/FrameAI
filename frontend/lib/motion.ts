import type { Variants, Transition } from 'framer-motion'

export const EASE_OUT_EXPO: Transition['ease'] = [0.22, 1, 0.36, 1]
export const EASE_SMOOTH: Transition['ease'] = [0.4, 0, 0.2, 1]
export const SPRING_POP: Transition = { type: 'spring', stiffness: 300, damping: 28 }

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: EASE_OUT_EXPO } },
}

export const fadeUpSm: Variants = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE_OUT_EXPO } },
}

export const stagger = (staggerChildren = 0.08, delayChildren = 0): Variants => ({
  hidden: {},
  show: { transition: { staggerChildren, delayChildren } },
})

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92 },
  show: { opacity: 1, scale: 1, transition: { duration: 0.4, ease: EASE_OUT_EXPO } },
}

export const viewportOnce = { once: true, amount: 0.2 } as const
