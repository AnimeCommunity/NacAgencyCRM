'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  Project,
  Quotation,
  QuotationItemInput,
  apiService,
  getErrorMessage,
  getSessionClaims,
} from '@/services/api';
import { downloadBlob } from '@/services/download';

interface DraftItem extends QuotationItemInput {
  key: number;
}

export default function CotizacionesPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [projectId, setProjectId] = useState('');
  const [expirationDate, setExpirationDate] = useState('');
  const [notes, setNotes] = useState('');
  const [items, setItems] = useState<DraftItem[]>([]);
  const [itemDescription, setItemDescription] = useState('');
  const [itemQuantity, setItemQuantity] = useState(1);
  const [itemPrice, setItemPrice] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const role = getSessionClaims()?.role;
  const canCreate = role === 'admin' || role === 'sales';
  const today = useMemo(() => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
  }, []);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [projectData, quotationData] = await Promise.all([
          apiService.proyectos.getAll(),
          apiService.cotizaciones.getAll(),
        ]);
        if (active) {
          setProjects(projectData);
          setQuotations(quotationData);
        }
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar las cotizaciones.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const preview = useMemo(() => {
    const subtotal = items.reduce((sum, item) => sum + item.cantidad * item.precio_unitario, 0);
    const taxes = subtotal * 0.19;
    return { subtotal, taxes, total: subtotal + taxes };
  }, [items]);

  const projectNames = useMemo(
    () => new Map(projects.map((project) => [project.id, project.nombre])),
    [projects],
  );

  const addItem = () => {
    const price = Number(itemPrice);
    if (!itemDescription.trim() || itemQuantity <= 0 || price <= 0) {
      setError('Completa la descripción, cantidad y precio del ítem.');
      return;
    }
    setItems((current) => [
      ...current,
      { key: Date.now(), descripcion: itemDescription.trim(), cantidad: itemQuantity, precio_unitario: price },
    ]);
    setItemDescription('');
    setItemQuantity(1);
    setItemPrice('');
    setError('');
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (items.length === 0) {
      setError('Agrega al menos un ítem a la cotización.');
      return;
    }

    setSaving(true);
    setError('');
    setNotice('');
    try {
      const created = await apiService.cotizaciones.create({
        projecto: Number(projectId),
        estado: 'enviada',
        fecha_vencimiento: expirationDate,
        notas: notes,
        items: items.map(({ descripcion, cantidad, precio_unitario }) => ({
          descripcion,
          cantidad,
          precio_unitario,
        })),
      });
      setQuotations((current) => [created, ...current]);
      setProjectId('');
      setExpirationDate('');
      setNotes('');
      setItems([]);
      setNotice(`Cotización ${created.numero} creada. El servidor calculó un total de $${Number(created.total).toLocaleString('es', { minimumFractionDigits: 2 })}.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible crear la cotización.'));
    } finally {
      setSaving(false);
    }
  };

  const changeStatus = async (quotation: Quotation, estado: Quotation['estado']) => {
    setUpdatingId(quotation.id);
    setError('');
    setNotice('');
    try {
      const updated = await apiService.cotizaciones.update(quotation.id, { estado });
      setQuotations((current) =>
        current.map((entry) => (entry.id === updated.id ? updated : entry)),
      );
      setNotice(`Cotización ${updated.numero} actualizada a ${updated.estado}.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible actualizar la cotización.'));
    } finally {
      setUpdatingId(null);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    setError('');
    try {
      const blob = await apiService.cotizaciones.exportExcel();
      downloadBlob(blob, 'historial_cotizaciones.xlsx');
      setNotice('Historial de cotizaciones descargado.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible descargar las cotizaciones.'));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Cotizaciones</h1>
          <p className="mt-1 text-sm text-slate-500">Los importes definitivos se calculan y validan en el servidor.</p>
        </div>
        {canCreate && <button type="button" onClick={handleExport} disabled={exporting} className="rounded-lg border border-emerald-300 px-4 py-2.5 text-sm font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-50">
          {exporting ? 'Descargando…' : 'Descargar historial XLSX'}
        </button>}
      </header>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(20rem,0.9fr)_minmax(0,2fr)]">
        <form onSubmit={handleSubmit} className="h-fit space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="quotation-form-title">
          <h2 id="quotation-form-title" className="text-lg font-semibold text-slate-800">Nueva cotización</h2>
          {!canCreate && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">El rol de producción tiene acceso de solo lectura.</p>}
          <div>
            <label htmlFor="quotation-project" className="block text-sm font-medium text-slate-700">Proyecto</label>
            <select id="quotation-project" required disabled={!canCreate} value={projectId} onChange={(event) => setProjectId(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
              <option value="">Selecciona un proyecto</option>
              {projects.map((project) => <option key={project.id} value={project.id}>{project.nombre}</option>)}
            </select>
          </div>
          <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-800">
            El consecutivo se asignará automáticamente al guardar la cotización.
          </div>
          <div>
            <label htmlFor="quotation-expiration" className="block text-sm font-medium text-slate-700">Vencimiento</label>
            <input id="quotation-expiration" type="date" min={today} required disabled={!canCreate} value={expirationDate} onChange={(event) => setExpirationDate(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <div>
            <label htmlFor="quotation-notes" className="block text-sm font-medium text-slate-700">Notas</label>
            <textarea id="quotation-notes" rows={2} disabled={!canCreate} value={notes} onChange={(event) => setNotes(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>

          <fieldset className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-4" disabled={!canCreate}>
            <legend className="px-1 text-sm font-semibold text-slate-700">Agregar servicio</legend>
            <div>
              <label htmlFor="item-description" className="block text-xs font-medium text-slate-600">Descripción</label>
              <input id="item-description" value={itemDescription} onChange={(event) => setItemDescription(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="item-quantity" className="block text-xs font-medium text-slate-600">Cantidad</label>
                <input id="item-quantity" type="number" min={1} value={itemQuantity} onChange={(event) => setItemQuantity(Number(event.target.value))} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
              </div>
              <div>
                <label htmlFor="item-price" className="block text-xs font-medium text-slate-600">Precio unitario</label>
                <input id="item-price" type="number" min="0.01" step="0.01" value={itemPrice} onChange={(event) => setItemPrice(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm" />
              </div>
            </div>
            <button type="button" onClick={addItem} className="w-full rounded-lg bg-slate-700 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-800">Añadir ítem</button>
          </fieldset>

          <div className="space-y-1 border-t border-slate-200 pt-4 text-sm">
            <div className="flex justify-between"><span>Subtotal estimado</span><span>${preview.subtotal.toFixed(2)}</span></div>
            <div className="flex justify-between"><span>Impuestos estimados (19%)</span><span>${preview.taxes.toFixed(2)}</span></div>
            <div className="flex justify-between text-base font-bold text-indigo-700"><span>Total estimado</span><span>${preview.total.toFixed(2)}</span></div>
            <p className="pt-2 text-xs text-slate-500">Vista previa local. Estos valores no se envían y el servidor devuelve los importes oficiales.</p>
          </div>
          <button type="submit" disabled={saving || !canCreate} className="w-full rounded-lg bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800 disabled:bg-slate-400">
            {saving ? 'Creando…' : 'Emitir cotización'}
          </button>
        </form>

        <div className="min-w-0 space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="draft-items-title">
            <h2 id="draft-items-title" className="font-semibold text-slate-800">Ítems preparados ({items.length})</h2>
            {items.length === 0 ? <p className="mt-4 text-sm text-slate-500">Todavía no agregaste servicios.</p> : (
              <ul className="mt-3 divide-y divide-slate-100">
                {items.map((item) => (
                  <li key={item.key} className="flex items-center justify-between gap-4 py-3 text-sm">
                    <span><strong>{item.cantidad}×</strong> {item.descripcion}</span>
                    <div className="flex items-center gap-3"><span className="font-mono text-slate-600">${(item.cantidad * item.precio_unitario).toFixed(2)}</span><button type="button" onClick={() => setItems((current) => current.filter((entry) => entry.key !== item.key))} className="text-xs font-semibold text-red-600 hover:underline">Quitar</button></div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="quotation-history-title">
            <div className="border-b border-slate-200 p-4"><h2 id="quotation-history-title" className="font-semibold text-slate-800">Historial de cotizaciones</h2></div>
            {loading ? <p className="p-8 text-center text-sm text-slate-500">Cargando cotizaciones…</p> : quotations.length === 0 ? <p className="p-8 text-center text-sm text-slate-500">No hay cotizaciones registradas.</p> : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-sm">
                  <caption className="sr-only">Historial de cotizaciones</caption>
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Número</th><th className="p-3">Proyecto</th><th className="p-3">Fecha</th><th className="p-3">Total servidor</th><th className="p-3">Estado</th><th className="p-3 text-right">Acciones</th></tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {quotations.map((quotation) => (
                      <tr key={quotation.id}>
                        <td className="p-3 font-mono font-semibold text-slate-800">{quotation.numero}</td>
                        <td className="p-3 text-slate-600">{projectNames.get(quotation.projecto) || `Proyecto #${quotation.projecto}`}</td>
                        <td className="p-3 text-slate-600">{quotation.created_at}</td>
                        <td className="p-3 font-semibold text-slate-900">${Number(quotation.total).toLocaleString('es', { minimumFractionDigits: 2 })}</td>
                        <td className="p-3"><span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold uppercase text-amber-800">{quotation.estado}</span></td>
                        <td className="p-3">
                          {canCreate ? (
                            <div className="flex justify-end gap-2">
                              <button type="button" disabled={updatingId === quotation.id || quotation.estado === 'aceptada'} onClick={() => changeStatus(quotation, 'aceptada')} className="rounded-md border border-emerald-200 px-2.5 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-40">Aceptar</button>
                              <button type="button" disabled={updatingId === quotation.id || quotation.estado === 'rechazada'} onClick={() => changeStatus(quotation, 'rechazada')} className="rounded-md border border-red-200 px-2.5 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-40">Rechazar</button>
                              <button type="button" disabled={updatingId === quotation.id || quotation.estado === 'vencida'} onClick={() => changeStatus(quotation, 'vencida')} className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40">Vencida</button>
                            </div>
                          ) : <span className="block text-right text-xs text-slate-400">Solo lectura</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
