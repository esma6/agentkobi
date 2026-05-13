"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ShoppingCart,
  Package,
  Users,
  Bot,
  TrendingUp,
  AlertTriangle,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { clsx } from "clsx";
import { api } from "@/lib/api";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/orders", label: "Siparişler", icon: ShoppingCart },
  { href: "/products", label: "Ürünler & Stok", icon: Package },
  { href: "/customers", label: "Müşteriler", icon: Users },
  { href: "/briefing", label: "Sabah Brifingi", icon: Bot },
];

type SendStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; telegram: boolean; email: boolean }
  | { kind: "error"; message: string };

export function Sidebar({ criticalCount = 0 }: { criticalCount?: number }) {
  const pathname = usePathname();
  const [status, setStatus] = useState<SendStatus>({ kind: "idle" });

  const handleSend = async () => {
    if (status.kind === "loading") return;
    setStatus({ kind: "loading" });
    try {
      const res = await api.sendBriefing();
      setStatus({
        kind: "success",
        telegram: res.channels?.telegram ?? false,
        email: res.channels?.email ?? false,
      });
    } catch (err) {
      setStatus({
        kind: "error",
        message: err instanceof Error ? err.message : "Bilinmeyen hata",
      });
    }
    setTimeout(() => setStatus({ kind: "idle" }), 6000);
  };

  return (
    <aside className="fixed left-0 top-0 h-full w-[240px] bg-brand-950 text-white flex flex-col z-40">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-brand-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight">AgentKobi</span>
        </div>
        <p className="text-brand-400 text-xs mt-1">KOBİ AI Asistanı</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          const isBriefing = href === "/products" && criticalCount > 0;
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                active
                  ? "bg-brand-700 text-white"
                  : "text-brand-300 hover:bg-brand-900 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="flex-1">{label}</span>
              {isBriefing && (
                <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center badge-pulse">
                  {criticalCount}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Brifingi Şimdi Gönder */}
      <div className="px-3 pb-3">
        <button
          type="button"
          onClick={handleSend}
          disabled={status.kind === "loading"}
          className={clsx(
            "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all",
            status.kind === "loading"
              ? "bg-brand-700 text-brand-200 cursor-wait"
              : "bg-brand-500 hover:bg-brand-400 text-white shadow-lg shadow-brand-900/40"
          )}
          title="Brifingi Telegram ve E-posta üzerinden hemen gönder"
        >
          {status.kind === "loading" ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Gönderiliyor…</span>
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              <span>Brifingi Şimdi Gönder</span>
            </>
          )}
        </button>
        {status.kind === "success" && (
          <div className="mt-2 p-2 rounded-md bg-brand-900/60 border border-brand-700/60 text-xs space-y-1">
            <div className="flex items-center gap-2 text-brand-200">
              {status.telegram ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <XCircle className="w-3.5 h-3.5 text-red-400" />
              )}
              <span>Telegram</span>
            </div>
            <div className="flex items-center gap-2 text-brand-200">
              {status.email ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <XCircle className="w-3.5 h-3.5 text-red-400" />
              )}
              <span>E-posta</span>
            </div>
          </div>
        )}
        {status.kind === "error" && (
          <div className="mt-2 p-2 rounded-md bg-red-900/40 border border-red-700/50 text-xs text-red-200">
            Hata: {status.message}
          </div>
        )}
      </div>

      {/* Footer */}
      {criticalCount > 0 && (
        <div className="mx-3 mb-4 p-3 bg-red-900/40 border border-red-700/50 rounded-lg">
          <div className="flex items-center gap-2 text-red-300 text-xs font-medium">
            <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
            <span>{criticalCount} ürün kritik stokta</span>
          </div>
        </div>
      )}

      <div className="px-6 py-4 border-t border-brand-800">
        <p className="text-brand-500 text-xs">Demo İşletme</p>
        <p className="text-brand-400 text-xs">Demo Sahibi</p>
      </div>
    </aside>
  );
}
