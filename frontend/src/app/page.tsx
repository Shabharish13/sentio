import Link from "next/link";
import { home } from "@/lib/sentio";
import { Section, SectionHeading, Eyebrow, FeatureCard, CtaBand } from "@/components/ui";

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="bg-gradient-to-b from-brand-soft/60 to-white py-24">
        <div className="container-x text-center">
          <Eyebrow>{home.hero.eyebrow}</Eyebrow>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-bold tracking-tight text-ink sm:text-6xl">
            {home.hero.headline}
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted">{home.hero.subhead}</p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link href={home.hero.primary.href} className="btn-primary">
              {home.hero.primary.label}
            </Link>
            <Link href={home.hero.secondary.href} className="btn-ghost">
              {home.hero.secondary.label}
            </Link>
          </div>
        </div>
      </section>

      {/* Problems */}
      <Section>
        <SectionHeading title={home.problems.heading} subhead={home.problems.subhead} />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {home.problems.cards.map((c) => (
            <FeatureCard key={c.title} title={c.title} body={c.body} />
          ))}
        </div>
      </Section>

      {/* Features */}
      <Section muted>
        <SectionHeading title={home.features.heading} />
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {home.features.cards.map((c) => (
            <FeatureCard key={c.title} title={c.title} body={c.body} />
          ))}
        </div>
      </Section>

      {/* Social proof */}
      <Section>
        <SectionHeading title={home.socialProof.heading} center />
        <div className="mx-auto mt-12 grid max-w-4xl gap-6 md:grid-cols-2">
          {home.socialProof.stats.map((s) => (
            <div key={s.headline} className="card">
              <p className="text-4xl font-bold text-brand">{s.metric}</p>
              <p className="text-sm font-medium text-faint">{s.label}</p>
              <p className="mt-4 text-base font-semibold text-ink">{s.headline}</p>
              <p className="mt-2 text-sm text-muted">{s.attribution}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* Integrations */}
      <Section muted>
        <SectionHeading title={home.integrations.heading} subhead={home.integrations.subhead} center />
        <div className="mx-auto mt-10 flex max-w-4xl flex-wrap justify-center gap-3">
          {home.integrations.tools.map((t) => (
            <span
              key={t}
              className="rounded-full border border-line bg-white px-4 py-2 text-sm font-medium text-muted"
            >
              {t}
            </span>
          ))}
        </div>
      </Section>

      <CtaBand {...home.ctaBand} />
    </>
  );
}
