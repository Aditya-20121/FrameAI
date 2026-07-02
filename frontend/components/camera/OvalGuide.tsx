type Props = {
  isAligned: boolean
  countdown: number
}

export default function OvalGuide({ isAligned, countdown }: Props) {
  return (
    <div className="w-full h-full flex items-center justify-center" style={{ paddingBottom: '12%' }}>
      <div
        style={{
          width: 'min(56vw, 224px)',
          aspectRatio: '3 / 4',
          borderRadius: '50%',
          boxShadow: '0 0 0 100vmax rgba(0,0,0,0.52)',
          border: `2.5px solid ${isAligned ? '#22c55e' : 'rgba(255,255,255,0.75)'}`,
          transition: 'border-color 0.3s ease',
          background: isAligned && countdown > 0 ? 'rgba(34,197,94,0.06)' : 'transparent',
        }}
      />
    </div>
  )
}
