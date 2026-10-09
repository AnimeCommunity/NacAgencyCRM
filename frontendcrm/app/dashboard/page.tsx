'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  InteractionOutcome,
  ManagementReport,
  ReportFilters,
  apiService,
  getErrorMessage,
  getSessionClaims,
} from '@/services/api';
import { downloadBlob } from '@/services/download';

const outcomeLabels: Record<InteractionOutcome, string> = {
  sin_definir: 'Sin definir',
  contactado: 'Contactado',
  sin_respuesta: 'Sin respuesta',
  interesado: 'Interesado',
  no_interesado: 'No interesado',
  reunion_agendada: 'Reunión agendada',
  cerrado: 'Cierre concretado',
};

const currency = (value: string | number) =>
  Number(value).toLocaleString('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  });

export default function AnalyticsDashboardPage() {
  const [report, setReport] = useState<ManagementReport | null>(null);
  const [filters, setFilters] = useState<ReportFilters>({});
  const [draftFilters, setDraftFilters] = useState<ReportFilters>({});
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const role = getSessionClaims()?.role;
  const canExport = role === 'admin' || role === 'sales';

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const data = await apiService.reportes.getInformeGerencial(filters);
        if (active) setReport(data);
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar las analíticas.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [filters]);

  const applyFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setNotice('');
    setFilters(draftFilters);
  };

  const clearFilters = () => {
    setDraftFilters({});
    setLoading(true);
    setError('');
    setFilters({});
    setNotice('Filtros restablecidos.');
  };

  const exportReport = async () => {
    setExporting(true);
    setError('');
    setNotice('');
    try {
      const blob = await apiService.reportes.exportInformeGerencial(filters);
      downloadBlob(blob, 'informe_gerencial_crm.xlsx');
      setNotice('Informe gerencial XLSX descargado.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible descargar el informe.'));
    } finally {
      setExporting(false);
    }
  };

  const latestActivity = report?.actividad_mensual.at(-1);
  const maxInteractions = useMemo(
    () => Math.max(1, ...(report?.interacciones_por_resultado.map((row) => row.total) ?? [1])),
    [report],
  );

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Inteligencia de negocios</h1>
          <p className="mt-1 text-sm text-slate-500">Seguimiento de clientes, proyectos, cotizaciones, pagos e interacciones.</p>
        </div>
        {canExport && <button type="button" onClick={exportReport} disabled={exporting || loading} className="rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 disabled:bg-slate-400">
          {exporting ? 'Preparando informe…' : 'Descargar informe XLSX'}
        </button>}
      </header>

      <form onSubmit={applyFilters} className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-2 lg:grid-cols-[1fr_1fr_auto_auto] lg:items-end">
        <div>
          <label htmlFor="report-from" className="block text-sm font-medium text-slate-700">Desde</label>
          <input id="report-from" type="date" value={draftFilters.desde ?? ''} onChange={(event) => setDraftFilters((current) => ({ ...current, desde: event.target.value || undefined }))} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </div>
        <div>
          <label htmlFor="report-to" className="block text-sm font-medium text-slate-700">Hasta</label>
          <input id="report-to" type="date" value={draftFilters.hasta ?? ''} onChange={(event) => setDraftFilters((current) => ({ ...current, hasta: event.target.value || undefined }))} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
        </div>
        <button type="submit" disabled={loading} className="rounded-lg bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-400">Aplicar</button>
        <button type="button" onClick={clearFilters} disabled={loading} className="rounded-lg border border-slate-300 px-4 py-2 font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">Limpiar</button>
      </form>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
      </div>

      {loading ? (
        <p className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500" role="status">Calculando métricas gerenciales…</p>
      ) : report && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Indicadores principales">
            <article className="rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-800 p-5 text-white shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-indigo-100">Conversión de cotizaciones</p>
              <p className="mt-2 text-4xl font-bold">{report.resumen_conversion.tasa_exito_porcentaje}%</p>
              <p className="mt-2 text-xs text-indigo-100">{report.resumen_conversion.aceptadas} de {report.resumen_conversion.total} aceptadas.</p>
            </article>
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ingresos aceptados</p>
              <p className="mt-2 text-3xl font-bold text-emerald-700">{currency(report.resumen_financiero.ingresos_aceptados)}</p>
              <p className="mt-2 text-xs text-slate-500">Valor de cotizaciones aceptadas.</p>
            </article>
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Ingresos pagados</p>
              <p className="mt-2 text-3xl font-bold text-emerald-700">{currency(report.resumen_financiero.ingresos_pagados)}</p>
              <p className="mt-2 text-xs text-slate-500">Saldo por cobrar: {currency(report.resumen_financiero.saldo_por_cobrar)}.</p>
            </article>
            <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Interacciones del último periodo</p>
              <p className="mt-2 text-4xl font-bold text-violet-700">{latestActivity?.interacciones ?? 0}</p>
              <p className="mt-2 text-xs text-slate-500">Periodo {latestActivity?.periodo ?? 'sin actividad'}.</p>
            </article>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="pipeline-title">
            <h2 id="pipeline-title" className="font-semibold text-slate-800">Embudo comercial de clientes</h2>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ['Clientes registrados', report.clientes_conversion.total_clientes, '100%'],
                ['Cotizaron', report.clientes_conversion.clientes_que_cotizaron, `${report.clientes_conversion.tasa_cliente_a_cotizacion}%`],
                ['Concretaron', report.clientes_conversion.clientes_que_concretaron, `${report.clientes_conversion.tasa_cotizacion_a_cierre}%`],
                ['Pagaron', report.clientes_conversion.clientes_que_pagaron, `${report.clientes_conversion.tasa_cierre_a_pago}%`],
              ].map(([label, value, rate]) => (
                <article key={String(label)} className="rounded-lg bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
                  <div className="mt-2 flex items-end justify-between gap-3"><strong className="text-3xl text-slate-900">{value}</strong><span className="text-sm font-semibold text-indigo-700">{rate}</span></div>
                </article>
              ))}
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-2">
            <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="monthly-title">
              <div className="border-b border-slate-200 p-4"><h2 id="monthly-title" className="font-semibold text-slate-800">Actividad comercial por mes</h2></div>
              {report.actividad_mensual.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[620px] text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Periodo</th><th className="p-3 text-center">Proyectos</th><th className="p-3 text-center">Cotizaciones</th><th className="p-3 text-center">Interacciones</th><th className="p-3 text-right">Ingresos</th></tr></thead>
                    <tbody className="divide-y divide-slate-100">{report.actividad_mensual.map((row) => <tr key={row.periodo}><td className="p-3 font-semibold">{row.periodo}</td><td className="p-3 text-center">{row.proyectos}</td><td className="p-3 text-center">{row.cotizaciones}</td><td className="p-3 text-center">{row.interacciones}</td><td className="p-3 text-right font-semibold text-emerald-700">{currency(row.ingresos_aceptados)}</td></tr>)}</tbody>
                  </table>
                </div>
              ) : <p className="p-8 text-center text-sm text-slate-500">No hay actividad en el periodo seleccionado.</p>}
            </section>

            <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="weekly-title">
              <div className="border-b border-slate-200 p-4"><h2 id="weekly-title" className="font-semibold text-slate-800">Actividad comercial por semana</h2></div>
              {report.actividad_semanal.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[620px] text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Semana</th><th className="p-3 text-center">Proyectos</th><th className="p-3 text-center">Cotizaciones</th><th className="p-3 text-center">Interacciones</th><th className="p-3 text-right">Ingresos</th></tr></thead>
                    <tbody className="divide-y divide-slate-100">{report.actividad_semanal.map((row) => <tr key={row.periodo}><td className="p-3 font-semibold">{row.periodo}</td><td className="p-3 text-center">{row.proyectos}</td><td className="p-3 text-center">{row.cotizaciones}</td><td className="p-3 text-center">{row.interacciones}</td><td className="p-3 text-right font-semibold text-emerald-700">{currency(row.ingresos_aceptados)}</td></tr>)}</tbody>
                  </table>
                </div>
              ) : <p className="p-8 text-center text-sm text-slate-500">No hay actividad semanal en el periodo seleccionado.</p>}
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="outcome-title">
              <h2 id="outcome-title" className="font-semibold text-slate-800">Resultados de interacciones</h2>
              {report.interacciones_por_resultado.length ? (
                <ul className="mt-5 space-y-4">{report.interacciones_por_resultado.map((row) => <li key={row.resultado}><div className="mb-1 flex justify-between text-sm text-slate-600"><span>{outcomeLabels[row.resultado]}</span><strong>{row.total}</strong></div><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-violet-500" style={{ width: `${(row.total / maxInteractions) * 100}%` }} /></div></li>)}</ul>
              ) : <p className="mt-5 text-sm text-slate-500">No hay interacciones registradas.</p>}
            </section>
          </div>

          <div className="grid gap-6 xl:grid-cols-3">
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="client-status-title">
              <h2 id="client-status-title" className="font-semibold text-slate-800">Clientes por estado</h2>
              <div className="mt-4 grid grid-cols-2 gap-3">{report.clientes_por_estado.map((row) => <article key={row.estado} className="rounded-lg bg-slate-50 p-4"><p className="text-sm capitalize text-slate-600">{row.estado.replaceAll('_', ' ')}</p><strong className="mt-1 block text-2xl text-slate-900">{row.total}</strong></article>)}</div>
            </section>
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="quotation-status-title">
              <h2 id="quotation-status-title" className="font-semibold text-slate-800">Cotizaciones por estado</h2>
              <div className="mt-4 grid grid-cols-2 gap-3">{report.cotizaciones_por_estado.map((row) => <article key={row.estado} className="rounded-lg bg-slate-50 p-4"><p className="text-sm capitalize text-slate-600">{row.estado}</p><strong className="mt-1 block text-2xl text-slate-900">{row.total}</strong></article>)}</div>
            </section>
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="project-status-title">
              <h2 id="project-status-title" className="font-semibold text-slate-800">Proyectos por estado</h2>
              <div className="mt-4 grid grid-cols-2 gap-3">{report.proyectos_por_estado.map((row) => <article key={row.estado} className="rounded-lg bg-slate-50 p-4"><p className="text-sm capitalize text-slate-600">{row.estado.replaceAll('_', ' ')}</p><strong className="mt-1 block text-2xl text-slate-900">{row.total}</strong></article>)}</div>
            </section>
          </div>

          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="client-project-title">
            <div className="border-b border-slate-200 p-4"><h2 id="client-project-title" className="font-semibold text-slate-800">Clientes asociados a proyectos</h2></div>
            {report.clientes_por_proyecto.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[700px] text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Cliente</th><th className="p-3">Proyecto</th><th className="p-3">Estado</th><th className="p-3 text-center">Cotizaciones</th><th className="p-3 text-center">Aceptadas</th><th className="p-3">Pago</th></tr></thead>
                  <tbody className="divide-y divide-slate-100">{report.clientes_por_proyecto.map((row) => <tr key={row.proyecto_id}><td className="p-3 font-semibold text-slate-800">{row.cliente_nombre}</td><td className="p-3 text-slate-600">{row.proyecto_nombre}</td><td className="p-3 capitalize text-slate-600">{row.estado.replaceAll('_', ' ')}</td><td className="p-3 text-center">{row.cotizaciones}</td><td className="p-3 text-center">{row.cotizaciones_aceptadas}</td><td className="p-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${row.pagado ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>{row.pagado ? 'Pagado' : 'Pendiente'}</span></td></tr>)}</tbody>
                </table>
              </div>
            ) : <p className="p-8 text-center text-sm text-slate-500">No hay proyectos para el periodo seleccionado.</p>}
          </section>
        </>
      )}
    </div>
  );
}