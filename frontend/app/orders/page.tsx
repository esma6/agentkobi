import { api } from "@/lib/api";
import { StatusBadge } from "@/components/StatusBadge";
import { OrdersFilter } from "@/components/OrdersFilter";
import { Package, Truck } from "lucide-react";

const STATUS_OPTIONS = [
  { value: "", label: "Tümü" },
  { value: "pending", label: "Beklemede" },
  { value: "confirmed", label: "Onaylandı" },
  { value: "preparing", label: "Hazırlanıyor" },
  { value: "shipped", label: "Kargoda" },
  { value: "delivered", label: "Teslim Edildi" },
  { value: "cancelled", label: "İptal" },
];

interface Props {
  searchParams: { status?: string; page?: string };
}

async function getData(searchParams: Props["searchParams"]) {
  try {
    return await api.orders({
      status: searchParams.status || undefined,
      page: Number(searchParams.page) || 1,
      per_page: 25,
    });
  } catch {
    return null;
  }
}

export default async function OrdersPage({ searchParams }: Props) {
  const data = await getData(searchParams);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Siparişler</h1>
        <p className="text-gray-500 text-sm mt-1">
          {data ? `${data.total} sipariş bulundu` : "Siparişler yükleniyor..."}
        </p>
      </div>

      {/* Filter */}
      <OrdersFilter options={STATUS_OPTIONS} current={searchParams.status ?? ""} />

      {/* Table */}
      {data ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-500">#</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Durum</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Tutar</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Kargo</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Takip No</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Kargo Durumu</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Tahmini Teslimat</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Oluşturulma</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.items.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-gray-500 font-medium">
                      #{order.order_number}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={order.status} />
                    </td>
                    <td className="px-4 py-3 font-semibold text-gray-800">
                      {order.total_amount.toLocaleString("tr-TR")} ₺
                    </td>
                    <td className="px-4 py-3 text-gray-600 capitalize">
                      {order.shipping_provider ? (
                        <span className="flex items-center gap-1">
                          <Truck className="w-3.5 h-3.5 text-gray-400" />
                          {order.shipping_provider.toUpperCase()}
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500">
                      {order.tracking_number ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      {order.shipping_status ? (
                        <span className="text-xs bg-cyan-50 text-cyan-700 px-2 py-0.5 rounded-full">
                          {order.shipping_status}
                        </span>
                      ) : (
                        <span className="text-gray-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {order.estimated_delivery ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {new Date(order.created_at).toLocaleDateString("tr-TR")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="border-t border-gray-100 px-4 py-3 flex items-center justify-between text-sm text-gray-500">
              <span>
                Sayfa {data.page} / {data.pages} ({data.total} sipariş)
              </span>
              <div className="flex gap-2">
                {data.page > 1 && (
                  <a
                    href={`?page=${data.page - 1}${searchParams.status ? "&status=" + searchParams.status : ""}`}
                    className="px-3 py-1 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors"
                  >
                    Önceki
                  </a>
                )}
                {data.page < data.pages && (
                  <a
                    href={`?page=${data.page + 1}${searchParams.status ? "&status=" + searchParams.status : ""}`}
                    className="px-3 py-1 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors"
                  >
                    Sonraki
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8 text-center">
          <Package className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Backend'e bağlanılamadı.</p>
        </div>
      )}
    </div>
  );
}
