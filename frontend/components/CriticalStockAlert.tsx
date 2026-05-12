"use client";

import { AlertTriangle, X } from "lucide-react";
import { useState } from "react";
import type { CriticalStockItem } from "@/lib/api";

export function CriticalStockAlert({ items }: { items: CriticalStockItem[] }) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed || items.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-red-800">
              {items.length} Ürün Kritik Stok Seviyesinde
            </h3>
            <p className="text-xs text-red-600 mt-0.5">Tedarikçiye sipariş vermeniz önerilir.</p>
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="text-red-400 hover:text-red-600 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="mt-3 space-y-2">
        {items.slice(0, 5).map((item) => (
          <div
            key={item.id}
            className="flex items-center justify-between bg-white rounded-lg px-3 py-2 text-sm border border-red-100"
          >
            <div>
              <span className="font-medium text-gray-800">{item.name}</span>
              <span className="text-gray-400 ml-1.5 text-xs">({item.sku})</span>
            </div>
            <div className="text-right">
              <span className="text-red-700 font-semibold">
                {item.stock_quantity} {item.unit}
              </span>
              <span className="text-gray-400 text-xs ml-1">
                / {item.reorder_threshold} eşik
              </span>
            </div>
          </div>
        ))}
        {items.length > 5 && (
          <p className="text-xs text-red-500 pl-1">+{items.length - 5} daha...</p>
        )}
      </div>
    </div>
  );
}
