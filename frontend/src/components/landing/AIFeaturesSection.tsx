import { Sparkles, FileSearch, Activity, AlertTriangle } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const features = [
  {
    icon: Sparkles,
    title: "Smart Matching",
    description: "Our AI doesn't just filter — it understands. It analyzes your profile against thousands of program criteria and surfaces the schools where you'll thrive. No more scrolling through endless lists.",
    color: "text-gold-600",
    bg: "bg-gold-100",
    mockBg: "from-gold-100 to-gold-50",
  },
  {
    icon: FileSearch,
    title: "Document Intelligence",
    description: "Upload your transcripts, essays, and certificates once. Our AI extracts, structures, and verifies everything — turning messy documents into clean, actionable data for institutions.",
    color: "text-primary",
    bg: "bg-primary/10",
    mockBg: "from-forest-100 to-forest-50",
  },
  {
    icon: Activity,
    title: "Readiness Diagnostics",
    description: "Before you hit submit, know exactly where you stand. Your readiness score shows strengths, flags gaps, and tells you what to improve — like a GPS for your application.",
    color: "text-forest-500",
    bg: "bg-forest-100",
    mockBg: "from-forest-200/50 to-forest-100/50",
  },
  {
    icon: AlertTriangle,
    title: "Integrity Shield",
    description: "Every application passes through anomaly detection, plagiarism checks, and document verification. Institutions get peace of mind. Students get a fair process.",
    color: "text-primary",
    bg: "bg-primary/10",
    mockBg: "from-forest-100 to-forest-50",
  },
];

const AIFeaturesSection = () => (
  <section id="ai-features" className="py-24 px-4 sm:px-6 lg:px-8 bg-card">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-20">
          <span className="inline-flex items-center gap-1.5 bg-gold-100 text-gold-700 text-sm font-medium rounded-full px-5 py-1.5 mb-4">
            <Sparkles size={14} /> Powered by AI
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">Intelligence at every step</h2>
          <p className="text-muted-foreground max-w-xl mx-auto text-lg">From discovery to decision, AI works behind the scenes so you can focus on what matters.</p>
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
    </div>
  </section>
);

export default AIFeaturesSection;
