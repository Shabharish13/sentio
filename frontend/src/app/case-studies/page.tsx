import type { Metadata } from "next";
import { caseStudies } from "@/lib/sentio";
import { Section, CtaBand } from "@/components/ui";

export const metadata: Metadata = {
  title: "Case Studies — Sentio",
  description: "How CS teams use Sentio to catch churn early and standardize playbooks.",
};

export default function CaseStudiesPage() {
  return (
    <>
      <section className="bg-gradient-to-b from-brand-soft/60 to-white py-20">
        <div className="container-x">
          <h1 className="text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            {caseStudies.hero.headline}
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted">{caseStudies.hero.subhead}</p>
          <p className="mt-3 text-sm text-faint">{caseStudies.hero.note}</p>
        </div>
      </section>

      <Section>
        <div className="grid gap-8 md:grid-cols-2">
          {caseStudies.stories.map((s) => (
            <article key={s.headline} className="card flex flex-col">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-brand">{s.metric}</span>
                <span className="text-sm text-faint">{s.metricLabel}</span>
              </div>
              <h2 className="mt-4 text-xl font-semibold text-ink">{s.headline}</h2>
              <p className="mt-3 flex-1 text-sm leading-relaxed text-muted">{s.body}</p>
              <p className="mt-4 text-sm font-medium text-ink">{s.attribution}</p>
              <span className="mt-3 inline-block w-fit rounded-full bg-surface-2 px-3 py-1 text-xs text-faint">
                {s.tag}
              </span>
            </article>
          ))}
        </div>
      </Section>

      <CtaBand {...caseStudies.ctaBand} />
    </>
  );
}
