import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/shadcn/accordion";
import ScrollReveal from "./ScrollReveal";
import { GraduationCap, Building2 } from "lucide-react";

const studentFAQs = [
  { q: "Is UniPaith really free for students?", a: "Yes, always free. We're funded by institutional partnerships, so students never pay a cent." },
  { q: "How does the AI matching work?", a: "Our AI analyzes your profile, preferences, and goals to recommend best-fit programs — no guesswork, just data-driven guidance." },
  { q: "Can I apply to multiple universities at once?", a: "Absolutely. One profile powers all your applications. Fill it once, apply everywhere." },
  { q: "Is my data safe?", a: "Your data is encrypted end-to-end and never shared without your explicit consent. Your privacy is our priority." },
];

const institutionFAQs = [
  { q: "How does UniPaith help us find better candidates?", a: "AI matching surfaces students whose profiles align with your programs, improving yield and fit rates significantly." },
  { q: "What does integration look like?", a: "A simple API or dashboard — no need to overhaul your existing admissions systems. We fit into your workflow." },
  { q: "How is UniPaith priced for institutions?", a: "Flexible plans based on institution size and needs. Request a demo for a tailored quote." },
  { q: "Can we customize our institution profile?", a: "Yes, showcase your programs, campus culture, and unique strengths to attract the right students." },
];

const FAQSection = () => (
  <section className="py-24 px-4 bg-background">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal>
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4 font-heading">
            Frequently Asked Questions
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Everything you need to know about UniPaith — whether you're a student or an institution.
          </p>
        </div>
      </ScrollReveal>

      <div className="grid md:grid-cols-2 gap-10">
        <ScrollReveal variant="fade-left" delay={100}>
          <div className="flex items-center gap-2 mb-4">
            <GraduationCap className="h-5 w-5 text-gold-500" />
            <h3 className="text-xl font-semibold text-foreground font-heading">For Students</h3>
          </div>
          <Accordion type="single" collapsible className="w-full">
            {studentFAQs.map((faq, i) => (
              <AccordionItem key={i} value={`student-${i}`}>
                <AccordionTrigger className="text-left text-foreground hover:no-underline hover:text-gold-600 transition-colors">
                  {faq.q}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  {faq.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>

        <ScrollReveal variant="fade-right" delay={200}>
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="h-5 w-5 text-primary" />
            <h3 className="text-xl font-semibold text-foreground font-heading">For Institutions</h3>
          </div>
          <Accordion type="single" collapsible className="w-full">
            {institutionFAQs.map((faq, i) => (
              <AccordionItem key={i} value={`institution-${i}`}>
                <AccordionTrigger className="text-left text-foreground hover:no-underline hover:text-primary transition-colors">
                  {faq.q}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  {faq.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>
      </div>
    </div>
  </section>
);

export default FAQSection;
