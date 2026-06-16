import type { Metadata } from "next";
import Link from "next/link";
import { pricing } from "@/lib/sentio";
import { Section, SectionHeading } from "@/components/ui";

export const metadata: Metadata = {
  title: "Pricing — Sentio",
  description: "Simple, transparent plans for CS teams of every size.",
};

export default function PricingPage() {
  return (
    <>
      <section className="bg-gradient-to-b from-brand-soft/60 to-white py-20">
        <div className="container-x text-center">
          <h1 className="text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            {pricing.hero.headline}
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-muted">{pricing.hero.subhead}</p>
        </div>
      </section>

      <Section>
        <div className="grid items-start gap-6 lg:grid-cols-3">
          {pricing.plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl border bg-white p-7 ${
                plan.popular ? "border-brand shadow-lg" : "border-line"
              }`}
            >
              {plan.popular && (
                <span className="absolute -top-3 left-7 rounded-full bg-brand px-3 py-1 text-xs font-semibold text-white">
                  Most popular
                </span>
              )}
              <h3 className="text-lg font-bold text-ink">{plan.name}</h3>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-bold text-ink">{plan.price}</span>
                <span className="text-sm text-faint">· {plan.annual}</span>
              </div>
              <p className="mt-3 text-sm text-muted">{plan.blurb}</p>
              <dl className="mt-6 space-y-3 text-sm">
                <div>
                  <dt className="font-medium text-faint">Seats</dt>
                  <dd className="text-ink">{plan.seats}</dd>
                </div>
                <div>
                  <dt className="font-medium text-faint">Integrations</dt>
                  <dd className="text-ink">{plan.integrations}</dd>
                </div>
                <div>
                  <dt className="font-medium text-faint">Support</dt>
                  <dd className="text-ink">{plan.support}</dd>
                </div>
              </dl>
              <Link
                href="/demo"
                className={`mt-7 ${plan.popular ? "btn-primary" : "btn-ghost"} w-full`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
        <p className="mt-8 text-center text-sm text-muted">{pricing.belowPlans}</p>
      </Section>

      <Section muted>
        <SectionHeading title="Pricing FAQ" />
        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {pricing.faq.map((item) => (
            <div key={item.q} className="card">
              <h3 className="text-base font-semibold text-ink">{item.q}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{item.a}</p>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}
