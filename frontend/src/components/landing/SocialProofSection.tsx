import ScrollReveal from "./ScrollReveal";
import AnimatedCounter from "./AnimatedCounter";

const stats = [
  { end: 10000, suffix: "+", label: "Programs Indexed" },
  { end: 50, suffix: "+", label: "Countries Covered" },
  { end: 200, suffix: "+", label: "Institutions Engaged" },
  { value: "24/7", label: "AI Counselor Available" },
];

const founders = [
  {
    name: "Leo Zhu",
    role: "Co-Founder · Product & Operations",
    desc: "International student turned entrepreneur — navigated the admissions system firsthand.",
    initials: "LZ",
    bg: "bg-brand-amber-100",
    textColor: "text-brand-amber-700",
  },
  {
    name: "Rick Arrowood",
    role: "Co-Founder · Strategy & Partnerships",
    desc: "Education executive and academic — decades on the institutional side of admissions.",
    initials: "RA",
    bg: "bg-brand-slate-100",
    textColor: "text-brand-slate-700",
  },
];

const SocialProofSection = () => (
  <section className="py-24 px-4 sm:px-6 lg:px-8 bg-card">
    <div className="max-w-4xl mx-auto">
      {/* By the numbers */}
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

      <div className="border-t my-16" />

      {/* Founders */}
      <ScrollReveal variant="blur-in">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-6 text-foreground font-heading">
          Built by people who've lived both sides
        </h2>
        <p className="text-center text-muted-foreground mb-16 max-w-2xl mx-auto text-lg leading-relaxed">
          UniPaith was co-founded by a former international student who navigated the system firsthand and an education executive who's spent decades on the institutional side. We've seen the broken parts from every angle — and we're building the fix.
        </p>
      </ScrollReveal>

      <div className="grid md:grid-cols-2 gap-8">
        {founders.map((f, i) => (
          <ScrollReveal key={i} delay={i * 200} variant={i === 0 ? "fade-left" : "fade-right"}>
            <div className="bg-background rounded-2xl border p-8 hover-lift text-center">
              <div className={`w-16 h-16 rounded-full ${f.bg} flex items-center justify-center mx-auto mb-4`}>
                <span className={`text-lg font-bold ${f.textColor}`}>{f.initials}</span>
              </div>
              <h3 className="text-xl font-bold text-foreground mb-1 font-heading">{f.name}</h3>
              <p className="text-sm text-primary font-medium mb-3">{f.role}</p>
              <p className="text-muted-foreground text-sm">{f.desc}</p>
            </div>
          </ScrollReveal>
        ))}
      </div>
    </div>
  </section>
);

export default SocialProofSection;
