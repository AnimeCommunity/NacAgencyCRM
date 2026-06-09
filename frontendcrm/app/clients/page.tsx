'use client';
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface Cliente {
  id?: number;
  nombre: string;
  email: string;
  telefono: string;
  tipo: string;
  estado: string;
  origen: string;
}

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [nuevoCliente, setNuevoCliente] = useState({
    nombre: '', email: '', telefono: '', tipo: 'natural', estado: 'potencial', origen: 'web'
  });

  const fetchClientes = async () => {
    try {
      const data = await apiService.clientes.getAll();
      setClientes(data);
    } catch (err) {
      console.error("Error cargando clientes:", err);
    }
  };

  useEffect(() => { fetchClientes(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.clientes.create(nuevoCliente);
      fetchClientes();
      setNuevoCliente({ nombre: '', email: '', telefono: '', tipo: 'natural', estado: 'potencial', origen: 'web' });
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Gestión de Clientes</h2>
          <p className="text-gray-500">Administra la base de datos de contactos corporativos y naturales.</p>
        </div>
        {/* descargar reporte*/}
        <a 
          href={apiService.marketing.getExcelUrl()} 
          className="bg-green-700 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-800 transition shadow-sm text-sm"
        >
          Exportar Clientes (.xlsx)
        </a>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border space-y-4 h-fit">
          <h3 className="text-lg font-semibold text-slate-700">Registrar Cliente</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700">Nombre</label>
            <input type="text" required value={nuevoCliente.nombre} onChange={e => setNuevoCliente({...nuevoCliente, nombre: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input type="email" required value={nuevoCliente.email} onChange={e => setNuevoCliente({...nuevoCliente, email: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Teléfono</label>
            <input type="text" value={nuevoCliente.telefono} onChange={e => setNuevoCliente({...nuevoCliente, telefono: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Canal de Origen</label>
            <select value={nuevoCliente.origen} onChange={e => setNuevoCliente({...nuevoCliente, origen: e.target.value})} className="mt-1 block w-full p-2 border rounded-md bg-white">
              <option value="web">Sitio Web</option>
              <option value="whatsapp">WhatsApp Directo</option>
              <option value="redes">Redes Sociales</option>
              <option value="referido">Referido</option>
            </select>
          </div>
          <button type="submit" className="w-full bg-indigo-600 text-white p-2 rounded-md hover:bg-indigo-700 transition">
            Guardar Cliente
          </button>
        </form>

        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="p-4 font-semibold text-gray-600">Nombre</th>
                <th className="p-4 font-semibold text-gray-600">Email</th>
                <th className="p-4 font-semibold text-gray-600">Origen</th>
                <th className="p-4 font-semibold text-gray-600">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {clientes.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="p-4 font-medium">{c.nombre}</td>
                  <td className="p-4 text-gray-600">{c.email}</td>
                  <td className="p-4 capitalize text-xs text-slate-500">{c.origen}</td>
                  <td className="p-4">
                    <span className={`px-2 py-1 text-xs rounded-full font-semibold ${
                      c.estado === 'activo' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {c.estado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}