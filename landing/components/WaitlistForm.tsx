"use client";

import { useState, FormEvent } from "react";

type Status = "idle" | "submitting" | "success" | "duplicate" | "error";

export function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("submitting");
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
      const res = await fetch(`${base}/api/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (res.ok) {
        setStatus("success");
      } else if (res.status === 409) {
        setStatus("duplicate");
      } else {
        setStatus("error");
      }
    } catch {
      setStatus("error");
    }
  }

  if (status === "success") {
    return (
      <p className="mt-4 text-sm text-center text-green-400">
        You&apos;re on the waitlist! We&apos;ll be in touch.
      </p>
    );
  }

  return (
    <div id="waitlist" className="max-w-md mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-row gap-4">
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter your work email"
          disabled={status === "submitting"}
          className="flex-1 h-12 px-4 bg-brand-surface border border-brand-border rounded-lg text-brand-text placeholder-brand-muted focus:outline-none focus:ring-2 focus:ring-brand-accent"
        />
        <button
          type="submit"
          disabled={status === "submitting"}
          className="h-12 px-6 bg-brand-accent text-white font-semibold rounded-lg min-w-[120px] disabled:opacity-75 disabled:cursor-not-allowed"
        >
          {status === "submitting" ? "Joining..." : "Join Waitlist"}
        </button>
      </form>
      {status === "duplicate" && (
        <p className="mt-4 text-sm text-center text-brand-muted">
          You&apos;re already on the waitlist.
        </p>
      )}
      {status === "error" && (
        <p className="mt-4 text-sm text-center text-red-400">
          Something went wrong — please try again.
        </p>
      )}
    </div>
  );
}
