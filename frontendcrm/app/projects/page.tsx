'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import {
  Client,
  EventType,
  Project,
  ProjectStatus,
  apiService,
  getErrorMessage,
  getSessionClaims,
} from '@/services/api';

const emptyProject = {
  cliente: '',
  nombre: '',
  descripcion: '',
  tipo_evento: 'otro' as EventType,
  fecha_inicio: '',
  fecha_fin: '',
  presupuesto_estimado: '',
  pagado: false,
  fecha_pago: '',
  estado: 'propuesta' as ProjectStatus,
};

export default function ProyectosPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState(emptyProject);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const claims = getSessionClaims();
  const canCreate = claims?.role === 'admin' || claims?.role === 'sales';
  const today = useMemo(() => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
  }, []);

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [projectData, clientData] = await Promise.all([
          apiService.proyectos.getAll(),
          apiService.clientes.getAll(),
        ]);
        if (active) {
          setProjects(projectData);
          setClients(clientData);
        }
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar los proyectos.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const resetForm = () => {
    setForm(emptyProject);
    setEditingId(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const userId = getSessionClaims()?.user_id;
    if (!userId) {
      setError('El token no contiene el identificador del usuario responsable. Inicia sesión nuevamente.');
      return;
    }
    if (form.fecha_fin < form.fecha_inicio) {
      setError('La fecha de fin no puede ser anterior a la fecha de inicio.');
      return;
    }

    setSaving(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        cliente: Number(form.cliente),
        nombre: form.nombre,
        descripcion: form.descripcion,
        tipo_evento: form.tipo_evento,
        fecha_inicio: form.fecha_inicio,
        fecha_fin: form.fecha_fin,
        presupuesto_estimado: Number(form.presupuesto_estimado),
        pagado: form.pagado,
        fecha_pago: form.pagado && form.fecha_pago ? form.fecha_pago : null,
        estado: form.estado,
      };
      if (editingId) {
        await apiService.proyectos.update(editingId, payload);
        setNotice('Proyecto actualizado correctamente.');
      } else {
        await apiService.proyectos.create({ ...payload, responsable: userId });
        setNotice('Proyecto creado correctamente.');
      }
      const refreshedProjects = await apiService.proyectos.getAll();
      setProjects(refreshedProjects);
      resetForm();
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar el proyecto.'));
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (project: Project) => {
    setEditingId(project.id);
    setForm({
      cliente: String(project.cliente.id),
      nombre: project.nombre,
      descripcion: project.descripcion,
      tipo_evento: project.tipo_evento,
      fecha_inicio: project.fecha_inicio,
      fecha_fin: project.fecha_fin,
      presupuesto_estimado: project.presupuesto_estimado,
      pagado: project.pagado,
      fecha_pago: project.fecha_pago ?? '',
      estado: project.estado,
    });
    setError('');
    setNotice('');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const cancelProject = async (project: Project) => {
    if (!window.confirm(`¿Cancelar el proyecto “${project.nombre}”?`)) return;
    setCancellingId(project.id);
    setError('');
    setNotice('');
    try {
      const updated = await apiService.proyectos.cancel(project.id);
      setProjects((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      if (editingId === updated.id) resetForm();
      setNotice(`Proyecto ${updated.nombre} cancelado.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible cancelar el proyecto.'));
    } finally {
      setCancellingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Proyectos y eventos</h1>
        <p className="mt-1 text-sm text-slate-500">Planifica eventos, fechas, responsables y presupuestos.</p>
      </header>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(19rem,0.8fr)_minmax(0,2fr)]">
        <form onSubmit={handleSubmit} className="h-fit space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="project-form-title">
          <div className="flex items-center justify-between gap-3">
            <h2 id="project-form-title" className="text-lg font-semibold text-slate-800">{editingId ? 'Editar proyecto' : 'Nuevo proyecto'}</h2>
            {editingId && <button type="button" onClick={resetForm} className="text-sm font-semibold text-slate-500 hover:text-slate-800">Cancelar edición</button>}
          </div>
          {!canCreate && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">El rol de producción tiene acceso de solo lectura.</p>}
          <div>
            <label htmlFor="project-client" className="block text-sm font-medium text-slate-700">Cliente</label>
            <select id="project-client" required disabled={!canCreate} value={form.cliente} onChange={(event) => setForm({ ...form, cliente: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
              <option value="">Selecciona un cliente</option>
              {clients.map((client) => <option key={client.id} value={client.id}>{client.nombre}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="project-name" className="block text-sm font-medium text-slate-700">Nombre del evento</label>
            <input id="project-name" required disabled={!canCreate} value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <div>
            <label htmlFor="project-description" className="block text-sm font-medium text-slate-700">Descripción</label>
            <textarea id="project-description" required rows={3} disabled={!canCreate} value={form.descripcion} onChange={(event) => setForm({ ...form, descripcion: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="event-type" className="block text-sm font-medium text-slate-700">Tipo</label>
              <select id="event-type" disabled={!canCreate} value={form.tipo_evento} onChange={(event) => setForm({ ...form, tipo_evento: event.target.value as EventType })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                <option value="concierto">Concierto</option><option value="show">Show</option><option value="streaming">Streaming</option><option value="fiesta">Fiesta</option><option value="sesion_fotografica">Sesión fotográfica</option><option value="otro">Otro</option>
              </select>
            </div>
            <div>
              <label htmlFor="project-status" className="block text-sm font-medium text-slate-700">Estado</label>
              <select id="project-status" disabled={!canCreate} value={form.estado} onChange={(event) => setForm({ ...form, estado: event.target.value as ProjectStatus })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                <option value="propuesta">Propuesta</option><option value="aprobado">Aprobado</option><option value="en_proceso">En proceso</option><option value="finalizado">Finalizado</option>{form.estado === 'cancelado' && <option value="cancelado" disabled>Cancelado</option>}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="start-date" className="block text-sm font-medium text-slate-700">Inicio</label>
              <input id="start-date" type="date" required disabled={!canCreate} value={form.fecha_inicio} onChange={(event) => setForm({ ...form, fecha_inicio: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
            <div>
              <label htmlFor="end-date" className="block text-sm font-medium text-slate-700">Fin</label>
              <input id="end-date" type="date" required disabled={!canCreate} value={form.fecha_fin} onChange={(event) => setForm({ ...form, fecha_fin: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
          </div>
          <div>
            <label htmlFor="project-budget" className="block text-sm font-medium text-slate-700">Presupuesto estimado</label>
            <input id="project-budget" type="number" min="0" step="0.01" required disabled={!canCreate} value={form.presupuesto_estimado} onChange={(event) => setForm({ ...form, presupuesto_estimado: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
          </div>
          <div className="rounded-lg border border-slate-200 p-3">
            <label className="flex items-center gap-3 text-sm font-medium text-slate-700">
              <input type="checkbox" disabled={!canCreate} checked={form.pagado} onChange={(event) => setForm({ ...form, pagado: event.target.checked, fecha_pago: event.target.checked ? form.fecha_pago : '' })} className="h-4 w-4 rounded border-slate-300 text-emerald-600" />
              Pago confirmado
            </label>
            {form.pagado && (
              <div className="mt-3">
                <label htmlFor="project-payment-date" className="block text-xs font-medium text-slate-600">Fecha de pago</label>
                <input id="project-payment-date" type="date" max={today} required disabled={!canCreate} value={form.fecha_pago} onChange={(event) => setForm({ ...form, fecha_pago: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
              </div>
            )}
          </div>
          <button type="submit" disabled={saving || !canCreate} className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-400">{saving ? 'Guardando…' : editingId ? 'Actualizar proyecto' : 'Crear proyecto'}</button>
        </form>

        <section className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="projects-list-title">
          <div className="border-b border-slate-200 p-4"><h2 id="projects-list-title" className="font-semibold text-slate-800">Proyectos ({projects.length})</h2></div>
          {loading ? <p className="p-8 text-center text-sm text-slate-500">Cargando proyectos…</p> : projects.length === 0 ? <p className="p-8 text-center text-sm text-slate-500">No hay proyectos registrados.</p> : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[780px] text-left text-sm">
                <caption className="sr-only">Listado de proyectos</caption>
                <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-3">Proyecto</th><th className="p-3">Cliente</th><th className="p-3">Fechas</th><th className="p-3">Responsable</th><th className="p-3">Presupuesto</th><th className="p-3">Estado</th><th className="p-3">Pago</th><th className="p-3 text-right">Acciones</th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {projects.map((project) => (
                    <tr key={project.id} className="hover:bg-slate-50">
                      <td className="p-3"><p className="font-semibold text-slate-800">{project.nombre}</p><p className="text-xs capitalize text-slate-500">{project.tipo_evento.replaceAll('_', ' ')}</p></td>
                      <td className="p-3 text-slate-600">{project.cliente.nombre}</td>
                      <td className="p-3 text-xs text-slate-600">{project.fecha_inicio}<br />{project.fecha_fin}</td>
                      <td className="p-3 text-slate-600">{project.responsable?.username || 'Sin asignar'}</td>
                      <td className="p-3 font-semibold text-emerald-700">${Number(project.presupuesto_estimado).toLocaleString('es', { minimumFractionDigits: 2 })}</td>
                      <td className="p-3"><span className="rounded-full bg-indigo-50 px-2 py-1 text-xs font-semibold capitalize text-indigo-700">{project.estado.replaceAll('_', ' ')}</span></td>
                      <td className="p-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${project.pagado ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>{project.pagado ? `Pagado${project.fecha_pago ? ` · ${project.fecha_pago}` : ''}` : 'Pendiente'}</span></td>
                      <td className="p-3">
                        {canCreate ? (
                          <div className="flex justify-end gap-2">
                            <button type="button" onClick={() => startEdit(project)} className="rounded-md border border-indigo-200 px-2.5 py-1.5 text-xs font-semibold text-indigo-700 hover:bg-indigo-50">Editar</button>
                            <button type="button" disabled={cancellingId === project.id || project.estado === 'cancelado' || project.estado === 'finalizado'} onClick={() => cancelProject(project)} className="rounded-md border border-red-200 px-2.5 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-40">{cancellingId === project.id ? 'Cancelando…' : 'Cancelar proyecto'}</button>
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
  );
}
