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
    a: "Common App handles submission to ~1,100 member schools. UniPaith handles your entire journey — matching, readiness, applications, tracking, and offer comparison across any program worldwide.",
  },
  {
    q: "Is it really free for students?",
    a: "Yes. Institutions pay for their operations platform. Students pay nothing — no trial, no premium tier, no credit card.",
  },
  {
    q: "Does the AI make decisions for me?",
    a: "No. It recommends programs and shows you why. Every decision — where to apply, what to submit, which offer to accept — is yours.",
  },
];

const institutionFAQs = [
  {
    q: "Do we need to replace our current CRM?",
    a: "No. UniPaith works alongside Slate, Salesforce, or your existing system. It feeds structured data and AI insights into your workflow.",
  },
  {
    q: "How is this different from Element451 or EAB?",
    a: "Those are institution-side CRMs. UniPaith is a two-sided platform — it connects you to students with structured, standardized profiles, plus AI-assisted review and communication.",
  },
  {
    q: "What does pricing look like?",
    a: "Flexible plans based on institution size and volume. Free entry tier for eligible community colleges and regional institutions.",
  },
];

const FAQSection = () => (
  <section className="py-24 px-4 bg-offwhite">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal>
        <div className="text-center mb-14">
          <h2 className="text-3xl md:text-4xl font-bold text-charcoal mb-4 font-heading">
            Frequently Asked Questions
          </h2>
        </div>
      </ScrollReveal>

      <div className="grid md:grid-cols-2 gap-10">
        <ScrollReveal variant="fade-left" delay={100}>
          <div className="flex items-center gap-2 mb-4">
            <GraduationCap className="h-5 w-5 text-student" />
            <h3 className="text-lg font-semibold text-charcoal font-heading">For Students</h3>
          </div>
          <Accordion type="single" collapsible className="w-full">
            {studentFAQs.map((faq, i) => (
              <AccordionItem key={i} value={`student-${i}`}>
                <AccordionTrigger className="text-left text-charcoal hover:no-underline hover:text-student transition-colors text-sm">
                  {faq.q}
                </AccordionTrigger>
                <AccordionContent className="text-gray-500 text-sm">{faq.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>

        <ScrollReveal variant="fade-right" delay={200}>
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="h-5 w-5 text-charcoal" />
            <h3 className="text-lg font-semibold text-charcoal font-heading">For Institutions</h3>
          </div>
          <Accordion type="single" collapsible className="w-full">
            {institutionFAQs.map((faq, i) => (
              <AccordionItem key={i} value={`institution-${i}`}>
                <AccordionTrigger className="text-left text-charcoal hover:no-underline hover:text-student transition-colors text-sm">
                  {faq.q}
                </AccordionTrigger>
                <AccordionContent className="text-gray-500 text-sm">{faq.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </ScrollReveal>
      </div>
    </div>
  </section>
);

export default FAQSection;
