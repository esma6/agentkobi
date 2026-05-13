// Next.js'de bu modül hem server (Node.js, container içi) hem client (tarayıcı)
// tarafında import edilir. İki tarafın farklı URL kullanması gerek:
//   - Server tarafı (container içi):  http://backend:8000  (docker network içi servis adı)
//   - Client tarafı  (tarayıcı):      http://localhost:8000 (host'taki port mapping)
//
// `typeof window === "undefined"` kontrolü server/client ayrımı için kullanılır.
// SERVER_API_URL compose'ta tanımlanır (NEXT_PUBLIC_ değil — sadece server'da görünür).
const BASE =
  typeof window === "undefined"
    ? process.env.SERVER_API_URL ?? "http://backend:8000"
    : process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export interface DashboardStats {
  total_orders: number;
  total_revenue: number;
  active_orders: number;
  shipped_orders: number;
  cancelled_orders: number;
  critical_stock_count: number;
  status_distribution: Record<string, number>;
  status_revenue: Record<string, number>;
}

export interface Order {
  id: string;
  order_number: number;
  customer_id: string;
  status: string;
  status_label: string;
  total_amount: number;
  shipping_provider: string | null;
  tracking_number: string | null;
  shipping_status: string | null;
  estimated_delivery: string | null;
  notes: string | null;
  created_at: string;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  description: string;
  price: number;
  stock_quantity: number;
  reorder_threshold: number;
  unit: string;
  is_critical: boolean;
}

export interface CriticalStockItem {
  id: string;
  sku: string;
  name: string;
  unit: string;
  stock_quantity: number;
  reorder_threshold: number;
  eksik_miktar: number;
  doluluk_yuzde: number;
  price: number;
}

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email: string;
  address: string;
  total_orders: number;
  created_at: string;
}

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  per_page: number;
  pages: number;
  items: T[];
}

export const api = {
  dashboardStats: () => get<DashboardStats>("/api/dashboard/stats"),

  orders: (params?: { status?: string; page?: number; per_page?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.page) q.set("page", String(params.page));
    if (params?.per_page) q.set("per_page", String(params.per_page));
    return get<PaginatedResponse<Order>>(`/api/orders${q.toString() ? "?" + q : ""}`);
  },

  products: (params?: { low_stock?: boolean; page?: number; per_page?: number }) => {
    const q = new URLSearchParams();
    if (params?.low_stock) q.set("low_stock", "true");
    if (params?.page) q.set("page", String(params.page));
    if (params?.per_page) q.set("per_page", String(params.per_page));
    return get<PaginatedResponse<Product>>(`/api/products${q.toString() ? "?" + q : ""}`);
  },

  criticalStock: () => get<{ count: number; items: CriticalStockItem[] }>("/api/stock/critical"),

  customers: (params?: { page?: number; per_page?: number }) => {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.per_page) q.set("per_page", String(params.per_page));
    return get<PaginatedResponse<Customer>>(`/api/customers${q.toString() ? "?" + q : ""}`);
  },

  runBriefing: () =>
    post<{ ok: boolean; briefing: string; used_fallback: boolean; errors: string[] }>(
      "/api/briefing/run",
      {
        business_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        business_name: "Demo İşletme",
        owner_name: "Demo Sahibi",
        trigger_source: "manual",
      }
    ),
};
