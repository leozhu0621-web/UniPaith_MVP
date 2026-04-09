import { UserCircle, Search, Send, MessageCircle } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const steps = [
  {
    icon: UserCircle,
    title: "Build Your Universal Profile",
    description:
      "One profile that works everywhere. Academics, activities, essays, documents \u2014 enter it once, reuse across every application. No more copy-pasting between portals.",
    color: "text-gold-600",
    bg: "bg-gold-100",
    line: "bg-gold-500",
  },
  {
    icon: Search,
    title: "Discover Programs That Actually Fit",
    description:
      "AI-powered matching based on your goals, budget, location, and academic profile. See why each program is recommended \u2014 with transparent reasoning, not a black box.",
    color: "text-primary",
    bg: "bg-primary/10",
    line: "bg-primary",
  },
  {
    icon: Send,
    title: "Apply & Track Everything",
    description:
      "Submit to multiple programs from one dashboard. Track deadlines, manage documents, monitor every status update. Your entire application portfolio in one view.",
    color: "text-forest-500",
    bg: "bg-forest-100",
    line: "bg-forest-500",
  },
  {
    icon: MessageCircle,
    title: "Get Guided by Your AI Counselor",
    description:
      "Ask questions, get essay feedback, check your readiness score, explore financial aid options. Like having a knowledgeable advisor available 24/7 \u2014 for free.",
    color: "text-gold-600",
    bg: "bg-gold-100",
    line: "bg-forest-500",
  },
];

const featureChips = [
  "Essay Workshop",
  "Deadline Tracker",
  "Financial Aid",
  "Readiness Score",
  "Document Manager",
];

const StudentsSection = () => (
  <section id="students" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-20">
          <span className="inline-block bg-gold-100 text-gold-700 text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">
            For Students
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
            Your entire admissions journey. One place.
          </h2>
          <p className="text-muted-foreground max-w-lg mx-auto text-lg">
            From profile to acceptance letter &mdash; guided every step.
          </p>
        </div>
      </ScrollReveal>

      <div className="relative">
        <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-border -translate-x-1/2" />

        <div className="space-y-16 md:space-y-24">
          {steps.map((step, i) => (
            <ScrollReveal
              key={i}
              delay={i * 250}
              variant={i % 2 === 0 ? "fade-left" : "fade-right"}
            >
              <div
                className={`flex flex-col md:flex-row items-center gap-8 ${i % 2 === 1 ? "md:flex-row-reverse" : ""}`}
              >
                <div className="flex-1 text-center md:text-left">
                  <div className="inline-flex items-center gap-2 mb-3">
                    <span
                      className={`w-8 h-8 rounded-full ${step.line} text-card flex items-center justify-center text-sm font-bold`}
                    >
                      {i + 1}
                    </span>
                    <h3 className="text-xl font-bold text-foreground font-heading">
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-muted-foreground leading-relaxed max-w-md">
                    {step.description}
                  </p>
                </div>

                <div className="hidden md:flex w-5 h-5 rounded-full border-4 border-background shadow-md flex-shrink-0 z-10">
                  <div className={`w-full h-full rounded-full ${step.line}`} />
                </div>

                <div className="flex-1">
                  <div
                    className={`${step.bg} rounded-2xl p-8 flex items-center justify-center hover-lift group`}
                  >
                    <step.icon
                      className={`${step.color} transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}
                      size={64}
                      strokeWidth={1.2}
                    />
                  </div>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>

      <ScrollReveal delay={1200}>
        <div className="mt-16 flex flex-wrap justify-center gap-3">
          {featureChips.map((chip) => (
            <span
              key={chip}
              className="inline-block bg-forest-100 text-forest-700 text-xs font-medium rounded-full px-3 py-1.5 border border-forest-200"
            >
              {chip}
            </span>
          ))}
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default StudentsSection;
