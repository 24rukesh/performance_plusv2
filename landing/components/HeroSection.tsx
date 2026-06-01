import { WaitlistForm } from "@/components/WaitlistForm";

export default function HeroSection() {
  return (
    <section className="bg-brand-bg py-24 px-6">
      <div className="max-w-3xl mx-auto text-center">
        <h1 className="text-4xl sm:text-5xl font-semibold text-brand-text leading-tight">
          Performance Plus
        </h1>
        <p className="mt-6 text-base text-brand-muted max-w-xl mx-auto leading-relaxed">
          Stop guessing. Let your sales reps&apos; notes route your ad budget.
        </p>
        <p className="mt-4 text-base text-brand-muted max-w-xl mx-auto leading-relaxed">
          Upload your web analytics and CRM exports. Get AI-reasoned budget
          decisions in seconds — grounded in what sales reps actually said about
          each lead.
        </p>
        <div className="mt-8 flex flex-row gap-4 justify-center">
          <a
            href="#waitlist"
            className="bg-brand-accent text-white font-semibold px-6 py-3 rounded-lg min-h-[44px] inline-flex items-center justify-center"
          >
            Join Waitlist
          </a>
          <a
            href="/app"
            target="_blank"
            rel="noopener noreferrer"
            className="border border-brand-accent text-brand-accent bg-transparent font-semibold px-6 py-3 rounded-lg min-h-[44px] inline-flex items-center justify-center"
          >
            Try Demo
          </a>
        </div>
        <div className="mt-12">
          <WaitlistForm />
        </div>
      </div>
    </section>
  );
}
