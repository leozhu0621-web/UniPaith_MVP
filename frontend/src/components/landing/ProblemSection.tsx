import { GraduationCap, Building2 } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import AnimatedCounter from "./AnimatedCounter";

const studentPains = [
  "Filling out the same forms across 12+ portals",
  "No clear signal on which programs actually fit",
  "Tracking deadlines across dozens of schools",
  "Paying $6K+ for agents who guess at eligibility",
];

const institutionPains = [
  "Manually reviewing thousands of inconsistent applications",
  "No standardized data to compare candidates fairly",
  "Growing compliance and integrity concerns",
  "Missing right-fit students who never surface",
];

const ProblemSection = () => (
  <section id="problem" className="py-24 px-4 sm:px-6 lg:px-8 bg-card">
    <div className="max-w-6xl mx-auto">
      <ScrollReveal variant="blur-in">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center text-foreground mb-6 font-heading">
          Admissions is still stuck in 2005
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto text-lg">
          Every year, millions of students and thousands of institutions go through the same broken cycle.
        </p>
      </ScrollReveal>

      <ScrollReveal delay={200}>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-4xl mx-auto mb-16">
          <div className="text-center">
            <div className="text-4xl sm:text-5xl font-bold text-brand-amber-500 mb-1 font-heading">
              <AnimatedCounter end={12} suffix="+" />
            </div>
            <p className="text-sm text-muted-foreground">apps per student</p>
          </div>
          <div className="text-center">
            <div className="text-4xl sm:text-5xl font-bold text-brand-slate-600 mb-1 font-heading">
              <AnimatedCounter end={40} suffix=" hrs" />
            </div>
            <p className="text-sm text-muted-foreground">repetitive paperwork</p>
          </div>
          <div className="text-center">
            <div className="text-4xl sm:text-5xl font-bold text-brand-green-500 mb-1 font-heading">
              <AnimatedCounter end={68} suffix="%" />
            </div>
            <p className="text-sm text-muted-foreground">feel overwhelmed</p>
          </div>
          <div className="text-center">
            <div className="text-4xl sm:text-5xl font-bold text-brand-amber-600 mb-1 font-heading">
              $<AnimatedCounter end={6} suffix="K+" />
            </div>
            <p className="text-sm text-muted-foreground">avg agent cost</p>
          </div>
        </div>
      </ScrollReveal>

      <div className="grid md:grid-cols-2 gap-8">
        <ScrollReveal delay={100} variant="fade-left">
          <div className="bg-background rounded-2xl border p-8 shadow-sm h-full">
            <div className="w-12 h-12 rounded-xl bg-brand-amber-100 flex items-center justify-center mb-5">
              <GraduationCap className="text-brand-amber-600" size={24} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-4 font-heading">Student side</h3>
            <ul className="space-y-3 text-muted-foreground text-sm">
              {studentPains.map((pain, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-brand-amber-500 mt-0.5">✦</span> {pain}
                </li>
              ))}
            </ul>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={300} variant="fade-right">
          <div className="bg-background rounded-2xl border p-8 shadow-sm h-full">
            <div className="w-12 h-12 rounded-xl bg-brand-slate-600/15 flex items-center justify-center mb-5">
              <Building2 className="text-brand-slate-600" size={24} />
            </div>
            <h3 className="text-xl font-bold text-foreground mb-4 font-heading">Institution side</h3>
            <ul className="space-y-3 text-muted-foreground text-sm">
              {institutionPains.map((pain, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-brand-slate-600 mt-0.5">✦</span> {pain}
                </li>
              ))}
            </ul>
          </div>
        </ScrollReveal>
      </div>

      <ScrollReveal delay={500}>
        <p className="text-center text-lg font-semibold text-foreground mt-12">
          UniPaith fixes both sides with one connected platform.
        </p>
      </ScrollReveal>
    </div>
  </section>
);

export default ProblemSection;
