import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/shadcn/accordion";
import ScrollReveal from "./ScrollReveal";
import { GraduationCap, Building2 } from "lucide-react";

const studentFAQs = [
  {
    q: "How is UniPaith different from Common App?",
    a: "Common App is an application rail for ~1,100 member schools. UniPaith is a full admissions workflow \u2014 profile, matching, readiness diagnostics, essay support, deadline tracking, and application management. You build one profile and use it everywhere, with AI that explains why programs fit you.",
  },
  {
    q: "Is UniPaith really free for students?",
    a: "Yes, always. Core features are free \u2014 profile, matching, applications, and tracking. We\u2019re funded by institutional partnerships, so students never pay to apply.",
  },
  {
    q: "Does the AI make decisions for me?",
    a: "Never. AI provides recommendations with transparent reasoning, flags what you\u2019re missing, and helps you improve. Every decision \u2014 where to apply, what to submit, which offer to accept \u2014 is yours.",
  },
  {
    q: "What happens to my data?",
    a: "Your data is yours. Encrypted end-to-end, never sold, and only shared with programs you choose to apply to. FERPA-ready and GDPR-compliant from day one.",
  },
  {
    q: "Can I still apply through other portals?",
    a: "Absolutely. UniPaith works alongside other application systems. Use it for the programs that accept it, and track everything else in the same dashboard.",
  },
];

const institutionFAQs = [
  {
    q: "Do we need to replace our current CRM?",
    a: "No. UniPaith is designed to work alongside Slate, Salesforce, or whatever system you already use. Think of it as an intelligent layer that feeds structured data and AI-supported insights into your existing workflow.",
  },
  {
    q: "How long does setup take?",
    a: "Most institutions are live within 2 weeks. We handle data migration, program listing setup, and staff onboarding. No heavy IT lift required.",
  },
  {
    q: "How is this different from Element451 or EAB?",
    a: "Those are institution-side CRMs. UniPaith is a two-sided workflow rail \u2014 it connects you to a network of students with structured, standardized profiles. You get better applicant data from day one, plus AI-assisted review, triage, and communication.",
  },
  {
    q: "Is the AI trustworthy for admissions decisions?",
    a: "Our AI never makes admissions decisions. It supports your team with rubric-aligned summaries, anomaly flags, and queue prioritization \u2014 all with full audit trails and human override at every step.",
  },
  {
    q: "What does pricing look like?",
    a: "Flexible plans based on institution size and volume. Free entry tier available for eligible community colleges and regional institutions. Request a demo for a tailored quote.",
  },
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
            Everything you need to know about UniPaith &mdash; whether you&rsquo;re a student or an
            institution.
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
                <AccordionContent className="text-muted-foreground">{faq.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>

        <ScrollReveal variant="fade-right" delay={200}>
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="h-5 w-5 text-primary" />
            <h3 className="text-xl font-semibold text-foreground font-heading">
              For Institutions
            </h3>
          </div>
          <Accordion type="single" collapsible className="w-full">
            {institutionFAQs.map((faq, i) => (
              <AccordionItem key={i} value={`institution-${i}`}>
                <AccordionTrigger className="text-left text-foreground hover:no-underline hover:text-primary transition-colors">
                  {faq.q}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">{faq.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>
      </div>
    </div>
  </section>
);

export default FAQSection;
