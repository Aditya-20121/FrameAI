import Link from 'next/link'
import { ArrowLeft, Mail } from 'lucide-react'

export const metadata = {
  title: 'Contact Us — FrameAI',
  description: 'Get in touch with the FrameAI team for queries, grievances, or data deletion requests.',
}

const TEAM = [
  { name: 'Aditya Kakade',  email: 'adityakakade2021@gmail.com' },
  { name: 'Kalpesh Pawar',  email: 'kalpeshpawar17680@gmail.com' },
  { name: 'Akhilesh Shinde', email: 'akhileshshinde477@gmail.com' },
]

export default function ContactPage() {
  return (
    <main className="min-h-screen bg-stone-50">
      <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-sm border-b border-stone-100">
        <div className="max-w-2xl mx-auto flex items-center gap-3 px-4 py-3.5">
          <Link href="/" className="text-stone-400 hover:text-stone-700 transition-colors p-1 -ml-1">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-amber-500 rounded-md flex items-center justify-center">
              <span className="text-white text-[10px] font-black">F</span>
            </div>
            <span className="font-bold text-stone-900">FrameAI</span>
          </div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-10 pb-20">
        <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-2">Get in touch</p>
        <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight mb-2">Contact Us</h1>
        <p className="text-stone-400 text-sm mb-10">
          For any queries, feel free to reach out to us at
        </p>

        <div className="space-y-3 mb-10">
          {TEAM.map(({ name, email }) => (
            <a
              key={email}
              href={`mailto:${email}`}
              className="flex items-center gap-4 bg-white border border-stone-100 rounded-2xl p-4 shadow-sm hover:shadow-md hover:-translate-y-0.5 transition-all group"
            >
              <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:bg-amber-100 transition-colors">
                <Mail className="w-4.5 h-4.5 text-amber-500" strokeWidth={2} />
              </div>
              <div className="min-w-0">
                <p className="text-stone-900 font-semibold text-sm">{name}</p>
                <p className="text-amber-600 text-sm truncate">{email}</p>
              </div>
            </a>
          ))}
        </div>

        <div className="bg-white border border-stone-100 rounded-2xl p-5 text-sm text-stone-500 space-y-2">
          <p className="font-semibold text-stone-700">What to include in your message</p>
          <ul className="list-disc list-inside space-y-1 text-xs">
            <li>For <strong className="text-stone-600">data deletion</strong> — include your session token from browser cookies (<code className="bg-stone-100 px-1 py-0.5 rounded text-[10px]">_frameai_session</code>)</li>
            <li>For <strong className="text-stone-600">grievances</strong> — describe the issue clearly; we acknowledge within 24 hours and resolve within 15 working days</li>
            <li>For <strong className="text-stone-600">general queries</strong> — anything about how the app works, frame recommendations, or partnerships</li>
          </ul>
        </div>

        <div className="mt-6 flex gap-4 text-xs text-stone-400">
          <Link href="/privacy" className="underline underline-offset-2 hover:text-stone-600 transition-colors">Privacy Policy</Link>
          <Link href="/terms" className="underline underline-offset-2 hover:text-stone-600 transition-colors">Terms &amp; Conditions</Link>
        </div>
      </div>
    </main>
  )
}
