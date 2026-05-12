import { clsx } from "clsx";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: "green" | "blue" | "amber" | "red" | "purple";
  trend?: { value: number; label: string };
}

const colorMap = {
  green: {
    bg: "bg-brand-50",
    icon: "bg-brand-100 text-brand-700",
    text: "text-brand-700",
  },
  blue: {
    bg: "bg-blue-50",
    icon: "bg-blue-100 text-blue-700",
    text: "text-blue-700",
  },
  amber: {
    bg: "bg-amber-50",
    icon: "bg-amber-100 text-amber-700",
    text: "text-amber-700",
  },
  red: {
    bg: "bg-red-50",
    icon: "bg-red-100 text-red-700",
    text: "text-red-700",
  },
  purple: {
    bg: "bg-purple-50",
    icon: "bg-purple-100 text-purple-700",
    text: "text-purple-700",
  },
};

export function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = "green",
  trend,
}: StatsCardProps) {
  const c = colorMap[color];

  return (
    <div className={clsx("rounded-xl p-5 border border-gray-100 bg-white shadow-sm")}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              <span
                className={clsx(
                  "text-xs font-semibold",
                  trend.value >= 0 ? "text-brand-600" : "text-red-500"
                )}
              >
                {trend.value >= 0 ? "+" : ""}
                {trend.value}%
              </span>
              <span className="text-xs text-gray-400">{trend.label}</span>
            </div>
          )}
        </div>
        <div className={clsx("p-3 rounded-xl", c.icon)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
