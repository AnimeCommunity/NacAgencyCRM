'use client';
import { useEffect, useState } from 'react';
import { apiService } from '@/services/api';

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_proyectos: 0,
    proyectos_en_proceso: 0,
    ingresos_estimados: 0,
    cotizaciones_pendientes: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDashboardStats() {
      try {
        // informes desde django
        const dataReporte = await apiService.reportes.getInformeGerencial();
        const dataMarketing = await apiService.marketing.getStats();

        setStats({
          total_proyectos: dataReporte?.resumen_conversion?.total || 0,
          proyectos_en_proceso: dataMarketing?.resumen_ventas?.cantidad_ventas || 0,
          ingresos_estimados: parseFloat(dataMarketing?.resumen_ventas?.total_ingresos || 0),
          cotizaciones_pendientes: dataReporte?.resumen_conversion?.pendientes || 0
        });
      } catch (err) {
        console.error("Error mapeando data real del dashboard:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDashboardStats();
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-gray-500 font-medium">Cargando estadisticas del sistema de eventos...</div>;
  }

  return (
    <div>
      <header className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-slate-800">Panel de Control</h2>
        <p className="text-gray-500">Bienvenido al sistema de gestión de eventos.</p>
      </header>

      {/* data de django*/}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500 uppercase">Total Cotizaciones/Proyectos</p>
          <p className="text-3xl font-bold mt-2 text-slate-800">{stats.total_proyectos}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500 uppercase">Cierres Exitosos</p>
          <p className="text-3xl font-bold mt-2 text-blue-600">{stats.proyectos_en_proceso}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500 uppercase">Ingresos Reales</p>
          <p className="text-3xl font-bold mt-2 text-green-600">${stats.ingresos_estimados.toLocaleString(undefined, {minimumFractionDigits: 2})}</p>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <p className="text-sm font-medium text-gray-500 uppercase">Por Evaluar</p>
          <p className="text-3xl font-bold mt-2 text-yellow-600">{stats.cotizaciones_pendientes}</p>
        </div>
      </div>
    </div>
  );
}