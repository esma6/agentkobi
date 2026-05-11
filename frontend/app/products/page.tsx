import { api } from "@/lib/api";
import { CriticalStockAlert } from "@/components/CriticalStockAlert";
import { AlertTriangle, Package, TrendingDown } from "lucide-react";
import { clsx } from "clsx";

interface Props {
  searchParams: { low_stock?: string; page?: string };
}

async function getData(searchParams: Props["searchParams"]) {
  try {
    const [products, critical] = await Promise.all([
      api.products({
        low_stock: searchParams.low_stock === "1",
        page: Number(searchParams.page) || 1,
        per_page: 30,
      }),
      api.criticalStock(),
    ]);
    return { products, critical };
  } catch {
    return { products: null, critical: null };
  }
}

export default async function ProductsPage({ searchParams }: Props) {
  const { products, critical } = await getData(searchParams);
  const showLow = searchParams.low_stock === "1";

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Ürünler & Stok</h1>
        <p className="text-gray-500 text-sm mt-1">
          {products ? `${products.total} ürün` : "Yükleniyor..."}
        </p>
      </div>

      {critical && critical.count > 0 && (
        <CriticalStockAlert items={critical.items} />
      )}

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        <a
          href="/products"
          className={clsx(
            "px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
            !showLow
              ? "bg-brand-600 text-white"
              : "bg-white text-gray-600 border border-gray-200 hover:border-brand-300"
          )}
        >
          Tümü
        </a>
        <a
          href="/products?low_stock=1"
          className={clsx(
            "px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1.5",
            showLow
              ? "bg-red-600 text-white"
              : "bg-white text-gray-600 border border-gray-200 hover:border-red-300"
          )}
        >
          <AlertTriangle className="w-3.5 h-3.5" />
          Kritik Stok
          {critical && critical.count > 0 && (
            <span
              className={clsx(
                "ml-1 rounded-full px-1.5 py-0.5 text-xs font-bold",
                showLow ? "bg-red-400 text-white" : "bg-red-100 text-red-700"
              )}
            >
              {critical.count}
            </span>
          )}
        </a>
      </div>

      {/* Table */}
      {products ? (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-500">SKU</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Ürün Adı</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Fiyat</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Stok</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Eşik</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Birim</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Doluluk</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-500">Durum</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {products.items.map((product) => {
                  const pct = Math.min(
                    100,
                    Math.round((product.stock_quantity / product.reorder_threshold) * 100)
                  );
                  const barColor =
                    pct < 50 ? "bg-red-500" : pct < 80 ? "bg-amber-400" : "bg-brand-500";

                  return (
                    <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">
                        {product.sku}
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-800">{product.name}</td>
                      <td className="px-4 py-3 text-gray-700 font-semibold">
                        {product.price.toLocaleString("tr-TR")} ₺
                      </td>
                      <td className="px-4 py-3 font-semibold">
                        <span
                          className={clsx(
                            product.is_critical ? "text-red-600" : "text-gray-800"
                          )}
                        >
                          {product.stock_quantity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{product.reorder_threshold}</td>
                      <td className="px-4 py-3 text-gray-500">{product.unit}</td>
                      <td className="px-4 py-3 w-32">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${barColor}`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-400 w-8 text-right">{pct}%</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        {product.is_critical ? (
                          <span className="flex items-center gap-1 text-xs text-red-600 font-medium">
                            <TrendingDown className="w-3.5 h-3.5" />
                            Kritik
                          </span>
                        ) : (
                          <span className="text-xs text-brand-600 font-medium">Normal</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {products.pages > 1 && (
            <div className="border-t border-gray-100 px-4 py-3 flex items-center justify-between text-sm text-gray-500">
              <span>Sayfa {products.page} / {products.pages}</span>
              <div className="flex gap-2">
                {products.page > 1 && (
                  <a href={`?page=${products.page - 1}`} className="px-3 py-1 rounded-lg bg-gray-100 hover:bg-gray-200">
                    Önceki
                  </a>
                )}
                {products.page < products.pages && (
                  <a href={`?page=${products.page + 1}`} className="px-3 py-1 rounded-lg bg-brand-600 text-white hover:bg-brand-700">
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
