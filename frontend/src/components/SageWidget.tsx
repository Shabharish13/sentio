"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { postChat } from "@/lib/api";
import { widget } from "@/lib/sentio";

interface Msg {
  role: "user" | "assistant";
  content: string;
  status?: string; // outcome badge for assistant turns
  animate?: boolean; // typewriter the assistant answer on arrival
}

// Pages where the widget auto-opens after a delay (per website-copy.md). It is
// mounted on every page and is page-aware regardless.
const AUTO_OPEN_PAGES = ["/pricing", "/demo"];

function outcomeBadge(outcome: string, booked: boolean): string | undefined {
  if (booked) return "Demo booked - our team will reach out within one business day.";
  if (outcome === "escalate") return "Shared with our sales team - they'll follow up by email.";
  if (outcome === "disqualify") return undefined;
  if (outcome === "nurture") return "Shared a resource for you.";
  return undefined;
}

// --- Minimal, safe markdown -> React renderer (no new dependencies). ---------
// Handles **bold**, simple bullet lists (- / *), and line breaks. Plain text
// only; no raw HTML is ever injected, so this is XSS-safe by construction.
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  const regex = /\*\*([^*]+)\*\*/g;
  let last = 0;
  let match: RegExpExecArray | null;
  let i = 0;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) nodes.push(text.slice(last, match.index));
    nodes.push(<strong key={`${keyPrefix}-b${i++}`}>{match[1]}</strong>);
    last = match.index + match[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return nodes;
}

function Markdown({ text }: { text: string }) {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  let bullets: string[] = [];
  let key = 0;

  const flushBullets = () => {
    if (bullets.length === 0) return;
    const items = bullets;
    blocks.push(
      <ul key={`ul${key++}`} className="my-1 list-disc space-y-0.5 pl-4">
        {items.map((b, j) => (
          <li key={j}>{renderInline(b, `li${key}-${j}`)}</li>
        ))}
      </ul>,
    );
    bullets = [];
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    if (bullet) {
      bullets.push(bullet[1]);
      continue;
    }
    flushBullets();
    if (line.trim() === "") continue;
    blocks.push(
      <p key={`p${key++}`} className="my-1 first:mt-0 last:mb-0">
        {renderInline(line, `p${key}`)}
      </p>,
    );
  }
  flushBullets();
  return <>{blocks}</>;
}

// Word-by-word typewriter that renders the revealed substring as markdown.
function TypewriterMarkdown({ text, onTick }: { text: string; onTick?: () => void }) {
  const [count, setCount] = useState(0);
  const words = text.split(/(\s+)/); // keep whitespace tokens so spacing is preserved

  useEffect(() => {
    if (count >= words.length) return;
    const t = setTimeout(() => {
      setCount((c) => c + 1);
      onTick?.();
    }, 28);
    return () => clearTimeout(t);
  }, [count, words.length, onTick]);

  const shown = words.slice(0, count).join("");
  return <Markdown text={shown || ""} />;
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

  const scrollToBottom = () =>
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });

  useEffect(() => {
    scrollToBottom();
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
      const answer = res.answer ?? res.reply;
      setMessages((m) => {
        const next: Msg[] = [
          ...m,
          {
            role: "assistant",
            content: answer,
            status: outcomeBadge(res.outcome, res.booked),
            animate: true,
          },
        ];
        // Qualifying question (when present) is a separate bubble after the answer.
        if (res.question) {
          next.push({ role: "assistant", content: res.question, animate: true });
        }
        return next;
      });
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
                  className={`inline-block max-w-[85%] rounded-2xl px-3 py-2 text-left text-sm ${
                    m.role === "user"
                      ? "bg-brand text-white"
                      : "border border-line bg-white text-ink"
                  }`}
                >
                  {m.role === "assistant" && m.animate ? (
                    <TypewriterMarkdown text={m.content} onTick={scrollToBottom} />
                  ) : m.role === "assistant" ? (
                    <Markdown text={m.content} />
                  ) : (
                    m.content
                  )}
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
