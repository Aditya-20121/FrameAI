import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export const metadata = {
  title: 'Privacy Policy — FrameAI',
  description: 'How FrameAI collects, uses, and protects your data.',
}

export default function PrivacyPage() {
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

      <article className="max-w-2xl mx-auto px-4 py-10 pb-20">
        <p className="text-[10px] font-bold uppercase tracking-widest text-amber-500 mb-2">Legal</p>
        <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight mb-1">Privacy Policy</h1>
        <p className="text-stone-400 text-sm mb-10">Last updated: 30 June 2026</p>

        <div className="space-y-8 text-stone-600 text-sm leading-relaxed">

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">1. Who we are</h2>
            <p>
              FrameAI is an AI-powered eyeglass frame recommendation tool. We help you find frames
              that suit your face shape and skin tone by analysing a selfie you provide. We do not
              require you to create an account or share any personal contact information.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">2. What data we collect</h2>
            <div className="space-y-3">
              <div className="bg-white border border-stone-100 rounded-xl p-4">
                <p className="font-semibold text-stone-800 mb-1">Your selfie photo</p>
                <p>Uploaded to Cloudflare R2 storage to run face analysis. Automatically deleted after 24 hours.</p>
              </div>
              <div className="bg-white border border-stone-100 rounded-xl p-4">
                <p className="font-semibold text-stone-800 mb-1">Face analysis results</p>
                <p>Face shape, undertone, skin depth, jawline, and eye spacing — derived from your photo and stored in our database. This is anonymous measurement data, not biometric identity data.</p>
              </div>
              <div className="bg-white border border-stone-100 rounded-xl p-4">
                <p className="font-semibold text-stone-800 mb-1">AI-generated try-on images</p>
                <p>When you use the "Try this on" feature, the generated image is stored in Cloudflare R2. We retain these to monitor and improve generation quality. They are not linked to any personal identity.</p>
              </div>
              <div className="bg-white border border-stone-100 rounded-xl p-4">
                <p className="font-semibold text-stone-800 mb-1">Session cookie</p>
                <p>A single anonymous cookie (<code className="text-xs bg-stone-100 px-1 py-0.5 rounded">_frameai_session</code>) is set in your browser to track your free try-on allowance (3 per session). It contains a random token — no personal information. It expires after one year of inactivity.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">3. How we use your data</h2>
            <ul className="list-disc list-inside space-y-1 text-stone-600">
              <li>To analyse your face and recommend suitable eyeglass frames</li>
              <li>To generate photorealistic try-on images of you wearing frames you select</li>
              <li>To enforce the 3 free try-on limit per session</li>
              <li>To monitor and improve the quality of AI-generated images</li>
            </ul>
            <p className="mt-3">We do <strong className="text-stone-800">not</strong> use your photo or analysis data for advertising, profiling, or any purpose beyond the above.</p>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">4. Third-party services</h2>
            <p className="mb-3">We use the following third parties to operate this service. Each receives only what is necessary to perform their function:</p>
            <div className="space-y-2">
              {[
                { name: 'Segmind', purpose: 'AI face analysis (Qwen3 VL) and try-on image generation (Nano Banana). Your photo is sent to Segmind\'s API for processing.', link: 'https://www.segmind.com/privacy' },
                { name: 'Supabase', purpose: 'Database hosting for session tokens and face analysis results.', link: 'https://supabase.com/privacy' },
                { name: 'Cloudflare R2', purpose: 'Cloud storage for uploaded photos and generated images.', link: 'https://www.cloudflare.com/privacypolicy/' },
                { name: 'Vercel', purpose: 'Frontend hosting.', link: 'https://vercel.com/legal/privacy-policy' },
                { name: 'Render', purpose: 'Backend API hosting.', link: 'https://render.com/privacy' },
              ].map(({ name, purpose, link }) => (
                <div key={name} className="bg-white border border-stone-100 rounded-xl p-4">
                  <p className="font-semibold text-stone-800 mb-0.5">{name}</p>
                  <p className="text-xs text-stone-500 mb-1">{purpose}</p>
                  <a href={link} target="_blank" rel="noopener noreferrer" className="text-xs text-amber-600 underline underline-offset-2">
                    Privacy policy →
                  </a>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">5. Data retention</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-stone-100 text-stone-500 uppercase tracking-wider">
                    <th className="text-left p-3 rounded-tl-lg">Data</th>
                    <th className="text-left p-3 rounded-tr-lg">Retention</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {[
                    ['Selfie photo (R2)', 'Deleted after 24 hours'],
                    ['Face analysis results (DB)', 'Retained indefinitely (anonymous)'],
                    ['Generated try-on images (R2)', 'Retained for quality monitoring'],
                    ['Session cookie', '1 year from last activity'],
                  ].map(([data, retention]) => (
                    <tr key={data} className="bg-white">
                      <td className="p-3 text-stone-700 font-medium">{data}</td>
                      <td className="p-3 text-stone-500">{retention}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">6. Your rights</h2>
            <p>
              You can request deletion of any data associated with your session by visiting our{' '}
              <a href="/contact" className="text-amber-600 underline underline-offset-2">Contact page</a>.
              Since we do not collect your name or email, please include your session token
              (visible in your browser&apos;s cookies under <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">_frameai_session</code>)
              so we can locate your records.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">7. Cookies</h2>
            <p>
              We set one strictly necessary cookie (<code className="text-xs bg-stone-100 px-1 py-0.5 rounded">_frameai_session</code>).
              We do not use advertising cookies, tracking pixels, or third-party analytics cookies.
              This cookie cannot be opted out of without breaking the service.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">8. Children</h2>
            <p>
              FrameAI is not directed at children under 13. We do not knowingly collect data from
              children. If you believe a child has used this service, contact us for deletion.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">9. Changes to this policy</h2>
            <p>
              We may update this policy as the product evolves. Material changes will be noted
              with an updated date at the top of this page.
            </p>
          </section>

          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">10. Contact</h2>
            <p>
              For privacy questions or deletion requests, visit our{' '}
              <a href="/contact" className="text-amber-600 underline underline-offset-2">Contact page</a>.
            </p>
          </section>

        </div>
      </article>
    </main>
  )
}
