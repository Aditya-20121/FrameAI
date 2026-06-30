/**
 * Derives actionable shopping guidance from a completed face analysis.
 * Used by AnalysisCard to tell users what to look for — styles, colours, size.
 *
 * Rules mirror the Python recommender (services/recommender.py) but are kept
 * client-side so AnalysisCard can display them without an extra API call.
 */

import type { AnalysisResponse, FaceShape, Undertone, SkinDepth, Jawline, Cheekbones, EyeSet } from './types'

// ── Types ─────────────────────────────────────────────────────────────────────

export interface StyleGuide {
  bestStyles:   StyleRec[]
  avoidStyles:  string[]
  styleNote:    string | null     // e.g. "curved styles will soften your jaw"
  bestColours:  ColourRec[]
  avoidColours: string[]
  colourNote:   string
  sizeLabel:    string            // e.g. "Standard fit"
  sizeSpec:     string            // e.g. "52–54mm lens width"
  sizeNote:     string | null     // optional eye-spacing note
}

export interface StyleRec {
  name:  string                   // display name, e.g. "Rectangular"
  slug:  string                   // machine name, e.g. "rectangular"
  why:   string                   // one-phrase reason
}

export interface ColourRec {
  name:  string                   // e.g. "Tortoiseshell"
  hex:   string                   // approximate visual hex
  why:   string                   // e.g. "earthy tones for warm skin"
}

// ── Frame style rules (mirrors FACE_SHAPE_RULES in recommender.py) ────────────

const STYLE_WHY: Record<string, string> = {
  rectangular: 'adds length & definition',
  wayfarer:    'strong horizontal presence',
  square:      'structured, versatile look',
  round:       'softens angular features',
  'cat-eye':   'upswept for lift & balance',
  rimless:     'lightweight, minimal look',
  aviator:     'curved, open feel',
  browline:    'upper detail draws the eye',
  geometric:   'modern angular definition',
}

const FACE_SHAPE_STYLE_GUIDE: Record<FaceShape, {
  best: string[]
  avoid: string[]
  tip: string
}> = {
  oval: {
    best:  ['rectangular', 'wayfarer', 'cat-eye'],
    avoid: [],
    tip:   'Oval is the most versatile shape — almost any style works.',
  },
  round: {
    best:  ['rectangular', 'square', 'geometric'],
    avoid: ['round'],
    tip:   'Angular frames elongate and define a round face.',
  },
  square: {
    best:  ['round', 'cat-eye', 'aviator'],
    avoid: ['square', 'rectangular'],
    tip:   'Curved frames soften a strong jaw and angular proportions.',
  },
  heart: {
    best:  ['round', 'aviator', 'rimless'],
    avoid: ['cat-eye', 'browline'],
    tip:   'Lighter, bottom-weighted frames balance a wide forehead.',
  },
  diamond: {
    best:  ['cat-eye', 'browline', 'round'],
    avoid: ['rectangular'],
    tip:   'Frames with width or detail at the top balance strong cheekbones.',
  },
  oblong: {
    best:  ['round', 'wayfarer', 'square'],
    avoid: ['rimless'],
    tip:   'Wide frames add horizontal presence and break vertical length.',
  },
}

// ── Colour rules ──────────────────────────────────────────────────────────────

// Representative hex swatches (approximate — for visual guidance only)
const COLOUR_HEXES: Record<string, string> = {
  'Tortoiseshell': '#7A4A28',
  'Gold':          '#C89440',
  'Brown':         '#5C3317',
  'Rose Gold':     '#C4847E',
  'Olive':         '#5B5829',
  'Black':         '#1A1A1A',
  'Silver':        '#A8A9AD',
  'Gunmetal':      '#4A4C52',
  'Navy':          '#1B2A4A',
  'Burgundy':      '#6B1E30',
  'Deep Green':    '#1C3D2E',
  'Purple':        '#4A2880',
  'Clear':         '#D8E4EC',
  'Blush':         '#E8C2BC',
}

// Best colour names per undertone
const UNDERTONE_COLOURS: Record<Undertone, string[]> = {
  warm:    ['Tortoiseshell', 'Gold', 'Brown'],
  cool:    ['Black', 'Navy', 'Silver'],
  neutral: ['Clear', 'Tortoiseshell', 'Navy'],
}

// Depth adjustments — swap in a bolder or softer recommendation
const DEPTH_COLOUR_SWAP: Partial<Record<SkinDepth, Partial<Record<Undertone, string[]>>>> = {
  fair:   {
    warm: ['Tortoiseshell', 'Gold', 'Rose Gold'],     // Rose gold gentler on fair skin
    cool: ['Silver', 'Blush', 'Navy'],                // Silver & blush soft on fair
  },
  deep:   {
    warm: ['Tortoiseshell', 'Gold', 'Olive'],         // Olive pops on deep warm
    cool: ['Black', 'Burgundy', 'Deep Green'],        // Bold jewels on deep cool
    neutral: ['Black', 'Clear', 'Burgundy'],
  },
  olive:  {
    warm: ['Tortoiseshell', 'Olive', 'Gold'],         // Olive-warm harmony
  },
}

const UNDERTONE_COLOUR_NOTES: Record<Undertone, string> = {
  warm:    'Earthy and golden tones echo the warmth in your skin.',
  cool:    'Crisp, jewel-toned and dark frames complement cool undertones.',
  neutral: 'Your versatile undertone suits a wide range — lean into any palette.',
}

const UNDERTONE_AVOID: Record<Undertone, string[]> = {
  warm:    ['Silver', 'Gunmetal', 'Cool Grey'],
  cool:    ['Orange', 'Gold', 'Amber'],
  neutral: [],
}

// ── Size rules ────────────────────────────────────────────────────────────────

const SIZE_SPECS: Record<string, { label: string; spec: string; full: string }> = {
  narrow:   {
    label: 'Narrow fit',
    spec:  '48–51mm lens width',
    full:  'Look for frames tagged "S" or "XS", or a total frame width under 130mm.',
  },
  standard: {
    label: 'Standard fit',
    spec:  '52–54mm lens width',
    full:  'Most frames will suit you. Standard fit covers the majority of the catalogue.',
  },
  wide:     {
    label: 'Wide fit',
    spec:  '55–57mm lens width',
    full:  'Look for frames tagged "L" or "W", or a total frame width above 138mm.',
  },
}

const EYE_SET_SIZE_NOTES: Partial<Record<EyeSet, string>> = {
  close: 'A lighter bridge or clear nose pads will optically open up the space between your eyes.',
  wide:  'A defined, darker bridge keeps your proportions balanced.',
}

// ── Jawline / cheekbone style notes ───────────────────────────────────────────

function getStyleNote(jawline?: Jawline | null, cheekbones?: Cheekbones | null): string | null {
  if (jawline === 'angular') return 'Curved styles will soften your defined jaw.'
  if (jawline === 'soft')    return 'Angular styles will add structure and definition.'
  if (cheekbones === 'high') return 'Cat-eye frames highlight your cheekbone structure beautifully.'
  return null
}

// ── Main deriver ──────────────────────────────────────────────────────────────

export function deriveStyleGuide(analysis: AnalysisResponse): StyleGuide | null {
  if (!analysis.face_shape || !analysis.undertone) return null

  const shape     = analysis.face_shape
  const undertone = analysis.undertone
  const depth     = analysis.skin_depth   ?? undefined
  const jawline   = analysis.jawline      ?? undefined
  const cheekbones = analysis.cheekbones  ?? undefined
  const eyeSet    = analysis.eye_set      ?? undefined
  const sizeBand  = analysis.size_band    ?? 'standard'

  // ── Styles ────────────────────────────────────────────────────────────────

  const shapeRules = FACE_SHAPE_STYLE_GUIDE[shape]

  // Boost jawline-influenced styles to front
  let orderedBest = [...shapeRules.best]
  if (jawline === 'angular') {
    // Prefer soft/curved styles first
    const curved = ['round', 'cat-eye', 'aviator', 'rimless']
    orderedBest = [...orderedBest.filter(s => curved.includes(s)), ...orderedBest.filter(s => !curved.includes(s))]
  } else if (jawline === 'soft') {
    // Prefer defining styles first
    const defining = ['rectangular', 'square', 'geometric', 'browline']
    orderedBest = [...orderedBest.filter(s => defining.includes(s)), ...orderedBest.filter(s => !defining.includes(s))]
  }

  const bestStyles: StyleRec[] = orderedBest.slice(0, 3).map(slug => ({
    name: slug.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join('-'),
    slug,
    why:  STYLE_WHY[slug] ?? '',
  }))

  // ── Colours ───────────────────────────────────────────────────────────────

  const depthSwap   = depth ? DEPTH_COLOUR_SWAP[depth]?.[undertone] : undefined
  const colourNames = depthSwap ?? UNDERTONE_COLOURS[undertone]

  const bestColours: ColourRec[] = colourNames.map(name => ({
    name,
    hex: COLOUR_HEXES[name] ?? '#888888',
    why: '',
  }))

  // ── Size ──────────────────────────────────────────────────────────────────

  const sizeInfo = SIZE_SPECS[sizeBand] ?? SIZE_SPECS['standard']
  const sizeNote = eyeSet ? (EYE_SET_SIZE_NOTES[eyeSet] ?? null) : null

  return {
    bestStyles,
    avoidStyles:  shapeRules.avoid.map(s => s.split('-').map(w => w[0].toUpperCase() + w.slice(1)).join('-')),
    styleNote:    getStyleNote(jawline as Jawline, cheekbones as Cheekbones),
    bestColours,
    avoidColours: UNDERTONE_AVOID[undertone],
    colourNote:   UNDERTONE_COLOUR_NOTES[undertone],
    sizeLabel:    sizeInfo.label,
    sizeSpec:     sizeInfo.spec,
    sizeNote,
  }
}
