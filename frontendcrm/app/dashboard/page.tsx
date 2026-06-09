'use client';
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

export default function DashboardReportesPage() {
  const [reporteFinanciero, setReporteFinanciero] = useState<any>(null);
  const [statsMarketing, setStatsMarketing] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function cargarAnaliticas() {
      try {
        const finData = await apiService.reportes.getInformeGerencial();
        const mktData = await apiService.marketing.getStats();
        setReporteFinanciero(finData);
        setStatsMarketing(mktData);
      } catch (err) {
        console.error("Error cargando métricas en tiempo real", err);
      } finally {
        setLoading(false);
      }
    }
    cargarAnaliticas();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500 font-medium">Calculando métricas del CRM y cargando indicadores gerenciales...</div>;

  return (
    <div className="space-y-8 p-6">
      <div>
        <h2 className="text-3xl font-bold text-slate-800">Panel de Inteligencia de Negocios (BI)</h2>
        <p className="text-gray-500">Métricas analíticas calculadas directamente desde el motor ORM de Django.</p>
      </div>

      {/* metricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-indigo-600 to-indigo-700 text-white p-6 rounded-xl shadow-sm">
          <span className="text-indigo-100 text-xs font-bold uppercase tracking-wider">Tasa de Conversión</span>
          <div className="text-4xl font-extrabold mt-2">{reporteFinanciero?.resumen_conversion?.tasa_exito_porcentaje}%</div>
          <p className="text-indigo-200 text-xs mt-2">{reporteFinanciero?.resumen_conversion?.aceptadas} de {reporteFinanciero?.resumen_conversion?.total} cotizaciones aprobadas.</p>
        </div>

        <div className="bg-white border p-6 rounded-xl shadow-sm">
          <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Ingresos por Cierre de Eventos</span>
          <div className="text-4xl font-extrabold mt-2 text-green-600">${parseFloat(statsMarketing?.resumen_ventas?.total_ingresos || 0).toLocaleString()}</div>
          <p className="text-gray-500 text-xs mt-2">{statsMarketing?.resumen_ventas?.cantidad_ventas} proyectos ejecutados con éxito.</p>
        </div>

        <div className="bg-white border p-6 rounded-xl shadow-sm">
          <span className="text-gray-400 text-xs font-bold uppercase tracking-wider">Clientes Top Valorados</span>
          <div className="mt-2 space-y-1">
            {reporteFinanciero?.top_5_clientes?.map((cli: any, idx: number) => (
              <div key={idx} className="flex justify-between text-xs text-slate-700">
                <span className="font-medium">{cli.nombre}</span>
                <span className="font-bold text-slate-900">${parseFloat(cli.total_invertido).toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* rendimiento x tipo de eeventos y leads */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* eventos */}
        <div className="bg-white p-6 rounded-xl border shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Rentabilidad por Tipología de Evento</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b text-slate-400 text-xs uppercase"><th className="pb-2">Tipo de Evento</th><th className="pb-2 text-center">Proyectos</th><th className="pb-2 text-right">Monto Total</th></tr>
              </thead>
              <tbody className="divide-y">
                {reporteFinanciero?.ingresos_por_tipo_evento?.map((item: any, i: number) => (
                  <tr key={i} className="text-slate-700"><td className="py-2 capitalize font-medium">{item.tipo_evento}</td><td className="py-2 text-center">{item.cantidad_proyectos}</td><td className="py-2 text-right text-indigo-600 font-bold">${parseFloat(item.total_generado).toLocaleString()}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* cnl Marketing */}
        <div className="bg-white p-6 rounded-xl border shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-4">Efectividad de Canales (Captación de Clientes)</h3>
          <div className="space-y-4">
            {statsMarketing?.origenes?.map((orig: any, i: number) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-sm text-slate-600 capitalize">
                  <span>{orig.origen}</span>
                  <span className="font-bold">{orig.total} leads</span>
                </div>
                <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(orig.total / statsMarketing.origenes.reduce((a:any,b:any)=>a+b.total,0))*100}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}