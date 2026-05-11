import { api } from "@/lib/api";
import { Users, MapPin, Phone, Mail, ShoppingBag } from "lucide-react";

interface Props {
  searchParams: { page?: string };
}

async function getData(searchParams: Props["searchParams"]) {
  try {
    return await api.customers({
      page: Number(searchParams.page) || 1,
      per_page: 20,
    });
  } catch {
    return null;
  }
}

export default async function CustomersPage({ searchParams }: Props) {
  const data = await getData(searchParams);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Müşteriler</h1>
        <p className="text-gray-500 text-sm mt-1">
          {data ? `${data.total} müşteri` : "Yükleniyor..."}
        </p>
      </div>

      {data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {data.items.map((customer) => (
            <div
              key={customer.id}
              className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 hover:shadow-md transition-shadow"
            >
              {/* Avatar + Name */}
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-semibold text-sm shrink-0">
                  {customer.name
                    .split(" ")
                    .slice(-2)
                    .map((n: string) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2)}
                </div>
                <div className="min-w-0">
                  <p className="font-semibold text-gray-800 text-sm truncate">{customer.name}</p>
                  <p className="text-xs text-gray-400">
                    Müşteri since{" "}
                    {new Date(customer.created_at).toLocaleDateString("tr-TR", {
                      year: "numeric",
                      month: "short",
                    })}
                  </p>
                </div>
              </div>

              {/* Info rows */}
              <div className="space-y-1.5 text-xs text-gray-500">
                <div className="flex items-center gap-2">
                  <Phone className="w-3.5 h-3.5 text-gray-300 shrink-0" />
                  <span>{customer.phone}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="w-3.5 h-3.5 text-gray-300 shrink-0" />
                  <span className="truncate">{customer.email}</span>
                </div>
                <div className="flex items-start gap-2">
                  <MapPin className="w-3.5 h-3.5 text-gray-300 shrink-0 mt-0.5" />
                  <span className="line-clamp-2">{customer.address}</span>
                </div>
              </div>

              {/* Order count */}
              <div className="mt-3 pt-3 border-t border-gray-50 flex items-center gap-2">
                <ShoppingBag className="w-4 h-4 text-brand-500" />
                <span className="text-sm font-semibold text-gray-700">
                  {customer.total_orders}
                </span>
                <span className="text-xs text-gray-400">sipariş</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8 text-center">
          <Users className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">Backend'e bağlanılamadı.</p>
        </div>
      )}

      {/* Pagination */}
      {data && data.pages > 1 && (
        <div className="mt-6 flex justify-center gap-2 text-sm">
          {data.page > 1 && (
            <a href={`?page=${data.page - 1}`} className="px-4 py-2 rounded-lg bg-white border border-gray-200 hover:border-brand-300 text-gray-600 transition-colors">
              Önceki
            </a>
          )}
          <span className="px-4 py-2 text-gray-500">
            {data.page} / {data.pages}
          </span>
          {data.page < data.pages && (
            <a href={`?page=${data.page + 1}`} className="px-4 py-2 rounded-lg bg-brand-600 text-white hover:bg-brand-700 transition-colors">
              Sonraki
            </a>
          )}
        </div>
      )}
    </div>
  );
}
