import { BriefingPanel } from "@/components/BriefingPanel";

export default function BriefingPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Sabah Brifingi</h1>
        <p className="text-gray-500 text-sm mt-1">
          AI ajanları günlük durumu analiz eder ve özet üretir.
        </p>
      </div>
      <BriefingPanel />
    </div>
  );
}
