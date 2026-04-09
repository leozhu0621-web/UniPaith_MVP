import { X, Check, Kanban, ListChecks, Megaphone, BarChart3, BrainCircuit, MessageSquare } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const comparisons = [
  {
    before: "Manual review of thousands of apps",
    after: "AI-prioritized review queue with rubric-aligned summaries",
  },
  {
    before: "Inconsistent formats from every applicant",
    after: "Standardized, structured profiles with verified documents",
  },
  {
    before: "Fragmented communication across channels",
    after: "Unified inbox with application-linked messaging",
  },
  {
    before: "Guessing at pipeline and conversion",
    after: "Real-time analytics dashboard with funnel insights",
  },
  {
    before: "Compliance gaps and integrity risks",
    after: "Built-in verification, anomaly detection, and audit trails",
  },
];

const features = [
  { icon: Kanban, label: "Pipeline Board" },
  { icon: ListChecks, label: "Review Queue" },
  { icon: Megaphone, label: "Campaign Tools" },
  { icon: BarChart3, label: "Analytics Dashboard" },
  { icon: BrainCircuit, label: "AI Triage" },
  { icon: MessageSquare, label: "Messaging Hub" },
];

const InstitutionsSection = () => (
  <section id="institutions" className="py-24 px-4 sm:px-6 lg:px-8 bg-forest-50">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <span className="inline-block bg-primary/10 text-primary text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">
            For Institutions
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
            Admissions operations, reimagined
          </h2>
          <p className="text-muted-foreground max-w-lg mx-auto text-lg">
            The AI-powered system that works alongside your existing tools &mdash; not against them.
          </p>
        </div>
      </ScrollReveal>

      {/* Before / After comparison table */}
      <div className="bg-card rounded-2xl border shadow-sm overflow-hidden">
        <div className="grid grid-cols-2 border-b">
          <ScrollReveal delay={100} variant="fade-left">
            <div className="p-6 sm:p-8 text-center bg-destructive/5">
              <h3 className="text-lg font-bold text-destructive font-heading">
                Before UniPaith
              </h3>
            </div>
          </ScrollReveal>
          <ScrollReveal delay={200} variant="fade-right">
            <div className="p-6 sm:p-8 text-center bg-primary/5">
              <h3 className="text-lg font-bold text-primary font-heading">
                With UniPaith
              </h3>
            </div>
          </ScrollReveal>
        </div>

        {comparisons.map((row, i) => (
          <ScrollReveal key={i} delay={300 + i * 150}>
            <div
              className={`grid grid-cols-2 transition-colors duration-200 hover:bg-muted/30 ${i < comparisons.length - 1 ? "border-b" : ""}`}
            >
              <div className="p-5 sm:p-6 flex items-start gap-3 bg-destructive/[0.02]">
                <X className="text-destructive flex-shrink-0 mt-0.5" size={18} />
                <p className="text-sm text-muted-foreground">{row.before}</p>
              </div>
              <div className="p-5 sm:p-6 flex items-start gap-3 bg-primary/[0.02]">
                <Check className="text-primary flex-shrink-0 mt-0.5" size={18} />
                <p className="text-sm text-foreground font-medium">{row.after}</p>
              </div>
            </div>
          </ScrollReveal>
        ))}
      </div>

      {/* What you get feature grid */}
      <ScrollReveal delay={1000}>
        <div className="mt-16">
          <h3 className="text-center text-xl font-bold text-foreground font-heading mb-8">
            What you get
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-6">
            {features.map((feat, i) => (
              <div
                key={i}
                className="flex flex-col items-center gap-3 bg-card rounded-xl border p-6 hover-lift"
              >
                <feat.icon className="text-primary" size={28} strokeWidth={1.4} />
                <span className="text-sm font-semibold text-foreground">{feat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </ScrollReveal>

      {/* Integration note */}
      <ScrollReveal delay={1200}>
        <p className="mt-10 text-center text-sm text-muted-foreground italic">
          Works alongside Slate, Salesforce, and your existing SIS. No rip-and-replace required.
        </p>
      </ScrollReveal>
    </div>
  </section>
);

export default InstitutionsSection;
