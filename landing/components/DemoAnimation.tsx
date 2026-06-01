"use client";

import { useEffect, useRef, useState } from "react";
import { BADGE_COLORS, PCT_COLOR } from "@/components/badge-tokens";

type Action = "increase" | "pause" | "decrease";

const demoCards: {
  id: string;
  label: string;
  action: Action;
  pct: string;
  reasoning: string;
  delay: string;
}[] = [
  {
    id: "cmp_b2b_search",
    label: "B2B Search",
    action: "increase",
    pct: "+22%",
    reasoning: 'High-intent sales notes: "ready to sign", "budget approved"',
    delay: "0s",
  },
  {
    id: "cmp_retargeting",
    label: "Retargeting",
    action: "increase",
    pct: "+15%",
    reasoning: "Warm leads re-engaging, CRM notes show strong purchase intent",
    delay: "0.2s",
  },
  {
    id: "cmp_competitor_conquest",
    label: "Competitor Conquest",
    action: "decrease",
    pct: "-30%",
    reasoning: "Low conversion quality, sales notes cite poor fit",
    delay: "0.4s",
  },
  {
    id: "cmp_linkedin_outbound",
    label: "LinkedIn Outbound",
    action: "pause",
    pct: "0%",
    reasoning: "Insufficient qualified data to justify spend",
    delay: "0.6s",
  },
];

function pctColor(pct: string): string {
  if (pct.startsWith("+")) return PCT_COLOR.positive;
  if (pct.startsWith("-")) return PCT_COLOR.negative;
  return PCT_COLOR.zero;
}

export default function DemoAnimation() {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    const node = sectionRef.current;
    if (!node) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setAnimate(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <section className="bg-brand-bg py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-semibold text-brand-text leading-snug text-center mb-2">
          See It In Action
        </h2>
        <p className="text-base text-brand-muted text-center mb-8">
          Generating budget decisions...
        </p>
        <div
          ref={sectionRef}
          className="rounded-xl border border-brand-border bg-brand-surface p-8"
        >
          {demoCards.map((card) => {
            const badge = BADGE_COLORS[card.action];
            return (
              <div
                key={card.id}
                style={{
                  animation: animate
                    ? `fadeSlideIn 0.5s ease-out ${card.delay} both`
                    : "none",
                  opacity: animate ? undefined : 0,
                }}
                className="bg-brand-bg border border-brand-border rounded-xl p-6 mb-4 last:mb-0"
              >
                <div className="flex items-center justify-between">
                  <span className="text-base font-semibold text-brand-text">
                    {card.label}
                  </span>
                  <span
                    style={{
                      background: badge.bg,
                      color: badge.text,
                      display: "inline-block",
                      padding: "4px 8px",
                      borderRadius: "12px",
                      fontSize: "12px",
                      fontWeight: 600,
                      letterSpacing: "0.5px",
                    }}
                  >
                    {badge.label}
                  </span>
                </div>
                <p className="font-mono text-base text-brand-muted mt-1">
                  {card.id}
                </p>
                <div className="border-t border-brand-border my-4" />
                <p className="text-base text-brand-text">{card.reasoning}</p>
                <p className="mt-3 text-base">
                  Budget change:{" "}
                  <span
                    style={{ color: pctColor(card.pct), fontWeight: 600 }}
                  >
                    {card.pct}
                  </span>
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
