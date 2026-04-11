import { Link } from "react-router-dom";
import { Button } from "@/components/shadcn/button";
import { ArrowRight } from "lucide-react";
import ScrollReveal from "./ScrollReveal";

const HeroSection = () => (
  <section className="relative min-h-screen flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 overflow-hidden bg-offwhite">
    <div className="absolute inset-0 -z-10">
      <div className="absolute top-20 left-[10%] w-72 h-72 bg-student-mist rounded-full blur-3xl animate-float" />
      <div className="absolute bottom-20 right-[10%] w-96 h-96 bg-student-mist rounded-full blur-3xl animate-float-slow" />
      <div className="absolute top-1/3 right-[20%] w-48 h-48 bg-gold-pale/40 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
    </div>

    <div className="max-w-5xl mx-auto text-center">
      <ScrollReveal variant="blur-in">
        <div className="inline-flex items-center gap-2 bg-student-mist text-student rounded-full px-5 py-2 text-sm font-medium mb-8">
          Everything a $6K agent does &mdash; for free
        </div>
      </ScrollReveal>

      <ScrollReveal delay={200} variant="scale-up">
        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-charcoal leading-[1.1] mb-6 tracking-tight font-heading">
          Your private{" "}
          <br className="hidden sm:block" />
          <span className="text-student">college advisor</span>
        </h1>
      </ScrollReveal>

      <ScrollReveal delay={400}>
        <p className="text-xl sm:text-2xl text-gray-500 max-w-3xl mx-auto mb-12 leading-relaxed">
          Find the right programs, manage every application, and know your real chances &mdash; all in one place. Like having a great counselor who actually knows your profile.
        </p>
      </ScrollReveal>

      <ScrollReveal delay={600}>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="text-base px-10 py-7 rounded-xl shadow-lg text-lg bg-student hover:bg-student-hover text-white" asChild>
            <Link to="/signup?role=student">
              Create Your Profile
              <ArrowRight size={20} className="ml-2" />
            </Link>
          </Button>
          <Button size="lg" variant="outline" className="text-base px-10 py-7 rounded-xl text-lg border-gray-300 text-charcoal hover:bg-student-mist" asChild>
            <Link to="/signup?role=institution_admin">Schedule a Demo</Link>
          </Button>
        </div>
      </ScrollReveal>

      <ScrollReveal delay={800}>
        <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 mt-12 text-sm text-gray-400">
          <span>10,000+ programs</span>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-gray-300" />
          <span>50+ countries</span>
          <span className="hidden sm:block w-1 h-1 rounded-full bg-gray-300" />
          <span>$0 for students</span>
        </div>
      </ScrollReveal>
    </div>
  </section>
);

export default HeroSection;
