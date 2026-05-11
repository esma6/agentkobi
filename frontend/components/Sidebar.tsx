"use client";

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
} from "lucide-react";
import { clsx } from "clsx";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/orders", label: "Siparişler", icon: ShoppingCart },
  { href: "/products", label: "Ürünler & Stok", icon: Package },
  { href: "/customers", label: "Müşteriler", icon: Users },
  { href: "/briefing", label: "Sabah Brifingi", icon: Bot },
];

export function Sidebar({ criticalCount = 0 }: { criticalCount?: number }) {
  const pathname = usePathname();

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
