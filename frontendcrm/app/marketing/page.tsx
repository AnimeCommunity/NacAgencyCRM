'use client';
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

export default function MarketingPage() {
  const [clientes, setClientes] = useState([]);
  const [plantillas, setPlantillas] = useState([]);
  
  // Estado para crear nueva plantilla
  const [nuevaPlantilla, setNuevaPlantilla] = useState({ nombre: '', tipo: 'email', asunto: '', contenido: '' });
  
  // Estado para la acción de enviar
  const [seleccion, setSeleccion] = useState({ clienteId: '', plantillaId: '' });
  const [loading, setLoading] = useState(false);

  const cargarDatos = async () => {
    try {
      const cls = await apiService.clientes.getAll();
      const tpls = await apiService.marketing.getTemplates();
      setClientes(cls);
      setPlantillas(tpls);
    } catch (err) {
      console.error("Error cargando datos de marketing", err);
    }
  };

  useEffect(() => { cargarDatos(); }, []);

  const handleCrearPlantilla = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.marketing.createTemplate(nuevaPlantilla);
      alert("¡Plantilla guardada con éxito!");
      setNuevaPlantilla({ nombre: '', tipo: 'email', asunto: '', contenido: '' });
      cargarDatos();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleEnviarCampana = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!seleccion.clienteId || !seleccion.plantillaId) return;
    
    setLoading(true);
    try {
      const res = await apiService.marketing.enviarCampana(
        parseInt(seleccion.clienteId),
        parseInt(seleccion.plantillaId)
      );

      
      if (res.url) {
        window.open(res.url, '_blank');
        alert("¡Enlace de WhatsApp generado e historial guardado!");
      } else {
        alert(res.status || "¡Correo enviado con éxito!");
      }
    } catch (err: any) {
      alert(`Error al procesar el envío: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold">Módulo de Automatización & Marketing</h2>
        <p className="text-gray-500">Diseña mensajes predeterminados y dispara campañas masivas o individuales.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* crear plantilla */}
        <form onSubmit={handleCrearPlantilla} className="bg-white p-6 rounded-xl shadow-sm border space-y-4">
          <h3 className="text-lg font-semibold border-b pb-2">Nueva Plantilla (Newsletter o Chat)</h3>
          <div>
            <label className="block text-sm font-medium text-gray-700">Nombre de la Plantilla</label>
            <input type="text" required placeholder="Ej: Recordatorio de Pago, Promo Mes" value={nuevaPlantilla.nombre} onChange={e => setNuevaPlantilla({...nuevaPlantilla, nombre: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Canal de Envío</label>
            <select value={nuevaPlantilla.tipo} onChange={e => setNuevaPlantilla({...nuevaPlantilla, tipo: e.target.value})} className="mt-1 block w-full p-2 border rounded-md bg-white">
              <option value="email">Correo Electrónico (SMTP)</option>
              <option value="whatsapp">Mensaje Directo de WhatsApp</option>
            </select>
          </div>
          {nuevaPlantilla.tipo === 'email' && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Asunto del Correo</label>
              <input type="text" required value={nuevaPlantilla.asunto} onChange={e => setNuevaPlantilla({...nuevaPlantilla, asunto: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700">Cuerpo del Mensaje</label>
            <p className="text-xs text-gray-400 mb-1">Usa {"{nombre}"} para personalizar dinámicamente.</p>
            <textarea required rows={4} value={nuevaPlantilla.contenido} onChange={e => setNuevaPlantilla({...nuevaPlantilla, contenido: e.target.value})} placeholder="Hola {nombre}, te escribimos de EventCRM..." className="block w-full p-2 border rounded-md" />
          </div>
          <button type="submit" className="w-full bg-indigo-600 text-white p-2 rounded-md hover:bg-indigo-700 transition">
            Guardar Plantilla
          </button>
        </form>

        {/* envios*/}
        <div className="space-y-6">
          <form onSubmit={handleEnviarCampana} className="bg-white p-6 rounded-xl shadow-sm border space-y-4">
            <h3 className="text-lg font-semibold border-b pb-2 text-green-600">Lanzador de Comunicaciones</h3>
            <div>
              <label className="block text-sm font-medium text-gray-700">Seleccionar Cliente Destinatario</label>
              <select required value={seleccion.clienteId} onChange={e => setSeleccion({...seleccion, clienteId: e.target.value})} className="mt-1 block w-full p-2 border rounded-md bg-white">
                <option value="">-- Selecciona un Cliente --</option>
                {clientes.map((c: any) => <option key={c.id} value={c.id}>{c.nombre} ({c.email})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Seleccionar Mensaje/Plantilla</label>
              <select required value={seleccion.plantillaId} onChange={e => setSeleccion({...seleccion, plantillaId: e.target.value})} className="mt-1 block w-full p-2 border rounded-md bg-white">
                <option value="">-- Selecciona una Plantilla --</option>
                {plantillas.map((t: any) => <option key={t.id} value={t.id}>{t.nombre} [{t.tipo_display}]</option>)}
              </select>
            </div>
            <button type="submit" disabled={loading} className="w-full bg-green-600 text-white p-3 rounded-md font-medium hover:bg-green-700 transition disabled:bg-gray-400">
              {loading ? 'Procesando Envío...' : 'Ejecutar Acción de Marketing'}
            </button>
          </form>

          {/* plantillas activas */}
          <div className="bg-white p-4 rounded-xl shadow-sm border">
            <h4 className="font-semibold text-gray-700 mb-2">Plantillas Activas</h4>
            <ul className="divide-y text-sm max-h-40 overflow-y-auto">
              {plantillas.map((t: any) => (
                <li key={t.id} className="py-2 flex justify-between items-center">
                  <span className="font-medium">{t.nombre}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${t.tipo === 'email' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>{t.tipo_display}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

      </div>
    </div>
  );
}