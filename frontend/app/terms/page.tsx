import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export const metadata = {
  title: 'Terms & Conditions — FrameAI',
  description: 'Terms of use for FrameAI, including data collection, consent, affiliate disclosure, and grievance officer details.',
}

const EFFECTIVE_DATE = '2 July 2026'

export default function TermsPage() {
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
        <h1 className="text-3xl font-extrabold text-stone-900 tracking-tight mb-1">Terms &amp; Conditions</h1>
        <p className="text-stone-400 text-sm mb-2">Effective date: {EFFECTIVE_DATE}</p>
        <p className="text-stone-400 text-xs mb-10">
          These terms are governed by Indian law and comply with the Information Technology Act 2000,
          the IT (SPDI) Rules 2011, the Digital Personal Data Protection Act 2023, and the Consumer
          Protection (E-Commerce) Rules 2020.
        </p>

        <div className="space-y-8 text-stone-600 text-sm leading-relaxed">

          {/* 1 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">1. About FrameAI</h2>
            <p>
              FrameAI (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) is an AI-powered eyeglass frame recommendation platform
              operated by <strong className="text-stone-800">Aditya Kakade</strong>, an individual based in India
              (&quot;Operator&quot;). For contact details, see our{' '}
              <Link href="/contact" className="text-amber-600 underline underline-offset-2">Contact page</Link>.
            </p>
            <p className="mt-2">
              FrameAI is a prototype product and is provided free of charge. It is not a registered
              company. These Terms constitute a legally binding agreement between you and the Operator
              under the laws of the Republic of India.
            </p>
          </section>

          {/* 2 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">2. Acceptance of Terms</h2>
            <p>
              By accessing or using FrameAI, including taking or uploading a photo, you confirm that
              you have read, understood, and agree to be bound by these Terms and our{' '}
              <Link href="/privacy" className="text-amber-600 underline underline-offset-2">Privacy Policy</Link>.
              If you do not agree, do not use this service.
            </p>
            <p className="mt-2">
              You must be at least 18 years of age to use FrameAI. If you are between 13 and 17,
              you may only use this service with the explicit consent of a parent or guardian.
              We do not knowingly process data of children under 13.
            </p>
          </section>

          {/* 3 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">3. Description of Service</h2>
            <p>FrameAI provides the following features:</p>
            <ul className="list-disc list-inside space-y-1 mt-2 text-stone-600">
              <li>Face shape and skin undertone analysis from a selfie using AI</li>
              <li>Personalised eyeglass frame recommendations from a curated catalogue</li>
              <li>AI-generated photorealistic try-on images (limited to 3 per anonymous session)</li>
              <li>Links to purchase recommended frames from third-party retailers</li>
            </ul>
            <p className="mt-3">
              All recommendations are <strong className="text-stone-800">AI-assisted aesthetic suggestions only</strong>.
              They do not constitute medical, optometric, or clinical advice of any kind.
            </p>
          </section>

          {/* 4 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">
              4. Biometric Data &amp; Sensitive Personal Data
            </h2>
            <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 mb-4">
              <p className="text-amber-800 text-xs font-semibold uppercase tracking-widest mb-1">
                Important — Biometric Data
              </p>
              <p className="text-amber-900 text-sm">
                Under Rule 3 of the Information Technology (Reasonable Security Practices and Procedures
                and Sensitive Personal Data or Information) Rules 2011 (&quot;SPDI Rules&quot;), your facial image
                and derived facial measurements constitute <strong>sensitive personal data</strong>.
              </p>
            </div>
            <p>
              When you use FrameAI, you provide us with a photograph of your face. From this photograph,
              our AI derives: face shape classification, jawline type, cheekbone prominence, eye spacing,
              skin undertone, and skin depth. These are considered biometric data under Indian law.
            </p>
            <p className="mt-2">
              We collect and process this data <strong className="text-stone-800">solely for the
              purpose of recommending eyeglass frames</strong> suited to your facial features. Your
              photograph is automatically and permanently deleted from our servers within <strong className="text-stone-800">24 hours</strong> of upload.
            </p>
          </section>

          {/* 5 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">5. Consent for Data Processing</h2>
            <p>
              In compliance with the SPDI Rules 2011 (Rule 5) and the Digital Personal Data Protection
              Act 2023 (&quot;DPDP Act&quot;), we obtain your explicit, informed, and specific consent before
              collecting any biometric data.
            </p>
            <div className="space-y-3 mt-3">
              <div className="bg-white border border-stone-100 rounded-xl p-4">
                <p className="font-semibold text-stone-800 mb-1">What you consent to</p>
                <ul className="list-disc list-inside space-y-1 text-stone-600 text-xs">
                  <li>Collection and temporary storage of your facial photograph</li>
                  <li>Processing of your photograph by Segmind&apos;s Gemini AI model for face analysis</li>
                  <li>Storage of derived (anonymous) facial measurements in our database</li>
                  <li>Generation of a photorealistic try-on image when you request it</li>
                </ul>
              </div>
              <div className="bg-white border border-stone-100 rounded-xl p-4">
                <p className="font-semibold text-stone-800 mb-1">Withdrawal of consent</p>
                <p className="text-xs">
                  You may withdraw consent at any time by closing the session and not submitting a photo.
                  For deletion of data already submitted,{' '}
                  <Link href="/contact" className="text-amber-600 underline underline-offset-2">contact us</Link>{' '}
                  with your session token (found in your browser cookies under{' '}
                  <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">_frameai_session</code>).
                  Withdrawal does not affect the lawfulness of processing carried out before withdrawal.
                </p>
              </div>
            </div>
          </section>

          {/* 6 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">6. How We Use Your Data</h2>
            <p>We use your data exclusively for the following purposes:</p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>Analysing your face shape and skin undertone to recommend frames</li>
              <li>Generating photorealistic AI try-on images when requested</li>
              <li>Enforcing the 3 free try-on limit per anonymous session</li>
              <li>Monitoring and improving the quality of AI outputs</li>
            </ul>
            <p className="mt-3">
              We do <strong className="text-stone-800">not</strong> use your data for advertising,
              behavioural profiling, sale to third parties, or any purpose other than those listed above.
              Your biometric data is never sold, rented, or licensed.
            </p>
          </section>

          {/* 7 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">7. Third-Party Data Processors</h2>
            <p className="mb-3">
              We share only the minimum necessary data with the following processors to operate
              the service. Each processes data on our behalf under their own privacy policies:
            </p>
            <div className="space-y-2">
              {[
                {
                  name: 'Segmind (Google Gemini 2.5 Flash Lite)',
                  data: "Your facial photograph is sent to Segmind's API for AI-based face analysis.",
                  link: 'https://www.segmind.com/privacy',
                },
                {
                  name: 'Segmind (Nano Banana 2 Lite)',
                  data: 'Your photograph and selected frame image are sent to generate try-on images.',
                  link: 'https://www.segmind.com/privacy',
                },
                {
                  name: 'Cloudflare R2',
                  data: 'Temporary cloud storage for uploaded photos and generated try-on images.',
                  link: 'https://www.cloudflare.com/privacypolicy/',
                },
                {
                  name: 'Supabase',
                  data: 'Database hosting for anonymous session tokens and face analysis results.',
                  link: 'https://supabase.com/privacy',
                },
              ].map(({ name, data, link }) => (
                <div key={name} className="bg-white border border-stone-100 rounded-xl p-4">
                  <p className="font-semibold text-stone-800 mb-0.5 text-xs">{name}</p>
                  <p className="text-xs text-stone-500 mb-1">{data}</p>
                  <a href={link} target="_blank" rel="noopener noreferrer" className="text-xs text-amber-600 underline underline-offset-2">
                    Privacy policy →
                  </a>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-stone-500">
              All processors are bound by contractual data protection obligations. Data is not
              transferred outside India for storage purposes, though processing may occur on
              internationally hosted AI infrastructure.
            </p>
          </section>

          {/* 8 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">8. Data Retention</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-stone-100 text-stone-500 uppercase tracking-wider">
                    <th className="text-left p-3 rounded-tl-lg">Data</th>
                    <th className="text-left p-3">Retention Period</th>
                    <th className="text-left p-3 rounded-tr-lg">Basis</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {[
                    ['Selfie photo (cloud storage)', 'Deleted after 24 hours', 'Minimum necessary'],
                    ['Face analysis results (database)', 'Retained anonymously — no photo link', 'Service improvement'],
                    ['AI try-on images (cloud storage)', 'Retained for quality monitoring', 'Legitimate interest'],
                    ['Session token (browser cookie)', '1 year from last activity', 'Enforcing usage limits'],
                  ].map(([data, retention, basis]) => (
                    <tr key={data} className="bg-white">
                      <td className="p-3 text-stone-700 font-medium">{data}</td>
                      <td className="p-3 text-stone-500">{retention}</td>
                      <td className="p-3 text-stone-400">{basis}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* 9 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">
              9. Your Rights under the DPDP Act 2023
            </h2>
            <p className="mb-3">
              Under Sections 11–14 of the Digital Personal Data Protection Act 2023, you have the
              following rights as a Data Principal:
            </p>
            <div className="grid grid-cols-1 gap-2">
              {[
                {
                  right: 'Right to Information',
                  desc: 'You may request a summary of the personal data we hold about your session.',
                },
                {
                  right: 'Right to Correction & Erasure',
                  desc: 'You may request correction of inaccurate data or erasure of all data linked to your session.',
                },
                {
                  right: 'Right to Withdraw Consent',
                  desc: 'You may withdraw consent at any time. The service cannot continue without consent for biometric processing.',
                },
                {
                  right: 'Right to Grievance Redressal',
                  desc: 'You may raise a grievance with our Grievance Officer (Section 18 of these Terms).',
                },
                {
                  right: 'Right to Nominate',
                  desc: 'You may nominate another person to exercise these rights on your behalf in case of death or incapacity.',
                },
              ].map(({ right, desc }) => (
                <div key={right} className="bg-white border border-stone-100 rounded-xl p-4">
                  <p className="font-semibold text-stone-800 mb-1 text-xs">{right}</p>
                  <p className="text-xs text-stone-500">{desc}</p>
                </div>
              ))}
            </div>
            <p className="mt-3 text-xs text-stone-500">
              To exercise any of the above rights,{' '}
              <Link href="/contact" className="text-amber-600 underline underline-offset-2">contact us</Link>.
              We will respond within 15 working days.
            </p>
          </section>

          {/* 10 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">10. Affiliate Disclosure</h2>
            <div className="bg-stone-50 border border-stone-200 rounded-xl p-4">
              <p>
                FrameAI displays eyeglass frames from third-party retailers including Lenskart and
                John Jacobs India. Some links to these retailers are <strong className="text-stone-800">affiliate links</strong>.
                If you purchase through an affiliate link, FrameAI may earn a referral commission
                at <strong className="text-stone-800">no additional cost to you</strong>.
              </p>
              <p className="mt-2">
                Affiliate relationships do <strong className="text-stone-800">not influence AI recommendations</strong>.
                Frames are ranked purely by how well they match your facial features as determined
                by our recommendation algorithm. We do not accept payment from retailers to alter rankings.
              </p>
              <p className="mt-2 text-xs text-stone-400">
                Disclosure in accordance with Section 2(47) of the Consumer Protection Act 2019
                and the Consumer Protection (E-Commerce) Rules 2020.
              </p>
            </div>
          </section>

          {/* 11 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">11. AI Disclaimer</h2>
            <p>
              All face shape analysis, undertone detection, and frame recommendations are generated
              by AI models. These are <strong className="text-stone-800">aesthetic suggestions only</strong>.
              They may not be accurate for all face types, lighting conditions, or photographic angles.
            </p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>AI recommendations are not a substitute for advice from a licensed optometrist</li>
              <li>AI-generated try-on images are photorealistic simulations — actual fit may vary</li>
              <li>Accuracy of face shape detection may be limited by photo quality or unusual angles</li>
              <li>Skin undertone detection is an approximation — results may vary across devices and lighting</li>
            </ul>
          </section>

          {/* 12 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">12. Limitation of Liability</h2>
            <p>To the maximum extent permitted by applicable Indian law:</p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>
                FrameAI is provided &quot;as is&quot; without warranties of any kind, express or implied,
                including warranties of accuracy, fitness for a particular purpose, or non-infringement.
              </li>
              <li>
                The Operator is not liable for any direct, indirect, incidental, special, or
                consequential damages arising from use of the service or reliance on its recommendations.
              </li>
              <li>
                Since FrameAI is provided free of charge, the Operator&apos;s aggregate liability shall
                not exceed <strong className="text-stone-800">INR 0 (zero)</strong>.
              </li>
              <li>
                The Operator is not responsible for any purchase decisions made based on AI
                recommendations, or for the quality, fit, or pricing of frames purchased from
                third-party retailers.
              </li>
            </ul>
          </section>

          {/* 13 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">13. Intellectual Property</h2>
            <p>
              All content on FrameAI — including but not limited to the recommendation algorithm,
              UI design, code, and branding — is owned by the Operator or its licensors.
              You may not copy, reproduce, or distribute any part of this service without prior
              written consent.
            </p>
            <p className="mt-2">
              Frame product images are the property of their respective retailers and are displayed
              under implied licence for recommendation purposes. AI-generated try-on images are
              derivative works; you are granted a personal, non-commercial licence to save and
              share them for personal use only.
            </p>
          </section>

          {/* 14 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">14. Prohibited Uses</h2>
            <p>You agree not to:</p>
            <ul className="list-disc list-inside space-y-1 mt-2">
              <li>Upload photographs of any person other than yourself without their explicit consent</li>
              <li>Upload photographs of minors without verifiable parental or guardian consent</li>
              <li>Attempt to reverse-engineer, scrape, or extract data from the service</li>
              <li>Use the service for any unlawful purpose under Indian law</li>
              <li>Attempt to circumvent the 3 try-on limit per session</li>
              <li>Use automated tools or bots to interact with the service</li>
            </ul>
          </section>

          {/* 15 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">15. Third-Party Retailers</h2>
            <p>
              FrameAI links to frames on third-party retailer websites (Lenskart, John Jacobs, etc.).
              When you click a purchase link, you leave FrameAI and are subject to that retailer&apos;s
              own terms of sale, return policy, and privacy policy. FrameAI is not a party to any
              transaction between you and a retailer. Any disputes regarding a purchase must be
              resolved directly with the retailer.
            </p>
          </section>

          {/* 16 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">16. Changes to These Terms</h2>
            <p>
              We may update these Terms as the product evolves. Material changes will be indicated
              by an updated effective date at the top of this page. Continued use of the service
              after a change constitutes acceptance of the revised Terms.
            </p>
          </section>

          {/* 17 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">17. Governing Law &amp; Jurisdiction</h2>
            <p>
              These Terms are governed by and construed in accordance with the laws of the
              <strong className="text-stone-800"> Republic of India</strong>, without regard to
              conflict of law principles. Any dispute arising out of or in connection with these
              Terms shall be subject to the exclusive jurisdiction of the competent courts in India.
            </p>
            <p className="mt-2">
              We encourage you to first{' '}
              <Link href="/contact" className="text-amber-600 underline underline-offset-2">contact us</Link>{' '}
              to attempt an amicable resolution before initiating any legal proceedings.
            </p>
          </section>

          {/* 18 — MANDATORY under IT Rules 2021 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">18. Grievance Officer</h2>
            <div className="bg-white border-2 border-amber-200 rounded-xl p-5">
              <p className="text-xs font-bold uppercase tracking-widest text-amber-600 mb-3">
                Mandatory under Rule 3(2) of the IT (Intermediary Guidelines) Rules 2021
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex gap-3">
                  <span className="text-stone-400 w-28 flex-shrink-0">Name</span>
                  <span className="text-stone-800 font-semibold">Aditya Kakade</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-stone-400 w-28 flex-shrink-0">Designation</span>
                  <span className="text-stone-700">Grievance Officer, FrameAI</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-stone-400 w-28 flex-shrink-0">Contact</span>
                  <Link href="/contact" className="text-amber-600 underline underline-offset-2">
                    Contact page →
                  </Link>
                </div>
                <div className="flex gap-3">
                  <span className="text-stone-400 w-28 flex-shrink-0">Country</span>
                  <span className="text-stone-700">India</span>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t border-stone-100 text-xs text-stone-500 space-y-1.5">
                <p>
                  Grievances must be submitted in writing via the{' '}
                  <Link href="/contact" className="text-amber-600 underline underline-offset-2">Contact page</Link>.
                  The Grievance Officer will <strong className="text-stone-700">acknowledge your grievance within 24 hours</strong> and
                  endeavour to resolve it within <strong className="text-stone-700">15 working days</strong> of receipt
                  (30 days for e-commerce related complaints under the Consumer Protection Rules 2020).
                </p>
                <p>If your grievance is not resolved satisfactorily, you may escalate to:</p>
                <ul className="list-disc list-inside space-y-0.5 ml-1">
                  <li>The <strong className="text-stone-700">Data Protection Board of India</strong> (for data-related complaints under the DPDP Act 2023)</li>
                  <li>The <strong className="text-stone-700">National Consumer Helpline</strong> at 1800-11-4000 (toll-free)</li>
                  <li>The Adjudicating Officer under the Information Technology Act 2000</li>
                  <li>The appropriate consumer forum under the Consumer Protection Act 2019</li>
                </ul>
              </div>
            </div>
          </section>

          {/* 19 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">19. Security</h2>
            <p>
              We implement reasonable technical and organisational security measures in accordance
              with IS/ISO/IEC 27001 standards to protect your sensitive personal data from
              unauthorised access, disclosure, alteration, or destruction. However, no method of
              transmission or storage over the internet is 100% secure. You use the service at
              your own risk.
            </p>
          </section>

          {/* 20 */}
          <section>
            <h2 className="text-base font-bold text-stone-900 mb-2">20. Contact</h2>
            <p>
              For general queries, privacy requests, or legal notices, visit our{' '}
              <Link href="/contact" className="text-amber-600 underline underline-offset-2">Contact page</Link>.
            </p>
          </section>

          <p className="text-xs text-stone-400 pt-4 border-t border-stone-100">
            These Terms were prepared in good faith to reflect applicable Indian law as of {EFFECTIVE_DATE}.
            They should be reviewed by a qualified legal professional before commercial use.
            FrameAI is a prototype product and this document will be updated as the service evolves.
          </p>

        </div>
      </article>
    </main>
  )
}
