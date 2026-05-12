import { api } from "@/lib/api";
import { StatsCard } from "@/components/StatsCard";
import { CriticalStockAlert } from "@/components/CriticalStockAlert";
import { StatusPieChart, RevenueBarChart, StockProgressBar } from "@/components/Charts";
import {
  ShoppingCart,
  TrendingUp,
  Truck,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from "lucide-react";

async function getData() {
  try {
    const [stats, critical] = await Promise.all([
      api.dashboardStats(),
      api.criticalStock(),
    ]);
    return { stats, critical };
  } catch {
    return { stats: null, critical: null };
  }
}

export default async function DashboardPage() {
  const { stats, critical } = await getData();

  if (!stats) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <AlertTriangle className="w-12 h-12 text-amber-400 mb-4" />
        <h2 className="text-lg font-semibold text-gray-700">Backend'e bağlanılamadı</h2>
        <p className="text-sm text-gray-400 mt-2">
          Lütfen <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">docker compose up</code> komutunu
          çalıştırın.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Demo İşletme — Genel Bakış</p>
      </div>

      {/* Critical stock alert */}
      {critical && critical.count > 0 && (
        <CriticalStockAlert items={critical.items} />
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 mb-8">
        <div className="col-span-2 xl:col-span-2">
          <StatsCard
            title="Toplam Sipariş"
            value={stats.total_orders}
            subtitle="Tüm zamanlar"
            icon={ShoppingCart}
            color="blue"
          />
        </div>
        <div className="col-span-2 xl:col-span-2">
          <StatsCard
            title="Toplam Ciro"
            value={`${stats.total_revenue.toLocaleString("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ₺`}
            subtitle="Tüm siparişler"
            icon={TrendingUp}
            color="green"
          />
        </div>
        <div className="col-span-1 xl:col-span-1">
          <StatsCard
            title="Aktif"
            value={stats.active_orders}
            subtitle="Siparişler"
            icon={CheckCircle}
            color="purple"
          />
        </div>
        <div className="col-span-1 xl:col-span-1">
          <StatsCard
            title="Kargoda"
            value={stats.shipped_orders}
            icon={Truck}
            color="blue"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-8">
        <div className="col-span-1">
          <StatsCard
            title="İptal Edilen"
            value={stats.cancelled_orders}
            subtitle="Toplam iptal"
            icon={XCircle}
            color="red"
          />
        </div>
        <div className="col-span-1">
          <StatsCard
            title="Kritik Stok"
            value={stats.critical_stock_count}
            subtitle="Ürün eşiğin altında"
            icon={AlertTriangle}
            color="amber"
          />
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Status distribution */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Sipariş Durumu Dağılımı
          </h3>
          <StatusPieChart data={stats.status_distribution} />
        </div>

        {/* Revenue by status */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Duruma Göre Ciro (₺)
          </h3>
          <RevenueBarChart data={stats.status_revenue} />
        </div>
      </div>

      {/* Critical Stock Progress */}
      {critical && critical.count > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-sm font-semibold text-gray-700">
              Kritik Stok Seviyeleri
            </h3>
            <span className="text-xs text-gray-400">{critical.count} ürün</span>
          </div>
          <div className="space-y-4">
            {critical.items.map((item) => (
              <StockProgressBar
                key={item.id}
                name={item.name}
                current={item.stock_quantity}
                threshold={item.reorder_threshold}
                unit={item.unit}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
