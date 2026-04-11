import { Link } from "react-router-dom";
import { UserCircle, Search, Send, MessageCircle, ArrowRight } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const steps = [
  {
    icon: UserCircle,
    title: "One Profile, Every School",
    description: "Fill it out once. Use it for every application — transcripts, essays, activities, documents.",
    iconColor: "text-student",
    bg: "bg-student-mist",
    line: "bg-student",
  },
  {
    icon: Search,
    title: "See Programs That Actually Fit",
    description: "Matched to your goals, budget, and profile. You'll see exactly why each one was picked.",
    iconColor: "text-student",
    bg: "bg-student-mist",
    line: "bg-student",
  },
  {
    icon: Send,
    title: "Apply & Track in One Place",
    description: "Manage deadlines, upload documents, track status — stop juggling 10 different portals.",
    iconColor: "text-student",
    bg: "bg-student-mist",
    line: "bg-student",
  },
  {
    icon: MessageCircle,
    title: "Get Help When You Need It",
    description: "Essay feedback, cost breakdowns, readiness checks — a counselor who knows your file, anytime.",
    iconColor: "text-student",
    bg: "bg-gold-pale",
    line: "bg-student",
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
  <section id="students" className="py-24 px-4 sm:px-6 lg:px-8 bg-offwhite">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <span className="inline-block bg-student-mist text-student text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">
            For Students
          </span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-charcoal mb-4 font-heading">
            How it works for students
          </h2>
          <p className="text-gray-500 max-w-lg mx-auto text-lg">
            The same things a great counselor does &mdash; but faster, cheaper, and available whenever you need it.
          </p>
        </div>
      </ScrollReveal>

      <div className="relative">
        <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-200 -translate-x-1/2" />

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
                    <span className={`w-8 h-8 rounded-full ${step.line} text-white flex items-center justify-center text-sm font-bold`}>
                      {i + 1}
                    </span>
                    <h3 className="text-xl font-bold text-charcoal font-heading">
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-gray-500 leading-relaxed max-w-md">
                    {step.description}
                  </p>
                </div>

                <div className="hidden md:flex w-5 h-5 rounded-full border-4 border-cloud shadow-md flex-shrink-0 z-10">
                  <div className={`w-full h-full rounded-full ${step.line}`} />
                </div>

                <div className="flex-1">
                  <div className={`${step.bg} rounded-2xl p-8 flex items-center justify-center hover-lift group`}>
                    <step.icon
                      className={`${step.iconColor} transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`}
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
              className="inline-block bg-student-mist text-student text-xs font-medium rounded-full px-3 py-1.5 border border-student/20"
            >
              {chip}
            </span>
          ))}
        </div>
        <div className="mt-6 text-center">
          <Link
            to="/for-students"
            className="inline-flex items-center gap-1 text-sm font-medium text-student hover:text-student-hover transition-colors"
          >
            See how it works <ArrowRight size={14} />
          </Link>
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default StudentsSection;
