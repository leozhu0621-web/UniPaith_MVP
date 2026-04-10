import { Link } from "react-router-dom";
import { UserCircle, Search, Send, MessageCircle, ArrowRight } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const steps = [
  {
    icon: UserCircle,
    title: "Build Your Universal Profile",
    description: "One profile that works everywhere — academics, activities, essays, documents.",
    color: "text-brand-amber-600",
    bg: "bg-brand-amber-100",
    line: "bg-brand-amber-500",
  },
  {
    icon: Search,
    title: "Get AI-Powered Matches",
    description: "Programs ranked by fit, with transparent reasoning tied to your goals.",
    color: "text-brand-green-600",
    bg: "bg-brand-green-100",
    line: "bg-brand-green-600",
  },
  {
    icon: Send,
    title: "Apply & Track Everything",
    description: "Deadlines, documents, status updates — one dashboard for your entire portfolio.",
    color: "text-brand-green-500",
    bg: "bg-brand-slate-100",
    line: "bg-brand-green-500",
  },
  {
    icon: MessageCircle,
    title: "AI Counselor 24/7",
    description: "Essay feedback, readiness scores, financial aid guidance — like a private advisor, free.",
    color: "text-brand-amber-600",
    bg: "bg-brand-amber-100",
    line: "bg-brand-green-500",
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
        <div className="text-center mb-16">
          <span className="inline-block bg-brand-amber-100 text-brand-amber-700 text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">
            For Students
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">
            Your private education advisor
          </h2>
          <p className="text-muted-foreground max-w-lg mx-auto text-lg">
            One profile. AI-powered matching. Guided applications.
          </p>
        </div>
      </ScrollReveal>

      <div className="relative">
        <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-border -translate-x-1/2" />

        <div className="space-y-16 md:space-y-20">
          {steps.map((step, i) => (
            <ScrollReveal
              key={i}
              delay={i * 200}
              variant={i % 2 === 0 ? "fade-left" : "fade-right"}
            >
              <div
                className={`flex flex-col md:flex-row items-center gap-8 ${i % 2 === 1 ? "md:flex-row-reverse" : ""}`}
              >
                <div className="flex-1 text-center md:text-left">
                  <div className="inline-flex items-center gap-2 mb-2">
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

      <ScrollReveal delay={1000}>
        <div className="mt-14 flex flex-wrap justify-center gap-3">
          {featureChips.map((chip) => (
            <span
              key={chip}
              className="inline-block bg-brand-green-100 text-brand-green-700 text-xs font-medium rounded-full px-3 py-1.5 border border-brand-green-200"
            >
              {chip}
            </span>
          ))}
        </div>
        <div className="mt-6 text-center">
          <Link
            to="/for-students"
            className="inline-flex items-center gap-1 text-sm font-medium text-brand-amber-600 hover:text-brand-amber-700 transition-colors"
          >
            See how it works <ArrowRight size={14} />
          </Link>
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default StudentsSection;
