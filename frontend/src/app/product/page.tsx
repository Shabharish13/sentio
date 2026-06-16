import type { Metadata } from "next";
import { home, product } from "@/lib/sentio";
import { Section, SectionHeading, FeatureCard, CtaBand } from "@/components/ui";

export const metadata: Metadata = { title: "Product — Sentio" };

export default function ProductPage() {
  return (
    <>
      <section className="bg-gradient-to-b from-brand-soft/60 to-white py-20">
        <div className="container-x">
          <h1 className="max-w-3xl text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            {product.hero.headline}
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted">{product.hero.subhead}</p>
        </div>
      </section>

      {/* How it works */}
      <Section>
        <SectionHeading title="How it works" />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {product.howItWorks.map((s) => (
            <div key={s.step} className="card">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
                {s.step}
              </span>
              <h3 className="mt-4 text-lg font-semibold text-ink">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* Capabilities (same four feature cards as Home) */}
      <Section muted>
        <SectionHeading title={home.features.heading} />
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {home.features.cards.map((c) => (
            <FeatureCard key={c.title} title={c.title} body={c.body} />
          ))}
        </div>
      </Section>

      {/* What teams use Sentio for (same three problem cards) */}
      <Section>
        <SectionHeading title="What teams use Sentio for" />
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {home.problems.cards.map((c) => (
            <FeatureCard key={c.title} title={c.title} body={c.body} />
          ))}
        </div>
      </Section>

      {/* Integrations by category */}
      <Section muted>
        <SectionHeading title={product.integrationsHeading} subhead={product.integrationsSubhead} />
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {product.integrationCategories.map((cat) => (
            <div key={cat.category} className="card">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-brand">
                {cat.category}
              </h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {cat.tools.map((t) => (
                  <span
                    key={t}
                    className="rounded-full border border-line bg-surface px-3 py-1 text-sm text-muted"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>

      <CtaBand {...product.ctaBand} />
    </>
  );
}
