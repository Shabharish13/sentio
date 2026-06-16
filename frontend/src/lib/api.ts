// Thin client for the Sentio FastAPI backend. Base URL is configurable so the
// same build works against localhost and a deployed backend.

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export interface DemoRequest {
  first_name: string;
  last_name: string;
  work_email: string;
  company_name: string;
  job_title: string;
  company_size: string;
  problem_stated: string;
  how_heard: string;
}

export interface LeadBrief {
  route: string;
  fit_grade: string;
  fit_score: number;
  intent_score: number;
  stakeholder: string;
  signal_type: string;
  top_signal: string | null;
  source_url: string | null;
  email_draft: string | null;
  disqualification_reason: string | null;
  contact_name: string;
  contact_title: string;
  contact_email: string;
  company_name: string;
  headcount: number | null;
  industry: string | null;
  revenue: string | null;
  enriched: boolean;
  crm_stage: string;
  crm_ref: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  outcome: string;
  escalated: boolean;
  booked: boolean;
  sources: string[];
}

export async function postDemo(payload: DemoRequest): Promise<LeadBrief> {
  const res = await fetch(`${API_BASE}/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`demo request failed: ${res.status}`);
  }
  return res.json();
}

export async function postChat(
  message: string,
  page: string,
  sessionId: string | null,
): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, page, session_id: sessionId }),
  });
  if (!res.ok) {
    throw new Error(`chat request failed: ${res.status}`);
  }
  return res.json();
}
