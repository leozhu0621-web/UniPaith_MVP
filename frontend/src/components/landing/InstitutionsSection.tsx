import { X, Check } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const comparisons = [
  { before: "Manually reviewing thousands of applications", after: "AI surfaces top candidates based on your criteria" },
  { before: "Inconsistent formats from every applicant", after: "Standardized, structured profiles for every student" },
  { before: "Compliance gaps and integrity risks", after: "Built-in verification, anomaly detection, and audit trails" },
  { before: "Guessing at yield and conversion rates", after: "Real-time analytics and pipeline insights" },
];

const InstitutionsSection = () => (
  <section id="institutions" className="py-24 px-4 sm:px-6 lg:px-8 bg-forest-50">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <span className="inline-block bg-primary/10 text-primary text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">For Institutions</span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">Admissions, transformed</h2>
          <p className="text-muted-foreground max-w-lg mx-auto text-lg">See the difference UniPaith makes — side by side.</p>
        </div>
      </ScrollReveal>

      <div className="bg-card rounded-2xl border shadow-sm overflow-hidden">
        <div className="grid grid-cols-2 border-b">
          <ScrollReveal delay={100} variant="fade-left">
            <div className="p-6 sm:p-8 text-center bg-destructive/5">
              <h3 className="text-lg font-bold text-destructive font-heading">Before UniPaith</h3>
            </div>
          </ScrollReveal>
          <ScrollReveal delay={200} variant="fade-right">
            <div className="p-6 sm:p-8 text-center bg-primary/5">
              <h3 className="text-lg font-bold text-primary font-heading">With UniPaith</h3>
            </div>
          </ScrollReveal>
        </div>

        {comparisons.map((row, i) => (
          <ScrollReveal key={i} delay={300 + i * 150}>
            <div className={`grid grid-cols-2 transition-colors duration-200 hover:bg-muted/30 ${i < comparisons.length - 1 ? "border-b" : ""}`}>
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
    </div>
  </section>
);

export default InstitutionsSection;
