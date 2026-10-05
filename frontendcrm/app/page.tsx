'use client';

import { useEffect, useState } from 'react';
import { ManagementReport, MarketingStats, apiService, getErrorMessage } from '@/services/api';

export default function HomeDashboard() {
  const [report, setReport] = useState<ManagementReport | null>(null);
  const [marketing, setMarketing] = useState<MarketingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [reportData, marketingData] = await Promise.all([
          apiService.reportes.getInformeGerencial(),
          apiService.marketing.getStats(),
        ]);
        if (active) {
          setReport(reportData);
          setMarketing(marketingData);
        }
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar el panel.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  if (loading) return <p className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500" role="status">Cargando indicadores…</p>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Panel de control</h1>
        <p className="mt-1 text-sm text-slate-500">Resumen operativo del CRM y los eventos.</p>
      </header>

      {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores principales">
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Cotizaciones</p><p className="mt-2 text-3xl font-bold text-slate-900">{report?.resumen_conversion.total ?? 0}</p></article>
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Aceptadas</p><p className="mt-2 text-3xl font-bold text-indigo-700">{report?.resumen_conversion.aceptadas ?? 0}</p></article>
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ingresos reales</p><p className="mt-2 text-3xl font-bold text-emerald-700">${Number(marketing?.resumen_ventas.total_ingresos ?? 0).toLocaleString('es', { maximumFractionDigits: 2 })}</p></article>
        <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pendientes</p><p className="mt-2 text-3xl font-bold text-amber-600">{report?.resumen_conversion.pendientes ?? 0}</p></article>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="conversion-title">
          <h2 id="conversion-title" className="font-semibold text-slate-800">Conversión comercial</h2>
          <p className="mt-4 text-5xl font-bold text-indigo-700">{report?.resumen_conversion.tasa_exito_porcentaje ?? 0}%</p>
          <p className="mt-2 text-sm text-slate-500">Cotizaciones aceptadas sobre el total emitido.</p>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="sales-title">
          <h2 id="sales-title" className="font-semibold text-slate-800">Eventos finalizados</h2>
          <p className="mt-4 text-5xl font-bold text-emerald-700">{marketing?.resumen_ventas.cantidad_ventas ?? 0}</p>
          <p className="mt-2 text-sm text-slate-500">Proyectos contabilizados como ventas cerradas.</p>
        </section>
      </div>
    </div>
  );
}
