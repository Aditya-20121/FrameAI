# FrameAI Frontend Design Skill

This skill defines the visual system, animation approach, and component patterns
for FrameAI. Follow every rule here before writing any UI code.

---

## Brand Identity

FrameAI is an AI-powered eyewear recommendation tool targeting urban Indian consumers.
The brand sits at the intersection of **precision tech** and **personal style** —
confident, warm, and modern. Not sterile. Not generic SaaS.

**Personality:** Trustworthy expert with a warm, human tone. Think optician who also knows AI.

---

## Color System

```
Accent (amber)    #f59e0b  — amber-500   — CTAs, icons, highlights, hover glows
Accent light      #fef3c7  — amber-50    — pill backgrounds, icon backgrounds
Accent muted      #fde68a  — amber-200   — shadows, borders on amber elements
Accent warm       #f97316  — orange-500  — used ONLY for gradient accents
Background        #fafaf9  — stone-50    — page background
Surface           #ffffff  — white       — card / section backgrounds
Border            #f5f5f4  — stone-100   — default dividers
Border medium     #e7e5e4  — stone-200   — hover borders, input borders
Text primary      #1c1917  — stone-900   — headings, strong labels
Text body         #78716c  — stone-500   — body copy, descriptors
Text muted        #a8a29e  — stone-400   — captions, metadata, placeholders
Destructive       #ef4444  — red-500     — errors only
```

**Neutral bias:** stone (warm grey with a slight yellow tint) — NOT slate or zinc.
Never use pure #808080 grey or generic blue-greys.

---

## Typography

### Fonts (already loaded in layout.tsx)
- **Display / Italic headings:** `font-display` → DM Serif Display — use italic weight only for emphasis spans
- **Body / UI:** `font-sans` → Plus Jakarta Sans — default for all other text
- **Mono:** `font-mono` → Geist Mono — code, IDs, technical values only

### Type Scale
```
Hero headline    clamp(2.4rem, 8vw, 3.2rem)   font-extrabold tracking-tight leading-[1.1]
Section heading  1.5rem / 2rem                 font-bold tracking-tight
Card heading     0.875rem                      font-semibold
Body             1rem                          font-normal leading-relaxed
Caption          0.75rem                       font-normal text-stone-400
Label / badge    0.6875rem                     font-bold uppercase tracking-widest
```

### Rules
- Italic DM Serif spans are used ONLY for ONE emphasis phrase per heading — never the whole heading
- All headings: `text-wrap: balance` (or `text-balance` Tailwind class)
- Body max-width: 60 characters (prose) — enforce with `max-w-xs` or `max-w-sm`
- Keep uppercase labels (`tracking-widest`) below 20 characters
- Do NOT mix font weights arbitrarily — semibold for UI, bold for headings, extrabold for hero only

---

## Spacing System (8px grid)

```
4px   — gap between icon and tiny label
8px   — inline gap between related elements
12px  — padding on small chips / badges
16px  — base padding for compact sections
24px  — section internal padding (mobile)
32px  — section vertical padding (desktop)
48px  — large section separation
```

Use Tailwind spacing scale: `gap-2, gap-3, gap-4, gap-6, gap-8, gap-12`
Max content width: `max-w-2xl` (672px) centered with `mx-auto`

---

## Border Radius

```
Pill buttons / tags    rounded-full
Primary CTA buttons    rounded-2xl
Cards / panels         rounded-2xl
Icon containers        rounded-xl
Small badges           rounded-full
Inputs                 rounded-xl
Modals                 rounded-3xl
```

Never use `rounded-lg` alone — it looks generic. Use `rounded-xl` minimum for cards.

---

## Shadow System

```
Card resting      shadow-sm  (stone-900/5)
Card hover        shadow-md
Primary CTA       shadow-lg shadow-amber-200
Amber hover       shadow-amber-300
Modals            shadow-2xl
```

Never use shadows with cool-grey tints. Shadows should be warm (amber or stone tint).

---

## Framer Motion Animation Patterns

### Always use Framer Motion for:
- Scroll-triggered section reveals (use `whileInView`, `viewport: { once: true, amount: 0.2 }`)
- Staggered card grids (staggerChildren: 0.08)
- Hover lift on interactive cards (whileHover: { y: -4, scale: 1.01 })
- Page/route transitions
- Modal open/close
- Number/count animations

### Standard entrance variant (reuse across all sections):
```ts
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } }
}
const stagger = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.08 } }
}
```

### Easing presets:
```ts
const EASE_OUT_EXPO = [0.22, 1, 0.36, 1]       // primary entrances
const EASE_SPRING   = { type: 'spring', stiffness: 300, damping: 28 }  // interactive
const EASE_SMOOTH   = [0.4, 0, 0.2, 1]          // layout shifts
```

### Rules:
- `viewport: { once: true }` always — do NOT re-animate on scroll back up
- Duration: 0.4–0.6s for entrances, 0.15–0.25s for hover/tap micro-interactions
- Never animate opacity alone without a y/scale transform — it feels flat
- `will-change: transform` only on elements that actually animate

---

## Component Patterns

### Buttons

**Primary CTA:**
```tsx
<motion.button
  whileHover={{ y: -2, boxShadow: '0 8px 20px rgb(251 191 36 / 0.4)' }}
  whileTap={{ scale: 0.97 }}
  className="flex items-center gap-2 bg-amber-500 text-white font-bold px-7 py-4 rounded-2xl shadow-lg shadow-amber-200 hover:bg-amber-400 transition-colors"
>
```

**Secondary / ghost:**
```tsx
className="flex items-center gap-2 bg-white text-stone-700 font-semibold px-6 py-4 rounded-2xl border border-stone-200 hover:border-stone-300 hover:shadow-sm transition-all"
```

### Cards

Always: `bg-white rounded-2xl border border-stone-100 shadow-sm`
Hover: `hover:shadow-md hover:-translate-y-0.5 transition-all duration-200`
Use `motion.div` with `whileHover` instead of CSS hover for premium feel.

### Section structure
```tsx
<section className="bg-white px-4 py-12 border-b border-stone-100">
  <div className="max-w-2xl mx-auto">
    <motion.div variants={stagger} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.2 }}>
      {/* Eyebrow label */}
      <p className="text-xs font-bold uppercase tracking-widest text-amber-600 mb-3">Section Name</p>
      {/* Heading */}
      <h2 className="text-2xl font-bold text-stone-900 text-balance mb-8">...</h2>
      {/* Content */}
    </motion.div>
  </div>
</section>
```

### Icon containers
```tsx
<div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center">
  <Icon className="w-5 h-5 text-amber-500" strokeWidth={1.75} />
</div>
```
Use `strokeWidth={1.75}` — the Lucide default (2) is too heavy.

---

## Anti-patterns — Never Do These

- No pure white (#fff) hero — always offset with stone-50 background or subtle gradient
- No generic blue accent — this product is amber/warm only
- No `rounded-lg` on cards — minimum `rounded-xl`
- No CSS `transition` on elements that should use Framer Motion
- No `animate-bounce` or `animate-ping` — use Framer Motion spring instead
- No placeholder avatars, stock faces, or Lorem Ipsum — use real content
- No centered-everything layout for content sections — left-align body copy
- No icon + label pairs without consistent `gap-2` and `text-xs font-medium`
- No shadow with a cool/blue tint
- No separate `margin-top` between siblings in a flex/grid parent — use `gap`
- No font size below 11px (`text-[11px]` minimum for captions)
- Never stack more than 3 grey tones in the same component without an accent break

---

## Mobile-First Rules

- All layouts start as single-column, expand at `sm:` (640px)
- Tap targets minimum 44×44px
- Bottom sheet preferred over centered modal on mobile
- Sticky header uses `backdrop-blur-sm` + `bg-white/95` for glass effect
- Touch: `active:scale-95` on all interactive elements (in addition to Framer `whileTap`)

---

## 21st.dev Component Integration

When pulling components from 21st.dev:
1. Replace all color tokens with the FrameAI amber/stone system above
2. Replace any blue accent → amber-500
3. Replace any generic grey → stone-* equivalent
4. Wrap entrance with `motion.div` using `fadeUp` + `stagger` variants
5. Ensure fonts use `font-sans` / `font-display` not the library's default

---

## Performance Rules

- All images: use `next/image` with `width`/`height` and `alt`
- Icons: import individually from `lucide-react` (never `import * as Icons`)
- Fonts: already loaded in layout.tsx — do not add new @font-face or Google Fonts links
- Animations: `viewport: { once: true }` always — no re-triggering
- Lazy load sections below the fold with `dynamic(() => import(...), { ssr: false })` if they are heavy

---

## Checklist Before Shipping Any Component

- [ ] Uses amber accent (not blue/purple/generic)
- [ ] Framer Motion on entrance and hover (not CSS keyframes for interactive elements)
- [ ] `viewport: { once: true }` on all whileInView
- [ ] `max-w-2xl mx-auto` wrapper present
- [ ] Mobile single-column layout tested
- [ ] No Lorem Ipsum — real product copy
- [ ] Tap targets ≥ 44px
- [ ] `text-balance` on all headings
