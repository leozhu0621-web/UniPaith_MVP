import { Link } from "react-router-dom";
import { Button } from "@/components/shadcn/button";
import { ArrowRight, ChevronDown } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const HeroSection = () => (
  <section className="relative min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 overflow-hidden">
    <div className="absolute inset-0 -z-10">
      <div className="absolute top-20 left-[10%] w-72 h-72 bg-forest-100/60 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-forest-300/30 rounded-full blur-3xl animate-float-slow" />
      <div className="absolute top-1/3 right-[20%] w-48 h-48 bg-gold-300/20 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
      <div className="absolute bottom-1/3 left-[20%] w-64 h-64 bg-forest-200/40 rounded-full blur-3xl animate-float-slow" style={{ animationDelay: "4s" }} />
    </div>

    <div className="max-w-5xl mx-auto text-center">
      <ScrollReveal variant="blur-in">
        <div className="inline-flex items-center gap-2 bg-forest-100 text-forest-700 rounded-full px-5 py-2 text-sm font-medium mb-8">
          The admissions infrastructure built for both sides
        </div>
      </ScrollReveal>

      <ScrollReveal delay={200} variant="scale-up">
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-foreground leading-[1.1] mb-8 tracking-tight font-heading">
          Apply once.{" "}
          <br className="hidden sm:block" />
          <span className="text-primary">Go anywhere.</span>
        </h1>
      </ScrollReveal>

      <ScrollReveal delay={400}>
        <p className="text-xl sm:text-2xl text-muted-foreground max-w-3xl mx-auto mb-6 leading-relaxed">
          Students get one portable profile to discover, match, and apply to programs worldwide.
          Institutions get AI-powered admissions operations that actually work.
        </p>
        <p className="text-base text-muted-foreground/70 max-w-xl mx-auto mb-12">
          No more fragmented systems. No more duplicate paperwork. One connected workflow for everyone.
        </p>
      </ScrollReveal>

      <ScrollReveal delay={600}>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-gold-500 hover:bg-gold-600 text-white" asChild>
            <Link to="/signup">
              Get Started Free
              <ArrowRight size={20} className="ml-2" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
            <a href="#students">See How It Works</a>
          </Button>
        </div>
      </ScrollReveal>

      <ScrollReveal delay={800}>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 mt-12 text-sm text-muted-foreground/60">
          <span>Free for students, always</span>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
          <span>No credit card required</span>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
          <span>FERPA &amp; GDPR ready</span>
        </div>
      </ScrollReveal>
    </div>

    <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce-gentle">
      <a href="#problem" className="flex flex-col items-center gap-2 text-muted-foreground/60 hover:text-muted-foreground transition-colors">
        <span className="text-xs font-medium tracking-widest uppercase">Scroll to explore</span>
        <ChevronDown size={20} />
      </a>
    </div>
  </section>
);

export default HeroSection;
