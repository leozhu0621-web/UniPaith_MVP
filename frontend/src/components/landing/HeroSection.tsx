import { Link } from "react-router-dom";
import { Button } from "@/components/shadcn/button";
import { ArrowRight } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const HeroSection = () => (
  <section className="relative min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 overflow-hidden">
    <div className="absolute inset-0 -z-10">
      <div className="absolute top-20 left-[10%] w-72 h-72 bg-brand-slate-100/60 rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-brand-slate-300/30 rounded-full blur-3xl animate-float-slow" />
      <div className="absolute top-1/3 right-[20%] w-48 h-48 bg-brand-amber-300/20 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
    </div>

    <div className="max-w-5xl mx-auto text-center">
      <ScrollReveal variant="blur-in">
        <div className="inline-flex items-center gap-2 bg-brand-slate-100 text-brand-slate-700 rounded-full px-5 py-2 text-sm font-medium mb-8">
          AI-powered admissions for students &amp; institutions
        </div>
      </ScrollReveal>

      <ScrollReveal delay={200} variant="scale-up">
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-foreground leading-[1.1] mb-6 tracking-tight font-heading">
          Everyone&rsquo;s private{" "}
          <br className="hidden sm:block" />
          <span className="text-primary">education advisor</span>
        </h1>
      </ScrollReveal>

      <ScrollReveal delay={400}>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-x-8 gap-y-3 text-lg sm:text-xl text-muted-foreground max-w-3xl mx-auto mb-12">
          <p>
            <span className="font-semibold text-foreground">Students:</span>{" "}
            AI guidance from profile to acceptance.
          </p>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/40" />
          <p>
            <span className="font-semibold text-foreground">Institutions:</span>{" "}
            The admissions ops system your team deserves.
          </p>
        </div>
      </ScrollReveal>

      <ScrollReveal delay={600}>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-brand-amber-500 hover:bg-brand-amber-600 text-white" asChild>
            <Link to="/signup?role=student">
              Create Your Profile
              <ArrowRight size={20} className="ml-2" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg" asChild>
            <Link to="/signup?role=institution_admin">Schedule a Demo</Link>
          </Button>
        </div>
      </ScrollReveal>

      <ScrollReveal delay={800}>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 mt-12 text-sm text-muted-foreground/60">
          <span>Free for students, always</span>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
          <span>FERPA &amp; GDPR ready</span>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-muted-foreground/30" />
          <span>10,000+ programs indexed</span>
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default HeroSection;
