import { Link } from "react-router-dom";
import { Button } from "@/components/shadcn/button";
import { ArrowRight, GraduationCap, Building2 } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const DualCTASection = () => (
  <section id="cta" className="py-24 px-4 sm:px-6 lg:px-8 relative overflow-hidden bg-charcoal">
    <div className="max-w-5xl mx-auto">
      <ScrollReveal variant="blur-in">
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center text-white mb-4 font-heading">
          Ready to get started?
        </h2>
        <p className="text-center text-gray-400 mb-14 text-lg max-w-xl mx-auto">
          Whether you&rsquo;re a student looking for the right school, or an institution ready to modernize &mdash; UniPaith is built for you.
        </p>
      </ScrollReveal>

      <div className="grid md:grid-cols-2 gap-8">
        <ScrollReveal delay={100} variant="fade-left">
          <div className="bg-white rounded-2xl p-8 sm:p-10 text-center shadow-sm hover-lift transition-all h-full group">
            <div className="w-16 h-16 rounded-2xl bg-student-mist flex items-center justify-center mx-auto mb-6">
              <GraduationCap className="text-student transition-transform duration-300 group-hover:scale-110" size={32} />
            </div>
            <h3 className="text-2xl font-bold text-charcoal mb-3 font-heading">Start your journey</h3>
            <p className="text-gray-500 mb-8">Create your profile and start matching with programs. No cost, no commitment.</p>
            <Button size="lg" className="w-full sm:w-auto px-10 py-7 rounded-xl text-base bg-student hover:bg-student-hover text-white text-lg" asChild>
              <Link to="/signup?role=student">
                Create Your Profile
                <ArrowRight size={20} className="ml-2" />
              </Link>
            </Button>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={300} variant="fade-right">
          <div className="bg-white rounded-2xl p-8 sm:p-10 text-center shadow-sm hover-lift transition-all h-full group">
            <div className="w-16 h-16 rounded-2xl bg-charcoal/10 flex items-center justify-center mx-auto mb-6">
              <Building2 className="text-charcoal transition-transform duration-300 group-hover:scale-110" size={32} />
            </div>
            <h3 className="text-2xl font-bold text-charcoal mb-3 font-heading">Transform your admissions</h3>
            <p className="text-gray-500 mb-8">See how UniPaith can cut review time, improve candidate quality, and give your team AI-powered support.</p>
            <Button size="lg" variant="outline" className="w-full sm:w-auto px-10 py-7 rounded-xl text-base border-school text-school hover:bg-school hover:text-white text-lg" asChild>
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
