"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { postChat } from "@/lib/api";
import { widget } from "@/lib/sentio";

interface Msg {
  role: "user" | "assistant";
  content: string;
  status?: string; // outcome badge for assistant turns
}

// Pages where the widget auto-opens after a delay (per website-copy.md). It is
// mounted on every page and is page-aware regardless.
const AUTO_OPEN_PAGES = ["/pricing", "/demo"];

function outcomeBadge(outcome: string, booked: boolean): string | undefined {
  if (booked) return "Demo booked — our team will reach out within one business day.";
  if (outcome === "escalate") return "Connecting you with a human teammate.";
  if (outcome === "disqualify") return undefined;
  if (outcome === "nurture") return "Shared a resource for you.";
  return undefined;
}

export default function SageWidget() {
  const pathname = usePathname() || "/";
  const [open, setOpen] = useState(false);
  const [autoOpened, setAutoOpened] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([
    { role: "assistant", content: widget.greeting },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoOpened || !AUTO_OPEN_PAGES.includes(pathname)) return;
    const t = setTimeout(() => {
      setOpen(true);
      setAutoOpened(true);
    }, 5000);
    return () => clearTimeout(t);
  }, [pathname, autoOpened]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending, open]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await postChat(text, pathname, sessionId);
      setSessionId(res.session_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.reply, status: outcomeBadge(res.outcome, res.booked) },
      ]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: widget.connectionError }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      {open && (
        <div className="fixed bottom-24 right-6 z-50 flex h-[28rem] w-[22rem] max-w-[calc(100vw-3rem)] flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-2xl">
          <div className="flex items-center justify-between bg-brand px-4 py-3 text-white">
            <div>
              <p className="text-sm font-semibold">{widget.headerTitle}</p>
              <p className="text-xs text-brand-soft">{widget.headerStatus}</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-brand-soft transition-colors hover:text-white"
              aria-label={widget.launcherClose}
            >
              ✕
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto bg-surface px-4 py-4">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                <div
                  className={`inline-block max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                    m.role === "user"
                      ? "bg-brand text-white"
                      : "border border-line bg-white text-ink"
                  }`}
                >
                  {m.content}
                </div>
                {m.status && (
                  <p className="mt-1 text-xs font-medium text-health">{m.status}</p>
                )}
              </div>
            ))}
            {sending && (
              <div className="text-left">
                <div className="inline-block rounded-2xl border border-line bg-white px-3 py-2 text-sm text-faint">
                  {widget.typing}
                </div>
              </div>
            )}
          </div>

          <form
            className="flex items-center gap-2 border-t border-line bg-white px-3 py-3"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={widget.inputPlaceholder}
              className="flex-1 rounded-lg border border-line px-3 py-2 text-sm outline-none focus:border-brand"
            />
            <button type="submit" disabled={sending} className="btn-primary disabled:opacity-50">
              {widget.send}
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-50 rounded-full bg-brand px-5 py-3 text-sm font-semibold text-white shadow-lg transition-colors hover:bg-brand-dark"
      >
        {open ? widget.launcherClose : widget.launcherOpen}
      </button>
    </>
  );
}
