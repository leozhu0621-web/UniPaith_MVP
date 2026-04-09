import { Link } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import ScrollReveal from "./ScrollReveal";
import AnimatedCounter from "./AnimatedCounter";

const stats = [
  { end: 10000, suffix: "+", label: "Programs Indexed" },
  { end: 50, suffix: "+", label: "Countries Covered" },
  { end: 200, suffix: "+", label: "Institutions Engaged" },
  { value: "24/7", label: "AI Counselor" },
];

const SocialProofSection = () => (
  <section className="py-24 px-4 sm:px-6 lg:px-8 bg-card">
    <div className="max-w-4xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wider mb-8">By the numbers</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold text-foreground font-heading mb-1">
                  {"end" in stat && stat.end ? (
                    <AnimatedCounter end={stat.end} suffix={stat.suffix} />
                  ) : (
                    <span>{stat.value}</span>
                  )}
                </div>
                <p className="text-sm text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </ScrollReveal>

      <div className="border-t my-12" />

      <ScrollReveal variant="blur-in">
        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-foreground mb-4 font-heading">
            Built by people who&rsquo;ve lived both sides
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-base leading-relaxed mb-6">
            Co-founded by a former international student who navigated the system firsthand
            and an education executive with decades on the institutional side.
          </p>
          <Link
            to="/about"
            className="inline-flex items-center gap-1 text-sm font-medium text-primary hover:text-brand-slate-700 transition-colors"
          >
            Meet the team <ArrowRight size={14} />
          </Link>
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default SocialProofSection;
