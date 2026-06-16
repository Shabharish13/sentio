import Link from "next/link";
import { brand, nav } from "@/lib/sentio";

export default function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-white/80 backdrop-blur">
      <div className="container-x flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-white">
            S
          </span>
          <span className="text-lg font-bold tracking-tight text-ink">{brand.name}</span>
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {nav.links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted transition-colors hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <Link href={nav.cta.href} className="btn-primary">
          {nav.cta.label}
        </Link>
      </div>
    </header>
  );
}
