'use client';
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface Cliente {
  id: number;
  nombre: string;
}

interface Proyecto {
  id?: number;
  nombre: string;
  descripcion: string;
  tipo_evento: string;
  fecha_inicio: string;
  fecha_fin: string;
  presupuesto_estimado: number;
  estado: string;
  cliente: any; 
  responsable?: any;
}

export default function ProyectosPage() {
  const [proyectos, setProyectos] = useState<Proyecto[]>([]);
  const [clientes, setClientes] = useState<Cliente[]>([]);
  
  const [nuevoProyecto, setNuevoProyecto] = useState({
    nombre: '',
    descripcion: '', 
    tipo_evento: 'otro',
    fecha_inicio: '',
    fecha_fin: '',
    presupuesto_estimado: '',
    estado: 'propuesta',
    cliente: '', 
    responsable: '1' 
  });

  const fetchData = async () => {
    try {
      // apiService
      const dataProj = await apiService.proyectos.getAll();
      setProyectos(dataProj);

      const dataCli = await apiService.clientes.getAll();
      setClientes(dataCli);
    } catch (err) {
      console.error("Error cargando datos en proyectos:", err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.proyectos.create({
        ...nuevoProyecto,
        cliente: parseInt(nuevoProyecto.cliente),
        responsable: parseInt(nuevoProyecto.responsable),
        presupuesto_estimado: parseFloat(nuevoProyecto.presupuesto_estimado)
      });
      
      fetchData(); // Recargar la tabla
      
      
      setNuevoProyecto({
        nombre: '', descripcion: '', tipo_evento: 'otro',
        fecha_inicio: '', fecha_fin: '', presupuesto_estimado: '',
        estado: 'propuesta', cliente: '', responsable: '1'
      });
    } catch (err) {
      console.error("Error al crear el proyecto:", err);
    }
  };

  return (
    <div className="space-y-8 p-2">
      <div>
        <h2 className="text-3xl font-bold text-slate-800">Gestión de Proyectos / Eventos</h2>
        <p className="text-gray-500">Planifica eventos, presupuestos y asigna clientes.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* form */}
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border space-y-4 h-fit">
          <h3 className="text-lg font-semibold text-slate-700">Crear Nuevo Proyecto</h3>
          
          <div>
            <label className="block text-sm font-medium text-gray-700">Cliente Asociado</label>
            <select required value={nuevoProyecto.cliente} onChange={e => setNuevoProyecto({...nuevoProyecto, cliente: e.target.value})} className="mt-1 block w-full p-2 border rounded-md bg-white">
              <option value="">-- Selecciona un Cliente --</option>
              {clientes.map(c => (
                <option key={c.id} value={c.id}>{c.nombre}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Nombre del Evento</label>
            <input type="text" required value={nuevoProyecto.nombre} onChange={e => setNuevoProyecto({...nuevoProyecto, nombre: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Descripción</label>
            <textarea required value={nuevoProyecto.descripcion} onChange={e => setNuevoProyecto({...nuevoProyecto, descripcion: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" rows={2} />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Tipo Evento</label>
              <select value={nuevoProyecto.tipo_evento} onChange={e => setNuevoProyecto({...nuevoProyecto, tipo_evento: e.target.value})} className="mt-1 block w-full p-2 border rounded-md bg-white">
                <option value="concierto">Concierto</option>
                <option value="show">Show</option>
                <option value="streaming">Streaming</option>
                <option value="fiesta">Fiesta</option>
                <option value="otro">Otro</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Presupuesto ($)</label>
              <input type="number" required value={nuevoProyecto.presupuesto_estimado} onChange={e => setNuevoProyecto({...nuevoProyecto, presupuesto_estimado: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Fecha Inicio</label>
              <input type="date" required value={nuevoProyecto.fecha_inicio} onChange={e => setNuevoProyecto({...nuevoProyecto, fecha_inicio: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Fecha Fin</label>
              <input type="date" required value={nuevoProyecto.fecha_fin} onChange={e => setNuevoProyecto({...nuevoProyecto, fecha_fin: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
            </div>
          </div>

          <button type="submit" className="w-full bg-indigo-600 text-white p-2 rounded-md hover:bg-indigo-700 transition">
            Crear Proyecto
          </button>
        </form>

        {/* tbl proyectos */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4 font-semibold text-gray-600">Proyecto</th>
                <th className="p-4 font-semibold text-gray-600">Cliente</th>
                <th className="p-4 font-semibold text-gray-600">Fechas</th>
                <th className="p-4 font-semibold text-gray-600">Presupuesto</th>
                <th className="p-4 font-semibold text-gray-600">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {proyectos.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50">
                  <td className="p-4">
                    <div className="font-medium text-slate-800">{p.nombre}</div>
                    <div className="text-xs text-gray-400 capitalize">{p.tipo_evento}</div>
                  </td>
                  <td className="p-4 text-gray-600">{p.cliente?.nombre || `Cliente ID: ${p.cliente}`}</td>
                  <td className="p-4 text-xs text-gray-600">{p.fecha_inicio} al {p.fecha_fin}</td>
                  <td className="p-4 font-medium text-green-600">${Number(p.presupuesto_estimado).toFixed(2)}</td>
                  <td className="p-4">
                    <span className="px-2 py-1 text-xs rounded-full font-semibold bg-blue-100 text-blue-800 capitalize">
                      {p.estado.replace('_', ' ')}
                    </span>
                  </td>
                </tr>
              ))}
              {proyectos.length === 0 && (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-gray-400">No hay proyectos activos.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}