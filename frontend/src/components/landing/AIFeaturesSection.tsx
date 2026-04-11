import { Link } from "react-router-dom";
import { Brain, FileSearch, Target, Shield, Lock, User, ClipboardCheck, ArrowRight } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const features = [
  {
    icon: Brain,
    title: "Explainable Matching",
    description: "See exactly why a program was recommended — tied to your goals and profile. No black boxes.",
    color: "text-student",
    bg: "bg-student-mist",
    mockBg: "from-mist to-cloud",
  },
  {
    icon: FileSearch,
    title: "Document Intelligence",
    description: "Upload once. AI extracts, structures, and verifies — turning documents into clean data institutions trust.",
    color: "text-charcoal",
    bg: "bg-charcoal/10",
    mockBg: "from-gray-100 to-cloud",
  },
  {
    icon: Target,
    title: "Readiness Diagnostics",
    description: "Know where you stand before you submit. Strengths, gaps, and a clear preparation path.",
    color: "text-student",
    bg: "bg-student-mist",
    mockBg: "from-mist to-cloud",
  },
  {
    icon: Shield,
    title: "Integrity & Compliance",
    description: "Anomaly detection, document verification, full audit trails. FERPA-ready, GDPR-compliant.",
    color: "text-charcoal",
    bg: "bg-charcoal/10",
    mockBg: "from-gray-100 to-cloud",
  },
];

const trustBadges = [
  { icon: Shield, label: "FERPA Ready" },
  { icon: Lock, label: "End-to-End Encrypted" },
  { icon: User, label: "Human-in-the-Loop" },
  { icon: ClipboardCheck, label: "Full Audit Trails" },
];

const AIFeaturesSection = () => (
  <section id="ai-features" className="py-24 px-4 sm:px-6 lg:px-8 bg-white">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <span className="inline-flex items-center gap-1.5 bg-student-mist text-student text-sm font-medium rounded-full px-5 py-1.5 mb-4">
            <Brain size={14} /> Powered by AI
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-charcoal mb-4 font-heading">Intelligence you can trust</h2>
          <p className="text-gray-500 max-w-xl mx-auto text-lg">Every AI output comes with reasoning. Every decision stays with humans.</p>
        </div>
      </ScrollReveal>

      <div className="space-y-16">
        {features.map((f, i) => (
          <ScrollReveal key={i} delay={150} variant={i % 2 === 0 ? "fade-left" : "fade-right"}>
            <div className={`flex flex-col ${i % 2 === 1 ? "md:flex-row-reverse" : "md:flex-row"} items-center gap-10`}>
              <div className="flex-1">
                <div className={`w-12 h-12 rounded-xl ${f.bg} flex items-center justify-center mb-4 group`}>
                  <f.icon className={`${f.color} transition-transform duration-300 group-hover:scale-110`} size={24} />
                </div>
                <h3 className="text-xl font-bold text-charcoal mb-2 font-heading">{f.title}</h3>
                <p className="text-gray-500 leading-relaxed text-sm">{f.description}</p>
              </div>

              <div className="flex-1 w-full">
                <div className={`bg-gradient-to-br ${f.mockBg} rounded-2xl border border-gray-200 p-8 h-44 flex items-center justify-center`}>
                  <div className="bg-white/80 backdrop-blur rounded-xl p-5 shadow-lg border border-gray-200 w-full max-w-xs hover-lift">
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-8 h-8 rounded-lg ${f.bg} flex items-center justify-center`}>
                        <f.icon className={f.color} size={16} />
                      </div>
                      <div className="w-24 h-2.5 bg-gray-200 rounded-full" />
                    </div>
                    <div className="space-y-2">
                      <div className="w-full h-2 bg-gray-200 rounded-full" />
                      <div className="w-4/5 h-2 bg-gray-200 rounded-full" />
                      <div className="w-3/5 h-2 bg-gray-200 rounded-full" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </ScrollReveal>
        ))}
      </div>

      <ScrollReveal delay={200} variant="fade-up">
        <div className="mt-16 flex flex-wrap justify-center gap-8 sm:gap-12">
          {trustBadges.map((badge, i) => (
            <div key={i} className="flex items-center gap-2 text-gray-500">
              <badge.icon size={18} className="text-student" />
              <span className="text-sm font-medium">{badge.label}</span>
            </div>
          ))}
        </div>
        <div className="mt-6 text-center">
          <Link
            to="/engine"
            className="inline-flex items-center gap-1 text-sm font-medium text-student hover:text-student-hover transition-colors"
          >
            Explore the AI engine <ArrowRight size={14} />
          </Link>
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default AIFeaturesSection;
