import { Layers, Database, Globe } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const differentiators = [
  {
    icon: Layers,
    title: "Not just an application portal",
    description: "Common App and UCAS handle submission. UniPaith handles the entire journey — from profile building and matching to readiness, application management, and decision tracking.",
    color: "text-student",
    bg: "bg-student-mist",
  },
  {
    icon: Database,
    title: "Not just a CRM",
    description: "Slate and Salesforce manage your workflow. UniPaith feeds them better data — structured student profiles, AI-prioritized queues, and standardized application packets.",
    color: "text-charcoal",
    bg: "bg-charcoal/10",
  },
  {
    icon: Globe,
    title: "Not just a marketplace",
    description: "ApplyBoard and IDP route students. UniPaith gives both sides a shared workflow rail — transparent, governed, and built to compound value as the network grows.",
    color: "text-student",
    bg: "bg-student-mist",
  },
];

const WhyUniPaithSection = () => (
  <section id="why-unipaith" className="py-24 px-4 sm:px-6 lg:px-8 bg-offwhite">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-charcoal mb-4 font-heading">Why UniPaith?</h2>
          <p className="text-gray-500 max-w-2xl mx-auto text-lg leading-relaxed">
            The admissions market is full of point solutions. UniPaith connects what others keep separate.
          </p>
        </div>
      </ScrollReveal>

      <div className="grid md:grid-cols-3 gap-8 mb-16">
        {differentiators.map((d, i) => (
          <ScrollReveal key={i} delay={i * 150} variant="fade-up">
            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover-lift transition-all h-full group">
              <div className={`w-14 h-14 rounded-xl ${d.bg} flex items-center justify-center mb-5`}>
                <d.icon className={`${d.color} transition-transform duration-300 group-hover:scale-110`} size={28} />
              </div>
              <h3 className="text-xl font-bold text-charcoal mb-3 font-heading">{d.title}</h3>
              <p className="text-gray-500 leading-relaxed text-sm">{d.description}</p>
            </div>
          </ScrollReveal>
        ))}
      </div>

      <ScrollReveal delay={300} variant="fade-up">
        <p className="text-center text-lg font-semibold text-charcoal max-w-xl mx-auto">
          The moat isn&rsquo;t AI alone. It&rsquo;s workflow + data + trust across both sides.
        </p>
      </ScrollReveal>
    </div>
  </section>
);

export default WhyUniPaithSection;
