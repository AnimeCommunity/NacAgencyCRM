'use client';

import { useEffect, useMemo, useState } from 'react';
import { ManagementReport, MarketingStats, apiService, getErrorMessage } from '@/services/api';

export default function AnalyticsDashboardPage() {
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
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar las analíticas.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const totalOrigins = useMemo(
    () => marketing?.origenes.reduce((total, origin) => total + origin.total, 0) ?? 0,
    [marketing],
  );

  if (loading) return <p className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500" role="status">Calculando métricas gerenciales…</p>;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Inteligencia de negocios</h1>
        <p className="mt-1 text-sm text-slate-500">Indicadores calculados por el backend sobre datos reales del CRM.</p>
      </header>
      {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}

      <section className="grid gap-4 md:grid-cols-3" aria-label="Métricas de negocio">
        <article className="rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-800 p-6 text-white shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-indigo-100">Tasa de conversión</p><p className="mt-2 text-4xl font-bold">{report?.resumen_conversion.tasa_exito_porcentaje ?? 0}%</p><p className="mt-2 text-xs text-indigo-100">{report?.resumen_conversion.aceptadas ?? 0} de {report?.resumen_conversion.total ?? 0} cotizaciones.</p></article>
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ingresos finalizados</p><p className="mt-2 text-4xl font-bold text-emerald-700">${Number(marketing?.resumen_ventas.total_ingresos ?? 0).toLocaleString('es')}</p><p className="mt-2 text-xs text-slate-500">{marketing?.resumen_ventas.cantidad_ventas ?? 0} proyectos finalizados.</p></article>
        <article className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Clientes de mayor valor</p>{report?.top_5_clientes.length ? <ol className="mt-3 space-y-2">{report.top_5_clientes.map((client) => <li key={client.nombre} className="flex justify-between gap-3 text-sm"><span className="truncate text-slate-700">{client.nombre}</span><strong>${Number(client.total_invertido).toLocaleString('es')}</strong></li>)}</ol> : <p className="mt-4 text-sm text-slate-500">Sin cierres aceptados todavía.</p>}</article>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="event-profit-title">
          <div className="border-b border-slate-200 p-4"><h2 id="event-profit-title" className="font-semibold text-slate-800">Ingresos por tipo de evento</h2></div>
          {report?.ingresos_por_tipo_evento.length ? <div className="overflow-x-auto"><table className="w-full min-w-[480px] text-left text-sm"><caption className="sr-only">Ingresos y proyectos por tipo de evento</caption><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Tipo</th><th className="p-3 text-center">Proyectos</th><th className="p-3 text-right">Total</th></tr></thead><tbody className="divide-y divide-slate-100">{report.ingresos_por_tipo_evento.map((item) => <tr key={item.tipo_evento}><td className="p-3 capitalize">{item.tipo_evento.replaceAll('_', ' ')}</td><td className="p-3 text-center">{item.cantidad_proyectos}</td><td className="p-3 text-right font-semibold text-indigo-700">${Number(item.total_generado).toLocaleString('es')}</td></tr>)}</tbody></table></div> : <p className="p-8 text-center text-sm text-slate-500">No hay ingresos aceptados por tipo de evento.</p>}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="origins-title">
          <h2 id="origins-title" className="font-semibold text-slate-800">Origen de clientes</h2>
          {marketing?.origenes.length ? <ul className="mt-5 space-y-4">{marketing.origenes.map((origin) => { const percentage = totalOrigins ? (origin.total / totalOrigins) * 100 : 0; return <li key={origin.origen}><div className="mb-1 flex justify-between text-sm capitalize text-slate-600"><span>{origin.origen}</span><strong>{origin.total}</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100" aria-label={`${origin.origen}: ${percentage.toFixed(1)}%`}><div className="h-full rounded-full bg-emerald-500" style={{ width: `${percentage}%` }} /></div></li>; })}</ul> : <p className="mt-5 text-sm text-slate-500">No hay datos de captación.</p>}
        </section>
      </div>
    </div>
  );
}
