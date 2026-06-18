import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SiteHeader } from "@/components/SiteHeader";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://centri-cinofili.it"),
  title: {
    default: "Centri Cinofili Italia — Registro nazionale dei centri educativi cinofili",
    template: "%s · Centri Cinofili Italia",
  },
  description:
    "Il primo portale verticale italiano dedicato alla mappatura e classificazione dei centri cinofili. Filtra per metodologia educativa, disciplina e infrastruttura.",
  openGraph: {
    title: "Centri Cinofili Italia",
    description:
      "Registro nazionale dei centri cinofili italiani. Filtra per metodo, disciplina e regione.",
    type: "website",
    locale: "it_IT",
    siteName: "Centri Cinofili Italia",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="it"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-[color:var(--ds-gray-900)]">
        <SiteHeader />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-[color:var(--ds-gray-100)] py-10">
          <div className="mx-auto max-w-7xl px-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="text-sm text-[color:var(--ds-gray-500)]">
              © {new Date().getFullYear()} Centri Cinofili Italia · Dati aperti, licenza CC BY 4.0
            </div>
            <nav className="flex items-center gap-5 text-sm">
              <a href="/" className="text-[color:var(--ds-gray-600)] hover:text-[color:var(--ds-gray-900)]">
                Cerca
              </a>
              <a href="/centri-cinofili/" className="text-[color:var(--ds-gray-600)] hover:text-[color:var(--ds-gray-900)]">
                Directory
              </a>
            </nav>
          </div>
        </footer>
      </body>
    </html>
  );
}