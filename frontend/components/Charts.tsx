"use client";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";

const STATUS_COLORS: Record<string, string> = {
  "Beklemede": "#f59e0b",
  "Onaylandı": "#3b82f6",
  "Hazırlanıyor": "#8b5cf6",
  "Kargoda": "#06b6d4",
  "Teslim Edildi": "#22c55e",
  "İptal": "#ef4444",
};

const FALLBACK_COLORS = [
  "#22c55e", "#3b82f6", "#f59e0b", "#8b5cf6", "#06b6d4", "#ef4444",
];

interface StatusPieChartProps {
  data: Record<string, number>;
}

export function StatusPieChart({ data }: StatusPieChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({ name, value }));

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={STATUS_COLORS[entry.name] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]}
            />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number, name: string) => [value + " sipariş", name]}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          wrapperStyle={{ fontSize: "12px" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}

interface RevenueBarChartProps {
  data: Record<string, number>;
}

export function RevenueBarChart({ data }: RevenueBarChartProps) {
  const chartData = Object.entries(data)
    .filter(([, v]) => v > 0)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value);

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis
          tick={{ fontSize: 11 }}
          tickFormatter={(v) => `${(v / 1000).toFixed(0)}K ₺`}
        />
        <Tooltip
          formatter={(value: number) => [`${value.toLocaleString("tr-TR")} ₺`, "Ciro"]}
        />
        <Bar dataKey="value" fill="#22c55e" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface StockBarProps {
  name: string;
  current: number;
  threshold: number;
  unit: string;
}

export function StockProgressBar({ name, current, threshold, unit }: StockBarProps) {
  const pct = Math.min(100, Math.round((current / threshold) * 100));
  const color = pct < 50 ? "bg-red-500" : pct < 80 ? "bg-amber-400" : "bg-brand-500";

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="font-medium text-gray-700 truncate max-w-[140px]">{name}</span>
        <span className="text-gray-500 shrink-0">
          {current} / {threshold} {unit}
        </span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
