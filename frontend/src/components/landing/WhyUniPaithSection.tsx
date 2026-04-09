import { Layers, Database, Globe } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const differentiators = [
  {
    icon: Layers,
    title: "Not just an application portal",
    description: "Common App and UCAS handle submission. UniPaith handles the entire journey — from profile building and matching to readiness, application management, and decision tracking.",
    color: "text-gold-600",
    bg: "bg-gold-100",
  },
  {
    icon: Database,
    title: "Not just a CRM",
    description: "Slate and Salesforce manage your workflow. UniPaith feeds them better data — structured student profiles, AI-prioritized queues, and standardized application packets.",
    color: "text-primary",
    bg: "bg-primary/10",
  },
  {
    icon: Globe,
    title: "Not just a marketplace",
    description: "ApplyBoard and IDP route students. UniPaith gives both sides a shared workflow rail — transparent, governed, and built to compound value as the network grows.",
    color: "text-forest-500",
    bg: "bg-forest-100",
  },
];

const WhyUniPaithSection = () => (
  <section id="why-unipaith" className="py-24 px-4 sm:px-6 lg:px-8 bg-background">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-foreground mb-4 font-heading">Why UniPaith?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto text-lg leading-relaxed">
            The admissions market is full of point solutions. Application portals that stop at submission. CRMs that never see the student. Marketplaces that don't touch operations. UniPaith connects what others keep separate.
          </p>
        </div>
      </ScrollReveal>

      <div className="grid md:grid-cols-3 gap-8 mb-16">
        {differentiators.map((d, i) => (
          <ScrollReveal key={i} delay={i * 150} variant="fade-up">
            <div className="bg-card rounded-2xl border p-8 hover-lift transition-all h-full group">
              <div className={`w-14 h-14 rounded-xl ${d.bg} flex items-center justify-center mb-5`}>
                <d.icon className={`${d.color} transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3`} size={28} />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-3 font-heading">{d.title}</h3>
              <p className="text-muted-foreground leading-relaxed text-sm">{d.description}</p>
            </div>
          </ScrollReveal>
        ))}
      </div>

      <ScrollReveal delay={300} variant="fade-up">
        <p className="text-center text-lg font-semibold text-foreground max-w-xl mx-auto">
          The moat isn't AI alone. It's workflow + data + trust across both sides.
        </p>
      </ScrollReveal>
    </div>
  </section>
);

export default WhyUniPaithSection;
