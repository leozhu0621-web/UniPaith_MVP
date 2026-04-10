import { Link } from "react-router-dom";
import { Button } from "@/components/shadcn/button";
import { ArrowRight, GraduationCap, Building2 } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const DualCTASection = () => (
  <section id="cta" className="py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden bg-gradient-to-br from-brand-slate-600 to-brand-slate-800">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center text-background mb-4 font-heading">
          The admissions system the industry has been waiting for
        </h2>
        <p className="text-center text-background/70 mb-14 text-lg max-w-xl mx-auto">
          Whether you're a student ready to take control of your future, or an institution ready to modernize — UniPaith is being built for you.
        </p>
      </ScrollReveal>

      <div className="grid md:grid-cols-2 gap-8">
        <ScrollReveal delay={100} variant="fade-left">
          <div className="bg-card rounded-2xl border p-8 sm:p-10 text-center shadow-sm hover-lift transition-all h-full group">
            <div className="w-16 h-16 rounded-2xl bg-brand-amber-100 flex items-center justify-center mx-auto mb-6">
              <GraduationCap className="text-brand-amber-600 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3" size={32} />
            </div>
            <h3 className="text-2xl font-bold text-foreground mb-3 font-heading">Start your journey</h3>
            <p className="text-muted-foreground mb-8">Join thousands of students already building their Universal Profile. Free forever — no credit card, no catches.</p>
            <Button size="lg" className="w-full sm:w-auto px-10 py-7 rounded-xl text-base bg-brand-amber-500 hover:bg-brand-amber-600 text-white text-lg" asChild>
              <Link to="/signup?role=student">
                Create Your Profile
                <ArrowRight size={20} className="ml-2" />
              </Link>
            </Button>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={300} variant="fade-right">
          <div className="bg-card rounded-2xl border p-8 sm:p-10 text-center shadow-sm hover-lift transition-all h-full group">
            <div className="w-16 h-16 rounded-2xl bg-brand-slate-600/10 flex items-center justify-center mx-auto mb-6">
              <Building2 className="text-brand-slate-600 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3" size={32} />
            </div>
            <h3 className="text-2xl font-bold text-foreground mb-3 font-heading">Transform your admissions</h3>
            <p className="text-muted-foreground mb-8">See how UniPaith can cut review time, improve candidate quality, and give your team AI-powered workflow support.</p>
            <Button size="lg" variant="outline" className="w-full sm:w-auto px-10 py-7 rounded-xl text-base border-brand-slate-600 text-brand-slate-600 hover:bg-brand-slate-600 hover:text-brand-slate-600-foreground text-lg" asChild>
              <Link to="/signup?role=institution_admin">
                Schedule a Demo
                <ArrowRight size={20} className="ml-2" />
              </Link>
            </Button>
          </div>
        </ScrollReveal>
      </div>
    </div>
  </section>
);

export default DualCTASection;
