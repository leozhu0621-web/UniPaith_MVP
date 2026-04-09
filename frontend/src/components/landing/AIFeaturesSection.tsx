import { Brain, FileSearch, Target, Shield, Lock, User, ClipboardCheck } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const features = [
  {
    icon: Brain,
    title: "Explainable Matching",
    description: "See exactly why a program was recommended — tied to your goals, constraints, and profile. No black-box algorithms. Students understand their options; institutions understand their pipeline.",
    color: "text-brand-amber-600",
    bg: "bg-brand-amber-100",
    mockBg: "from-brand-amber-100 to-brand-amber-50",
  },
  {
    icon: FileSearch,
    title: "Document Intelligence",
    description: "Upload transcripts, essays, and certificates once. AI extracts, structures, and verifies — turning messy documents into clean, structured data that institutions can trust.",
    color: "text-primary",
    bg: "bg-primary/10",
    mockBg: "from-brand-slate-100 to-brand-slate-50",
  },
  {
    icon: Target,
    title: "Readiness Diagnostics",
    description: "Before you submit, know where you stand. Readiness scores show strengths, flag gaps, and guide preparation — like a GPS for your application journey.",
    color: "text-brand-slate-500",
    bg: "bg-brand-slate-100",
    mockBg: "from-brand-slate-200/50 to-brand-slate-100/50",
  },
  {
    icon: Shield,
    title: "Integrity & Compliance",
    description: "Anomaly detection, plagiarism checks, document verification, and full audit trails. FERPA-ready, GDPR-compliant, with human oversight at every decision point.",
    color: "text-primary",
    bg: "bg-primary/10",
    mockBg: "from-brand-slate-100 to-brand-slate-50",
  },
];

const trustBadges = [
  { icon: Shield, label: "FERPA Ready" },
  { icon: Lock, label: "End-to-End Encrypted" },
  { icon: User, label: "Human-in-the-Loop" },
  { icon: ClipboardCheck, label: "Full Audit Trails" },
];

const AIFeaturesSection = () => (
  <section id="ai-features" className="py-24 px-4 sm:px-6 lg:px-8 bg-card">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-20">
          <span className="inline-flex items-center gap-1.5 bg-brand-amber-100 text-brand-amber-700 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
            <Brain size={14} /> Powered by AI
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">Intelligence you can trust</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-lg">Every AI output comes with reasoning. Every decision stays with humans. That's not a disclaimer — it's how we're built.</p>
        </div>
      </ScrollReveal>

      <div className="space-y-20">
        {features.map((f, i) => (
          <ScrollReveal key={i} delay={150} variant={i % 2 === 0 ? "fade-left" : "fade-right"}>
            <div className={`flex flex-col ${i % 2 === 1 ? "md:flex-row-reverse" : "md:flex-row"} items-center gap-10`}>
              <div className="flex-1">
                <div className={`w-14 h-14 rounded-xl ${f.bg} flex items-center justify-center mb-5 group`}>
                  <f.icon className={`${f.color} transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`} size={28} />
                </div>
                <h3 className="text-2xl font-bold text-foreground mb-3 font-heading">{f.title}</h3>
                <p className="text-muted-foreground leading-relaxed text-base">{f.description}</p>
              </div>

              <div className="flex-1 w-full">
                <div className={`bg-gradient-to-br ${f.mockBg} rounded-2xl border p-8 h-48 sm:h-56 flex items-center justify-center`}>
                  <div className="bg-card/80 backdrop-blur rounded-xl p-6 shadow-lg border w-full max-w-xs hover-lift">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-8 h-8 rounded-lg ${f.bg} flex items-center justify-center`}>
                        <f.icon className={f.color} size={16} />
                      </div>
                      <div className="w-24 h-2.5 bg-muted rounded-full" />
                    </div>
                    <div className="space-y-2">
                      <div className="w-full h-2 bg-muted rounded-full" />
                      <div className="w-4/5 h-2 bg-muted rounded-full" />
                      <div className="w-3/5 h-2 bg-muted rounded-full" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </ScrollReveal>
        ))}
      </div>

      <ScrollReveal delay={200} variant="fade-up">
        <div className="mt-20 flex flex-wrap justify-center gap-8 sm:gap-12">
          {trustBadges.map((badge, i) => (
            <div key={i} className="flex items-center gap-2 text-muted-foreground">
              <badge.icon size={18} className="text-brand-slate-500" />
              <span className="text-sm font-medium">{badge.label}</span>
            </div>
          ))}
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default AIFeaturesSection;
