"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { api } from "@/lib/api";

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const [criticalCount, setCriticalCount] = useState(0);

  useEffect(() => {
    api.criticalStock().then((d) => setCriticalCount(d.count)).catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar criticalCount={criticalCount} />
      <main className="ml-[240px] flex-1 min-h-screen">
        <div className="max-w-7xl mx-auto px-6 py-8">{children}</div>
      </main>
    </div>
  );
}
