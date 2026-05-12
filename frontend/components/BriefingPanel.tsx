"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import {
  Bot,
  Loader2,
  SendHorizonal,
  CheckCircle,
  AlertTriangle,
  Info,
} from "lucide-react";

interface BriefingResult {
  ok: boolean;
  briefing: string;
  used_fallback: boolean;
  errors: string[];
}

const AGENTS = [
  { name: "Sipariş Ajanı", desc: "Dünkü ve bugünkü siparişleri analiz eder", icon: "📦" },
  { name: "Stok Ajanı", desc: "Kritik stok seviyelerini tespit eder", icon: "🏪" },
  { name: "Kargo Ajanı", desc: "Gecikme ve kargo durumlarını kontrol eder", icon: "🚚" },
  { name: "Tedarikçi Ajanı", desc: "Sipariş taslakları hazırlar", icon: "📋" },
  { name: "RAG Modülü", desc: "Geçmiş brifingleri karşılaştırır", icon: "🧠" },
  { name: "Briefing LLM", desc: "Özet metin üretir", icon: "✨" },
  { name: "Validator", desc: "Halüsinasyon kontrolü yapar", icon: "🛡️" },
];

export function BriefingPanel() {
  const [state, setState] = useState<"idle" | "running" | "done" | "error">("idle");
  const [result, setResult] = useState<BriefingResult | null>(null);
  const [activeAgent, setActiveAgent] = useState(-1);

  async function handleRun() {
    setState("running");
    setResult(null);
    setActiveAgent(0);

    // Simulate agent progress while waiting
    const interval = setInterval(() => {
      setActiveAgent((prev) => {
        if (prev < AGENTS.length - 1) return prev + 1;
        return prev;
      });
    }, 600);

    try {
      const res = await api.runBriefing();
      clearInterval(interval);
      setActiveAgent(AGENTS.length);
      setResult(res);
      setState("done");
    } catch (err) {
      clearInterval(interval);
      setState("error");
      setResult({
        ok: false,
        briefing: "",
        used_fallback: false,
        errors: [err instanceof Error ? err.message : "Bilinmeyen hata"],
      });
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left: Control panel */}
      <div className="space-y-4">
        {/* Run card */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-brand-100 rounded-xl flex items-center justify-center">
              <Bot className="w-5 h-5 text-brand-700" />
            </div>
            <div>
              <h2 className="font-semibold text-gray-800">Günlük Brifing</h2>
              <p className="text-xs text-gray-400">LangGraph multi-agent workflow</p>
            </div>
          </div>

          <p className="text-sm text-gray-500 mb-5">
            7 ajan paralel ve sıralı çalışarak günlük işletme özetinizi hazırlar:
            sipariş durumu, kritik stoklar, kargo gecikmeleri ve tedarikçi taslakları.
          </p>

          <button
            onClick={handleRun}
            disabled={state === "running"}
            className="w-full flex items-center justify-center gap-2 py-3 px-6 rounded-xl font-semibold text-white bg-brand-600 hover:bg-brand-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md"
          >
            {state === "running" ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Ajanlar çalışıyor...
              </>
            ) : (
              <>
                <SendHorizonal className="w-4 h-4" />
                Şimdi Gönder
              </>
            )}
          </button>
        </div>

        {/* Agent pipeline visualization */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Agent Pipeline</h3>
          <div className="space-y-2">
            {AGENTS.map((agent, i) => {
              const done = state === "done" || (state === "running" && i < activeAgent);
              const active = state === "running" && i === activeAgent;

              return (
                <div
                  key={agent.name}
                  className={`flex items-center gap-3 p-2.5 rounded-lg transition-all ${
                    active
                      ? "bg-brand-50 border border-brand-200"
                      : done
                      ? "bg-gray-50"
                      : "opacity-50"
                  }`}
                >
                  <span className="text-lg w-7 text-center">{agent.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-700">{agent.name}</p>
                    <p className="text-xs text-gray-400 truncate">{agent.desc}</p>
                  </div>
                  <div className="shrink-0">
                    {active && (
                      <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />
                    )}
                    {done && (
                      <CheckCircle className="w-4 h-4 text-brand-500" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right: Result */}
      <div>
        {state === "idle" && (
          <div className="bg-white rounded-xl border border-dashed border-gray-200 p-8 text-center h-full flex flex-col items-center justify-center">
            <Bot className="w-12 h-12 text-gray-200 mb-4" />
            <p className="text-gray-400 text-sm">
              &ldquo;Şimdi Gönder&rdquo; butonuna basarak brifing başlatın.
            </p>
          </div>
        )}

        {state === "running" && (
          <div className="bg-white rounded-xl border border-brand-100 shadow-sm p-8 text-center h-full flex flex-col items-center justify-center">
            <div className="w-16 h-16 bg-brand-50 rounded-full flex items-center justify-center mb-4 mx-auto">
              <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
            </div>
            <p className="font-semibold text-gray-700">Ajanlar çalışıyor...</p>
            <p className="text-sm text-gray-400 mt-1">
              {AGENTS[Math.min(activeAgent, AGENTS.length - 1)]?.name} aktif
            </p>
          </div>
        )}

        {(state === "done" || state === "error") && result && (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 h-full">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4">
              {result.ok ? (
                <>
                  <CheckCircle className="w-5 h-5 text-brand-500" />
                  <h3 className="font-semibold text-gray-800">Brifing Hazır</h3>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <h3 className="font-semibold text-gray-800">Hata Oluştu</h3>
                </>
              )}
            </div>

            {/* Briefing text */}
            {result.briefing && (
              <div className="bg-gray-50 rounded-xl p-4 text-sm text-gray-700 leading-relaxed mb-4 border border-gray-100">
                {result.briefing}
              </div>
            )}

            {/* Fallback notice */}
            {result.used_fallback && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg border border-amber-100 text-xs text-amber-700 mb-3">
                <Info className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                <span>
                  LLM çağrısı yapılamadı; deterministik şablon kullanıldı. API anahtarlarını{" "}
                  <code className="font-mono">.env</code> dosyasında ayarlayın.
                </span>
              </div>
            )}

            {/* Errors */}
            {result.errors && result.errors.length > 0 && (
              <div className="space-y-1">
                {result.errors.map((e, i) => (
                  <p key={i} className="text-xs text-red-500 font-mono bg-red-50 px-2 py-1 rounded">
                    {e}
                  </p>
                ))}
              </div>
            )}

            {/* Re-run */}
            <button
              onClick={handleRun}
              className="mt-4 w-full py-2.5 px-4 rounded-lg border border-brand-200 text-brand-700 text-sm font-medium hover:bg-brand-50 transition-colors"
            >
              Tekrar Çalıştır
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
