"use client";

import { useState } from "react";
import { demoPage, SIZE_TO_BAND } from "@/lib/sentio";
import { postDemo, type DemoRequest, type LeadBrief } from "@/lib/api";

const EMPTY: DemoRequest = {
  first_name: "",
  last_name: "",
  work_email: "",
  company_name: "",
  job_title: "",
  company_size: "",
  problem_stated: "",
  how_heard: "",
};

type Status = "idle" | "loading" | "done" | "error";

export default function DemoPage() {
  const [form, setForm] = useState<DemoRequest>(EMPTY);
  const [status, setStatus] = useState<Status>("idle");
  const [brief, setBrief] = useState<LeadBrief | null>(null);

  function set<K extends keyof DemoRequest>(key: K, value: DemoRequest[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    try {
      const payload = {
        ...form,
        company_size: SIZE_TO_BAND[form.company_size] ?? form.company_size,
      };
      const result = await postDemo(payload);
      setBrief(result);
      setStatus("done");
    } catch {
      setStatus("error");
    }
  }

  function reset() {
    setForm(EMPTY);
    setBrief(null);
    setStatus("idle");
  }

  return (
    <section className="py-16">
      <div className="container-x grid gap-12 lg:grid-cols-2">
        {/* Pitch column */}
        <div className="lg:pr-8">
          <h1 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            {demoPage.pitch.headline}
          </h1>
          <p className="mt-4 text-lg text-muted">{demoPage.pitch.subhead}</p>
          <ul className="mt-8 space-y-3">
            {demoPage.pitch.bullets.map((b) => (
              <li key={b} className="flex gap-3 text-sm text-ink">
                <span className="mt-1 text-brand">●</span>
                {b}
              </li>
            ))}
          </ul>
        </div>

        {/* Right column: form / brief / error */}
        <div>
          {status === "done" && brief ? (
            <LeadBriefView brief={brief} onReset={reset} />
          ) : (
            <DemoForm
              form={form}
              set={set}
              onSubmit={onSubmit}
              loading={status === "loading"}
              error={status === "error"}
            />
          )}
        </div>
      </div>
    </section>
  );
}

function DemoForm({
  form,
  set,
  onSubmit,
  loading,
  error,
}: {
  form: DemoRequest;
  set: <K extends keyof DemoRequest>(key: K, value: DemoRequest[K]) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
  error: boolean;
}) {
  const field = "w-full rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand";
  return (
    <form onSubmit={onSubmit} className="rounded-2xl border border-line bg-white p-7">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="text-sm font-medium text-ink">First name</label>
          <input className={field} required value={form.first_name}
            onChange={(e) => set("first_name", e.target.value)} />
        </div>
        <div>
          <label className="text-sm font-medium text-ink">Last name</label>
          <input className={field} required value={form.last_name}
            onChange={(e) => set("last_name", e.target.value)} />
        </div>
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-ink">Work email *</label>
        <input className={field} type="email" required placeholder="you@company.com"
          value={form.work_email} onChange={(e) => set("work_email", e.target.value)} />
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-ink">Company name *</label>
        <input className={field} required value={form.company_name}
          onChange={(e) => set("company_name", e.target.value)} />
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-ink">Job title *</label>
        <input className={field} required placeholder="e.g. VP of Customer Success"
          value={form.job_title} onChange={(e) => set("job_title", e.target.value)} />
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-ink">Company size *</label>
        <select className={field} required value={form.company_size}
          onChange={(e) => set("company_size", e.target.value)}>
          <option value="" disabled>Select…</option>
          {demoPage.companySizes.map((s) => (
            <option key={s} value={s}>{s} employees</option>
          ))}
        </select>
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-ink">What are you trying to solve?</label>
        <textarea className={field} rows={2} placeholder="Optional — helps us tailor the walkthrough"
          value={form.problem_stated} onChange={(e) => set("problem_stated", e.target.value)} />
      </div>

      <div className="mt-4">
        <label className="text-sm font-medium text-ink">How did you hear about us?</label>
        <select className={field} value={form.how_heard}
          onChange={(e) => set("how_heard", e.target.value)}>
          <option value="">Select…</option>
          {demoPage.howHeard.map((h) => (
            <option key={h} value={h}>{h}</option>
          ))}
        </select>
      </div>

      <button type="submit" disabled={loading} className="btn-primary mt-6 w-full disabled:opacity-60">
        {loading ? demoPage.submitting : demoPage.submit}
      </button>
      <p className="mt-3 text-xs text-faint">{demoPage.submitCaption}</p>
      {error && <p className="mt-3 text-sm font-medium text-risk">{demoPage.errorFallback}</p>}
    </form>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-line bg-surface px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wide text-faint">{label}</p>
      <p className="mt-1 text-lg font-bold text-ink">{value}</p>
    </div>
  );
}

function Panel({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <div className="card">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-brand">{title}</h3>
      <dl className="mt-3 space-y-2 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-4">
            <dt className="text-faint">{k}</dt>
            <dd className="text-right font-medium text-ink">{v || "—"}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function LeadBriefView({ brief, onReset }: { brief: LeadBrief; onReset: () => void }) {
  const qualified = brief.route === "qualified";
  return (
    <div className="rounded-2xl border border-line bg-white p-7">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-ink">Lead Brief</h2>
        <button onClick={onReset} className="text-sm font-medium text-brand hover:underline">
          New request
        </button>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Fit grade" value={brief.fit_grade} />
        <Stat label="Fit score" value={brief.fit_score} />
        <Stat label="Intent score" value={brief.intent_score} />
        <Stat label="Routing" value={brief.route} />
      </div>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <Panel
          title="Contact"
          rows={[
            ["Name", brief.contact_name],
            ["Title", brief.contact_title],
            ["Email", brief.contact_email],
            ["Stakeholder", brief.stakeholder],
          ]}
        />
        <Panel
          title="Company"
          rows={[
            ["Name", brief.company_name],
            ["Headcount", brief.headcount != null ? String(brief.headcount) : ""],
            ["Industry", brief.industry ?? ""],
            ["Revenue", brief.revenue ?? ""],
            ["Enrichment", brief.enriched ? "Apollo" : "form only"],
          ]}
        />
      </div>

      {/* Research signal */}
      <div className="mt-5 card">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand">Research signal</h3>
        {brief.top_signal ? (
          <>
            <p className="mt-2 text-sm text-ink">{brief.top_signal}</p>
            <p className="mt-1 text-xs text-faint">
              {brief.signal_type}
              {brief.source_url ? (
                <>
                  {" · "}
                  <a href={brief.source_url} target="_blank" rel="noreferrer" className="text-brand hover:underline">
                    source
                  </a>
                </>
              ) : null}
            </p>
          </>
        ) : (
          <p className="mt-2 text-sm text-muted">
            No specific trigger found — email opens with company stage + vertical framing.
          </p>
        )}
      </div>

      {/* Draft email (qualified) or disqualification reason */}
      {qualified ? (
        brief.email_draft && (
          <div className="mt-5 card">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-brand">
              Draft email — for SDR review
            </h3>
            <p className="mt-1 text-xs text-faint">
              Sentio generates this draft — it does not send email automatically. Review and send from your inbox.
            </p>
            <pre className="mt-3 whitespace-pre-wrap rounded-lg bg-surface p-4 text-sm text-ink">
              {brief.email_draft}
            </pre>
          </div>
        )
      ) : (
        <div className="mt-5 rounded-2xl border border-risk/30 bg-risk/5 p-6">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-risk">
            Disqualified — reason
          </h3>
          <p className="mt-2 text-sm text-ink">{brief.disqualification_reason}</p>
        </div>
      )}

      <p className="mt-5 text-xs text-faint">
        Synced to HubSpot · ref {brief.crm_ref}
      </p>
    </div>
  );
}
