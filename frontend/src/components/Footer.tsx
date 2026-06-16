import Link from "next/link";
import { footer } from "@/lib/sentio";

export default function Footer() {
  return (
    <footer className="border-t border-line bg-surface">
      <div className="container-x flex flex-col gap-6 py-12 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-brand text-xs font-bold text-white">
            S
          </span>
          <span className="text-sm font-semibold text-ink">{footer.tagline}</span>
        </div>
        <nav className="flex flex-wrap gap-x-6 gap-y-2">
          {footer.links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-muted transition-colors hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="container-x pb-8">
        <p className="text-xs text-faint">{footer.disclaimer}</p>
      </div>
    </footer>
  );
}
