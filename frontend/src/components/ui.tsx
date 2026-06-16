import Link from "next/link";
import type { ReactNode } from "react";

export function Section({
  children,
  className = "",
  muted = false,
}: {
  children: ReactNode;
  className?: string;
  muted?: boolean;
}) {
  return (
    <section className={`${muted ? "bg-surface" : ""} py-20 ${className}`}>
      <div className="container-x">{children}</div>
    </section>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <span className="eyebrow">{children}</span>;
}

export function SectionHeading({
  title,
  subhead,
  center = false,
}: {
  title: string;
  subhead?: string;
  center?: boolean;
}) {
  return (
    <div className={`max-w-2xl ${center ? "mx-auto text-center" : ""}`}>
      <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">{title}</h2>
      {subhead && <p className="mt-4 text-lg text-muted">{subhead}</p>}
    </div>
  );
}

export function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-ink">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
    </div>
  );
}

export function CtaBand({
  heading,
  subhead,
  cta,
}: {
  heading: string;
  subhead?: string;
  cta: { label: string; href: string };
}) {
  return (
    <section className="py-20">
      <div className="container-x">
        <div className="rounded-3xl bg-brand px-8 py-14 text-center text-white">
          <h2 className="mx-auto max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">
            {heading}
          </h2>
          {subhead && <p className="mx-auto mt-3 max-w-xl text-brand-soft">{subhead}</p>}
          <Link
            href={cta.href}
            className="mt-8 inline-flex items-center justify-center rounded-lg bg-white px-6 py-3 text-sm font-semibold text-brand transition-colors hover:bg-brand-soft"
          >
            {cta.label}
          </Link>
        </div>
      </div>
    </section>
  );
}
