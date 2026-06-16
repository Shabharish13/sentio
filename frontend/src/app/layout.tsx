import type { Metadata } from "next";
import "./globals.css";
import Nav from "@/components/Nav";
import Footer from "@/components/Footer";
import SageWidget from "@/components/SageWidget";
import { brand } from "@/lib/sentio";

export const metadata: Metadata = {
  title: `${brand.name} — ${brand.tagline}`,
  description: brand.valueProp,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="flex min-h-full flex-col">
        <Nav />
        <main className="flex-1">{children}</main>
        <Footer />
        <SageWidget />
      </body>
    </html>
  );
}
