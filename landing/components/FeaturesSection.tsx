import {
  BoltIcon,
  ArrowsRightLeftIcon,
  CogIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";
import type { FC, SVGProps } from "react";

const features: {
  Icon: FC<SVGProps<SVGSVGElement>>;
  title: string;
  description: string;
}[] = [
  {
    Icon: BoltIcon,
    title: "Semantic Attribution",
    description:
      "Goes beyond click data. Understands why a lead converted by reading what the sales rep said.",
  },
  {
    Icon: ArrowsRightLeftIcon,
    title: "CRM Webhook Sync",
    description:
      "Ingest sessions directly from your CRM via webhook — no CSV export required in production.",
  },
  {
    Icon: CogIcon,
    title: "n8n Automation",
    description:
      "Trigger budget analysis on a schedule or CRM event using n8n workflow automation.",
  },
  {
    Icon: ChartBarIcon,
    title: "Budget Routing",
    description:
      "Structured JSON output means budget decisions flow directly into your ad platform APIs.",
  },
];

export default function FeaturesSection() {
  return (
    <section className="bg-brand-surface py-16 px-6">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-semibold text-brand-text leading-snug text-center mb-12">
          Why Performance Plus
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="bg-brand-bg border border-brand-border rounded-xl p-6"
            >
              <feature.Icon className="w-6 h-6 text-brand-accent mb-4" />
              <h3 className="text-xl font-semibold text-brand-text leading-snug mb-3">
                {feature.title}
              </h3>
              <p className="text-base text-brand-muted leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
