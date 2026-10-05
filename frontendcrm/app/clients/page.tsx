'use client';

import { FormEvent, useEffect, useState } from 'react';
import {
  ApiError,
  Client,
  ClientInput,
  Interaction,
  InteractionType,
  apiService,
  getErrorMessage,
  getSessionClaims,
} from '@/services/api';

const emptyClient: ClientInput = {
  nombre: '',
  email: '',
  telefono: '',
  tipo: 'natural',
  empresa: '',
  estado: 'potencial',
  ciudad: '',
  origen: 'web',
  notas: '',
};

const interactionLabels: Record<InteractionType, string> = {
  llamada: 'Llamada',
  correo_manual: 'Correo manual',
  reunión: 'Reunión',
  seguimiento: 'Seguimiento',
  email_marketing: 'Email de marketing',
  whatsapp_link: 'Enlace de WhatsApp',
};

export default function ClientesPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState<ClientInput>(emptyClient);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [interactionType, setInteractionType] = useState<InteractionType>('seguimiento');
  const [interactionDescription, setInteractionDescription] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const role = getSessionClaims()?.role;
  const canWriteClients = role === 'admin' || role === 'sales';
  const canDeleteClients = role === 'admin';
  const canExportClients = role === 'admin' || role === 'sales';

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const data = await apiService.clientes.getAll();
        if (active) setClients(data);
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar los clientes.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const resetForm = () => {
    setForm(emptyClient);
    setEditingId(null);
  };

  const handleSaveClient = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      if (editingId) {
        const updated = await apiService.clientes.update(editingId, form);
        setClients((current) => current.map((client) => (client.id === updated.id ? updated : client)));
        if (selectedClient?.id === updated.id) setSelectedClient(updated);
        setNotice('Cliente actualizado correctamente.');
      } else {
        const created = await apiService.clientes.create(form);
        setClients((current) => [created, ...current]);
        setNotice('Cliente creado correctamente.');
      }
      resetForm();
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar el cliente.'));
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (client: Client) => {
    setEditingId(client.id);
    setForm({
      nombre: client.nombre,
      email: client.email,
      telefono: client.telefono ?? '',
      tipo: client.tipo,
      empresa: client.empresa ?? '',
      estado: client.estado,
      ciudad: client.ciudad ?? '',
      origen: client.origen,
      notas: client.notas ?? '',
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const showHistory = async (client: Client) => {
    setSelectedClient(client);
    setHistoryLoading(true);
    setError('');
    try {
      const data = await apiService.interacciones.getAll(client.id);
      setInteractions(data);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible cargar el historial.'));
      setInteractions([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleCreateInteraction = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedClient) return;
    setSaving(true);
    setError('');
    try {
      const created = await apiService.interacciones.create({
        cliente: selectedClient.id,
        tipo: interactionType,
        descripcion: interactionDescription,
      });
      setInteractions((current) => [created, ...current]);
      setInteractionDescription('');
      setNotice('Interacción registrada.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible registrar la interacción.'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (client: Client) => {
    if (!window.confirm(`¿Eliminar a ${client.nombre}? Esta acción no se puede deshacer.`)) return;
    setError('');
    try {
      await apiService.clientes.remove(client.id);
      setClients((current) => current.filter((item) => item.id !== client.id));
      if (selectedClient?.id === client.id) {
        setSelectedClient(null);
        setInteractions([]);
      }
      setNotice('Cliente eliminado.');
    } catch (requestError) {
      const fallback = requestError instanceof ApiError && requestError.status === 403
        ? 'Tu rol no tiene permiso para eliminar clientes.'
        : 'No fue posible eliminar el cliente.';
      setError(getErrorMessage(requestError, fallback));
    }
  };

  const handleExport = async () => {
    setExporting(true);
    setError('');
    try {
      const blob = await apiService.clientes.exportExcel();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'reporte_clientes.xlsx';
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      setNotice('Reporte XLSX descargado.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible exportar el reporte.'));
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Gestión de clientes</h1>
          <p className="mt-1 text-sm text-slate-500">Administra contactos y consulta su historial de interacciones.</p>
        </div>
        {canExportClients && <button type="button" onClick={handleExport} disabled={exporting} className="rounded-lg bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800 disabled:bg-slate-400">
          {exporting ? 'Exportando…' : 'Exportar XLSX'}
        </button>}
      </header>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(18rem,0.8fr)_minmax(0,2fr)]">
        <form onSubmit={handleSaveClient} className="h-fit space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="client-form-title">
          <div className="flex items-center justify-between gap-3">
            <h2 id="client-form-title" className="text-lg font-semibold text-slate-800">{editingId ? 'Editar cliente' : 'Nuevo cliente'}</h2>
            {editingId && <button type="button" onClick={resetForm} className="text-sm font-medium text-slate-500 hover:text-slate-800">Cancelar</button>}
          </div>
          {!canWriteClients && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">El rol de producción tiene acceso de solo lectura a clientes.</p>}
          <div>
            <label htmlFor="client-name" className="block text-sm font-medium text-slate-700">Nombre</label>
            <input id="client-name" required disabled={!canWriteClients} value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <div>
            <label htmlFor="client-email" className="block text-sm font-medium text-slate-700">Correo</label>
            <input id="client-email" type="email" required disabled={!canWriteClients} value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            <div>
              <label htmlFor="client-phone" className="block text-sm font-medium text-slate-700">Teléfono</label>
              <input id="client-phone" disabled={!canWriteClients} value={form.telefono ?? ''} onChange={(event) => setForm({ ...form, telefono: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
            <div>
              <label htmlFor="client-city" className="block text-sm font-medium text-slate-700">Ciudad</label>
              <input id="client-city" disabled={!canWriteClients} value={form.ciudad ?? ''} onChange={(event) => setForm({ ...form, ciudad: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="client-type" className="block text-sm font-medium text-slate-700">Tipo</label>
              <select id="client-type" disabled={!canWriteClients} value={form.tipo} onChange={(event) => setForm({ ...form, tipo: event.target.value as ClientInput['tipo'] })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                <option value="natural">Natural</option>
                <option value="empresa">Empresa</option>
              </select>
            </div>
            <div>
              <label htmlFor="client-status" className="block text-sm font-medium text-slate-700">Estado</label>
              <select id="client-status" disabled={!canWriteClients} value={form.estado} onChange={(event) => setForm({ ...form, estado: event.target.value as ClientInput['estado'] })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                <option value="potencial">Potencial</option>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
              </select>
            </div>
          </div>
          {form.tipo === 'empresa' && (
            <div>
              <label htmlFor="client-company" className="block text-sm font-medium text-slate-700">Empresa</label>
              <input id="client-company" disabled={!canWriteClients} value={form.empresa ?? ''} onChange={(event) => setForm({ ...form, empresa: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
          )}
          <div>
            <label htmlFor="client-origin" className="block text-sm font-medium text-slate-700">Origen</label>
            <select id="client-origin" disabled={!canWriteClients} value={form.origen} onChange={(event) => setForm({ ...form, origen: event.target.value as ClientInput['origen'] })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
              <option value="web">Sitio web</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="redes">Redes sociales</option>
              <option value="referido">Referido</option>
              <option value="otro">Otro</option>
            </select>
          </div>
          <div>
            <label htmlFor="client-notes" className="block text-sm font-medium text-slate-700">Notas</label>
            <textarea id="client-notes" rows={3} disabled={!canWriteClients} value={form.notas ?? ''} onChange={(event) => setForm({ ...form, notas: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <button type="submit" disabled={saving || !canWriteClients} className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-400">
            {saving ? 'Guardando…' : editingId ? 'Actualizar cliente' : 'Crear cliente'}
          </button>
        </form>

        <section className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="clients-list-title">
          <div className="border-b border-slate-200 p-4">
            <h2 id="clients-list-title" className="font-semibold text-slate-800">Clientes ({clients.length})</h2>
          </div>
          {loading ? (
            <p className="p-8 text-center text-sm text-slate-500" role="status">Cargando clientes…</p>
          ) : clients.length === 0 ? (
            <p className="p-8 text-center text-sm text-slate-500">No hay clientes registrados.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <caption className="sr-only">Listado de clientes y acciones disponibles</caption>
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr><th className="p-3">Cliente</th><th className="p-3">Contacto</th><th className="p-3">Origen</th><th className="p-3">Estado</th><th className="p-3 text-right">Acciones</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {clients.map((client) => (
                    <tr key={client.id} className="hover:bg-slate-50">
                      <td className="p-3"><p className="font-semibold text-slate-800">{client.nombre}</p><p className="text-xs text-slate-500">{client.empresa || client.tipo}</p></td>
                      <td className="p-3 text-slate-600"><p>{client.email}</p><p className="text-xs">{client.telefono || 'Sin teléfono'}</p></td>
                      <td className="p-3 capitalize text-slate-600">{client.origen}</td>
                      <td className="p-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${client.estado === 'activo' ? 'bg-emerald-100 text-emerald-800' : client.estado === 'inactivo' ? 'bg-slate-200 text-slate-700' : 'bg-amber-100 text-amber-800'}`}>{client.estado}</span></td>
                      <td className="p-3"><div className="flex justify-end gap-2">
                        <button type="button" onClick={() => showHistory(client)} className="rounded-md border border-slate-300 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100">Historial</button>
                        {canWriteClients && <button type="button" onClick={() => startEdit(client)} className="rounded-md border border-indigo-200 px-2.5 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-50">Editar</button>}
                        {canDeleteClients && <button type="button" onClick={() => handleDelete(client)} className="rounded-md border border-red-200 px-2.5 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50">Eliminar</button>}
                      </div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="history-title">
        <div className="flex flex-col gap-2 border-b border-slate-200 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 id="history-title" className="text-lg font-semibold text-slate-800">Historial de interacciones</h2>
            <p className="text-sm text-slate-500">{selectedClient ? `Filtrado por ${selectedClient.nombre}` : 'Selecciona “Historial” en un cliente.'}</p>
          </div>
        </div>

        {selectedClient && (
          <div className="mt-5 grid gap-6 lg:grid-cols-[minmax(17rem,0.8fr)_minmax(0,2fr)]">
            <form onSubmit={handleCreateInteraction} className="space-y-4 rounded-lg bg-slate-50 p-4">
              <h3 className="font-semibold text-slate-800">Registrar interacción</h3>
              <div>
                <label htmlFor="interaction-type" className="block text-sm font-medium text-slate-700">Tipo</label>
                <select id="interaction-type" value={interactionType} onChange={(event) => setInteractionType(event.target.value as InteractionType)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                  <option value="llamada">Llamada</option><option value="correo_manual">Correo manual</option><option value="reunión">Reunión</option><option value="seguimiento">Seguimiento</option>
                </select>
              </div>
              <div>
                <label htmlFor="interaction-description" className="block text-sm font-medium text-slate-700">Descripción</label>
                <textarea id="interaction-description" rows={4} required value={interactionDescription} onChange={(event) => setInteractionDescription(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2" />
              </div>
              <button type="submit" disabled={saving} className="w-full rounded-lg bg-slate-800 px-4 py-2.5 font-semibold text-white hover:bg-slate-900 disabled:bg-slate-400">Agregar al historial</button>
            </form>
            <div>
              {historyLoading ? <p className="py-6 text-center text-sm text-slate-500">Cargando historial…</p> : interactions.length === 0 ? <p className="py-6 text-center text-sm text-slate-500">No hay interacciones para este cliente.</p> : (
                <ol className="space-y-3">
                  {interactions.map((interaction) => (
                    <li key={interaction.id} className="rounded-lg border border-slate-200 p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2"><span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700">{interactionLabels[interaction.tipo]}</span><time className="text-xs text-slate-500">{new Date(interaction.created_at).toLocaleString('es')}</time></div>
                      <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{interaction.descripcion}</p>
                    </li>
                  ))}
                </ol>
              )}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
