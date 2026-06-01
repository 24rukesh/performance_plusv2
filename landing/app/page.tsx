import HeroSection from "@/components/HeroSection";
import HowItWorksSection from "@/components/HowItWorksSection";

export default function Home() {
  return (
    <main className="min-h-screen">
      <HeroSection />
      <HowItWorksSection />
      {/* Plan 04 appends: <DemoAnimation />, <FeaturesSection />, <Footer /> */}
    </main>
  );
}
