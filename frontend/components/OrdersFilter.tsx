"use client";

import { useRouter, usePathname } from "next/navigation";

interface Option {
  value: string;
  label: string;
}

export function OrdersFilter({ options, current }: { options: Option[]; current: string }) {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <div className="flex flex-wrap gap-2 mb-4">
      {options.map((opt) => (
        <button
          key={opt.value}
          onClick={() => {
            const q = opt.value ? `?status=${opt.value}` : "";
            router.push(pathname + q);
          }}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            current === opt.value
              ? "bg-brand-600 text-white shadow-sm"
              : "bg-white text-gray-600 border border-gray-200 hover:border-brand-300 hover:text-brand-700"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
