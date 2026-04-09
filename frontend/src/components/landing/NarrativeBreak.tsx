import ScrollReveal from "./ScrollReveal";

interface NarrativeBreakProps {
  text: string;
  variant?: "fade-up" | "scale-up" | "blur-in";
}

const NarrativeBreak = ({ text, variant = "blur-in" }: NarrativeBreakProps) => (
  <div className="py-16 px-4 sm:px-6 lg:px-8 bg-forest-800">
    <ScrollReveal variant={variant}>
      <div className="max-w-3xl mx-auto text-center">
        <div className="w-12 h-0.5 bg-gold-500 mx-auto mb-6" />
        <p className="text-2xl sm:text-3xl lg:text-4xl font-bold text-center text-background max-w-3xl mx-auto leading-snug italic font-heading">
          {text}
        </p>
      </div>
    </ScrollReveal>
  </div>
);

export default NarrativeBreak;
