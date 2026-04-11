import ScrollReveal from '@/components/landing/ScrollReveal'
import { BookOpen } from 'lucide-react'

export default function BlogPage() {
  return (
    <div className="pt-16">
      <section className="py-32 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto text-center">
          <ScrollReveal variant="blur-in">
            <div className="w-16 h-16 rounded-2xl bg-mist flex items-center justify-center mx-auto mb-6">
              <BookOpen className="text-harbor" size={32} />
            </div>
            <h1 className="text-4xl sm:text-5xl font-bold text-foreground mb-4 tracking-tight font-heading">Blog &amp; Resources</h1>
            <p className="text-xl text-muted-foreground mb-10">Insights on AI-powered admissions, student success, and institutional operations. Coming soon.</p>
          </ScrollReveal>

          <ScrollReveal delay={200}>
            <div className="bg-card rounded-2xl border p-8 max-w-md mx-auto">
              <h3 className="text-lg font-bold text-foreground mb-3 font-heading">Get notified when we launch</h3>
              <p className="text-sm text-muted-foreground mb-4">We&rsquo;ll send you a note when the first posts go live. No spam.</p>
              <div className="flex gap-2">
                <input
                  type="email"
                  placeholder="your@email.com"
                  className="flex-1 rounded-lg border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-harbor"
                />
                <button className="bg-harbor hover:bg-ink text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors">
                  Notify me
                </button>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>
    </div>
  )
}
