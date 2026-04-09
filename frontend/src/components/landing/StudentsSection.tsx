import { UserCircle, Search, Send } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const steps = [
  {
    icon: UserCircle,
    title: "Build Your Universal Profile",
    description: "Create one comprehensive profile with your academics, activities, essays, and documents. Write it once — use it everywhere.",
    color: "text-gold-600",
    bg: "bg-gold-100",
    line: "bg-gold-500",
  },
  {
    icon: Search,
    title: "Discover & Match Programs",
    description: "Our AI analyzes your profile against thousands of program criteria and recommends schools where you're a genuine fit — not just a name on a list.",
    color: "text-primary",
    bg: "bg-primary/10",
    line: "bg-primary",
  },
  {
    icon: Send,
    title: "Apply & Track Everything",
    description: "Submit applications to multiple schools from a single dashboard. Track every status, deadline, and update in one place.",
    color: "text-forest-500",
    bg: "bg-forest-100",
    line: "bg-forest-500",
  },
];

const StudentsSection = () => (
  <section id="students" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-20">
          <span className="inline-block bg-gold-100 text-gold-700 text-sm font-medium rounded-full px-4 py-1.5 mb-4 uppercase tracking-wide">For Students</span>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">Your path, simplified</h2>
          <p className="text-muted-foreground max-w-lg mx-auto text-lg">From overwhelmed to admitted — in three steps.</p>
        </div>
      </ScrollReveal>

      <div className="relative">
        <div className="hidden md:block absolute left-1/2 top-0 bottom-0 w-0.5 bg-border -translate-x-1/2" />

        <div className="space-y-16 md:space-y-24">
          {steps.map((step, i) => (
            <ScrollReveal key={i} delay={i * 250} variant={i % 2 === 0 ? "fade-left" : "fade-right"}>
              <div className={`flex flex-col md:flex-row items-center gap-8 ${i % 2 === 1 ? "md:flex-row-reverse" : ""}`}>
                <div className="flex-1 text-center md:text-left">
                  <div className="inline-flex items-center gap-2 mb-3">
                    <span className={`w-8 h-8 rounded-full ${step.line} text-card flex items-center justify-center text-sm font-bold`}>
                      {i + 1}
                    </span>
                    <h3 className="text-xl font-bold text-foreground font-heading">{step.title}</h3>
                  </div>
                  <p className="text-muted-foreground leading-relaxed max-w-md">{step.description}</p>
                </div>

                <div className="hidden md:flex w-5 h-5 rounded-full border-4 border-background shadow-md flex-shrink-0 z-10">
                  <div className={`w-full h-full rounded-full ${step.line}`} />
                </div>

                <div className="flex-1">
                  <div className={`${step.bg} rounded-2xl p-8 flex items-center justify-center hover-lift group`}>
                    <step.icon className={`${step.color} transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`} size={64} strokeWidth={1.2} />
                  </div>
                </div>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </div>
  </section>
);

export default StudentsSection;
