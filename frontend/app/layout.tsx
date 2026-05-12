import type { Metadata } from "next";
import "./globals.css";
import { LayoutShell } from "@/components/LayoutShell";

export const metadata: Metadata = {
  title: "AgentKobi - KOBİ AI Asistanı",
  description: "Sipariş takibi, stok uyarısı ve sabah brifingi",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        <LayoutShell>{children}</LayoutShell>
      </body>
    </html>
  );
}
