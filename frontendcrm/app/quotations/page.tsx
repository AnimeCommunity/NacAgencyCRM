'use client';
import { useState, useEffect } from 'react';

interface Proyecto {
  id: number;
  nombre: string;
}

interface ItemCotizacion {
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  total: number;
}

export default function CotizacionesPage() {
  const [proyectos, setProyectos] = useState<Proyecto[]>([]);
  const [cotizaciones, setCotizaciones] = useState<any[]>([]);

  // Campos del maestro
  const [projecto, setProjecto] = useState('');
  const [numero, setNumero] = useState('');
  const [fechaVencimiento, setFechaVencimiento] = useState('');
  const [notas, setNotas] = useState('');

  // Items de la cotización (Detalle)
  const [items, setItems] = useState<ItemCotizacion[]>([]);
  const [itemDescripcion, setItemDescripcion] = useState('');
  const [itemCantidad, setItemCantidad] = useState(1);
  const [itemPrecio, setItemPrecio] = useState(0);

  const API_QUOTATIONS = 'http://localhost:8000/api/quotations/';
  const API_PROJECTS = 'http://localhost:8000/api/projects/';

  const loadData = async () => {
    try {
      const resProj = await fetch(API_PROJECTS);
      setProyectos(await resProj.json());

      const resQuot = await fetch(API_QUOTATIONS);
      setCotizaciones(await resQuot.json());
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { loadData(); }, []);

  // Agregar item temporal a la lista local
  const agregarItem = () => {
    if (!itemDescripcion || itemPrecio <= 0) return;
    const nuevoItem: ItemCotizacion = {
      descripcion: itemDescripcion,
      cantidad: itemCantidad,
      precio_unitario: itemPrecio,
      total: itemCantidad * itemPrecio
    };
    setItems([...items, nuevoItem]);
    setItemDescripcion('');
    setItemCantidad(1);
    setItemPrecio(0);
  };

  // Calcular totales consolidados
  const subtotal = items.reduce((acc, item) => acc + item.total, 0);
  const impuestos = subtotal * 0.19; // Ejemplo: IVA del 19%
  const totalGeneral = subtotal + impuestos;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (items.length === 0) {
      alert("Debes agregar al menos un ítem a la cotización.");
      return;
    }

    const payload = {
      projecto: parseInt(projecto),
      numero,
      subtotal: subtotal.toFixed(2),
      impuestos: impuestos.toFixed(2),
      total: totalGeneral.toFixed(2),
      estado: 'enviada',
      fecha_vencimiento: fechaVencimiento,
      notas,
      items: items
    };

    try {
      const res = await fetch(API_QUOTATIONS, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        alert("Cotización generada con éxito");
        loadData();
        // Reset al form
        setProjecto(''); setNumero(''); setFechaVencimiento(''); setNotas(''); setItems([]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold">Generador de Cotizaciones</h2>
        <p className="text-gray-500">Genera presupuestos detallados asociados a un proyecto de evento.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* detalle form */}
        <form onSubmit={handleSubmit} className="lg:col-span-1 bg-white p-6 rounded-xl shadow-sm border space-y-4 h-fit">
          <h3 className="text-lg font-semibold border-b pb-2">Encabezado</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700">Proyecto</label>
            <select required value={projecto} onChange={e => setProjecto(e.target.value)} className="mt-1 block w-full p-2 border rounded-md bg-white">
              <option value="">-- Selecciona Proyecto --</option>
              {proyectos.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">N° Factura/Cotiz.</label>
              <input type="text" placeholder="COT-001" required value={numero} onChange={e => setNumero(e.target.value)} className="mt-1 block w-full p-2 border rounded-md" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Vencimiento</label>
              <input type="date" required value={fechaVencimiento} onChange={e => setFechaVencimiento(e.target.value)} className="mt-1 block w-full p-2 border rounded-md" />
            </div>
          </div>

          {/* agregar itms */}
          <h3 className="text-lg font-semibold border-b pt-4 pb-2">Agregar Línea de Detalle</h3>
          <div className="space-y-2 bg-gray-50 p-3 rounded-lg border">
            <div>
              <label className="text-xs font-medium text-gray-600">Descripción del Servicio</label>
              <input type="text" value={itemDescripcion} onChange={e => setItemDescripcion(e.target.value)} placeholder="Ej. Alquiler de Sonido Profesional" className="block w-full p-2 border rounded-md bg-white text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs font-medium text-gray-600">Cant.</label>
                <input type="number" min="1" value={itemCantidad} onChange={e => setItemCantidad(parseInt(e.target.value) || 1)} className="block w-full p-2 border rounded-md bg-white text-sm" />
              </div>
              <div>
                <label className="text-xs font-medium text-gray-600">Precio Unitario ($)</label>
                <input type="number" value={itemPrecio} onChange={e => setItemPrecio(parseFloat(e.target.value) || 0)} className="block w-full p-2 border rounded-md bg-white text-sm" />
              </div>
            </div>
            <button type="button" onClick={agregarItem} className="w-full mt-2 text-xs bg-slate-700 text-white p-2 rounded hover:bg-slate-800 transition">
              + Añadir Ítem a la Lista
            </button>
          </div>

          {/* totales */}
          <div className="pt-4 border-t space-y-1 text-sm">
            <div className="flex justify-between"><span>Subtotal:</span><span className="font-medium">${subtotal.toFixed(2)}</span></div>
            <div className="flex justify-between"><span>Impuestos (19%):</span><span className="font-medium">${impuestos.toFixed(2)}</span></div>
            <div className="flex justify-between text-base font-bold text-indigo-600"><span>TOTAL:</span><span>${totalGeneral.toFixed(2)}</span></div>
          </div>

          <button type="submit" className="w-full bg-green-600 text-white p-3 rounded-md font-medium hover:bg-green-700 transition">
            Emitir Cotización Completa
          </button>
        </form>

        {/* items agregados y cotizaciones */}
        <div className="lg:col-span-2 space-y-6">
          {/* Items actual */}
          <div className="bg-white p-4 rounded-xl shadow-sm border">
            <h3 className="font-semibold text-gray-700 mb-2">Items listos para enviar ({items.length})</h3>
            <ul className="divide-y text-sm">
              {items.map((item, index) => (
                <li key={index} className="py-2 flex justify-between">
                  <span>{item.cantidad}x {item.descripcion}</span>
                  <span className="font-mono text-gray-600">${item.total.toFixed(2)}</span>
                </li>
              ))}
              {items.length === 0 && <p className="text-gray-400 text-xs py-2">La lista está vacía.</p>}
            </ul>
          </div>

          {/* Historial */}
          <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
            <h3 className="font-semibold text-gray-700 p-4 bg-gray-50 border-b">Historial de Cotizaciones</h3>
            <table className="w-full text-left border-collapse text-sm">
              <thead className="bg-gray-100 text-gray-600">
                <tr>
                  <th className="p-3">Número</th>
                  <th className="p-3">Proyecto</th>
                  <th className="p-3">Total</th>
                  <th className="p-3">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {cotizaciones.map((c) => (
                  <tr key={c.id}>
                    <td className="p-3 font-mono font-bold">{c.numero}</td>
                    <td className="p-3 text-gray-600">Proyecto ID: {c.projecto}</td>
                    <td className="p-3 font-semibold text-gray-900">${parseFloat(c.total).toFixed(2)}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800 uppercase">
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
    </div>
  );
}