const steps = [
  {
    number: 1,
    title: "Upload CSV Data",
    description:
      "Export your web analytics and CRM data as CSV files and upload both in one step.",
  },
  {
    number: 2,
    title: "AI Analysis",
    description:
      "GPT-4o reads your sales reps’ notes and translates qualitative sentiment into quantitative signals.",
  },
  {
    number: 3,
    title: "Budget Decisions",
    description:
      "Receive structured increase/pause/decrease recommendations for each campaign, with reasoning.",
  },
];

export default function HowItWorksSection() {
  return (
    <section className="bg-brand-surface py-16 px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-semibold text-brand-text leading-snug text-center mb-12">
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((step) => (
            <div key={step.number}>
              <div className="w-10 h-10 rounded-full bg-brand-accent text-white font-semibold text-lg flex items-center justify-center mb-4 mx-auto">
                {step.number}
              </div>
              <h3 className="text-xl font-semibold text-brand-text leading-snug text-center mb-3">
                {step.title}
              </h3>
              <p className="text-base text-brand-muted leading-relaxed text-center">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
