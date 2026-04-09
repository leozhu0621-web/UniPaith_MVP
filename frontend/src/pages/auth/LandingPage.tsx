import Navbar from "@/components/landing/Navbar";
import HeroSection from "@/components/landing/HeroSection";
import ProblemSection from "@/components/landing/ProblemSection";
import StudentsSection from "@/components/landing/StudentsSection";
import InstitutionsSection from "@/components/landing/InstitutionsSection";
import AIFeaturesSection from "@/components/landing/AIFeaturesSection";
import FlywheelSection from "@/components/landing/FlywheelSection";
import SocialProofSection from "@/components/landing/SocialProofSection";
import DualCTASection from "@/components/landing/DualCTASection";
import FAQSection from "@/components/landing/FAQSection";
import Footer from "@/components/landing/Footer";
import NarrativeBreak from "@/components/landing/NarrativeBreak";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <HeroSection />
      <ProblemSection />
      <NarrativeBreak text="What if one platform could fix both sides at once?" />
      <StudentsSection />
      <NarrativeBreak text="And it's not just students who benefit." />
      <InstitutionsSection />
      <NarrativeBreak text="Here's the intelligence behind it all." />
      <AIFeaturesSection />
      <FlywheelSection />
      <SocialProofSection />
      <FAQSection />
      <DualCTASection />
      <Footer />
    </div>
  );
}
