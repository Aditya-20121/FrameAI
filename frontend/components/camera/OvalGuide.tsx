type Props = {
  isAligned: boolean
  countdown: number
}

export default function OvalGuide({ isAligned, countdown }: Props) {
  const stroke = isAligned ? '#22c55e' : 'rgba(255,255,255,0.75)'
  const strokeWidth = isAligned ? 0.7 : 0.5

  return (
    <svg
      className="w-full h-full"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <mask id="oval-cutout">
          <rect width="100" height="100" fill="white" />
          <ellipse cx="50" cy="50" rx="28" ry="38" fill="black" />
        </mask>
      </defs>

      {/* Dark overlay outside the oval */}
      <rect
        width="100"
        height="100"
        fill="rgba(0,0,0,0.52)"
        mask="url(#oval-cutout)"
      />

      {/* Progress fill (green arc at bottom) */}
      {isAligned && countdown > 0 && (
        <ellipse
          cx="50"
          cy="50"
          rx="28"
          ry="38"
          fill="rgba(34,197,94,0.08)"
        />
      )}

      {/* Oval border */}
      <ellipse
        cx="50"
        cy="50"
        rx="28"
        ry="38"
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
      />
    </svg>
  )
}
