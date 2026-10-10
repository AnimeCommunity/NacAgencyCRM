'use client';

import { FormEvent, useEffect, useState } from 'react';
import {
  Client,
  MarketingTemplate,
  MarketingTemplateInput,
  apiService,
  getErrorMessage,
  getSessionClaims,
} from '@/services/api';

const emptyTemplate: MarketingTemplateInput = {
  nombre: '',
  tipo: 'email',
  asunto: '',
  contenido: '',
};

export default function MarketingPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [templates, setTemplates] = useState<MarketingTemplate[]>([]);
  const [templateForm, setTemplateForm] = useState(emptyTemplate);
  const [selection, setSelection] = useState({ clientId: '', templateId: '' });
  const [loading, setLoading] = useState(true);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [whatsappUrl, setWhatsappUrl] = useState('');
  const role = getSessionClaims()?.role;
  const canManage = role === 'admin' || role === 'sales';

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const [clientData, templateData] = await Promise.all([
          apiService.clientes.getAll(),
          apiService.marketing.getTemplates(),
        ]);
        if (active) {
          setClients(clientData);
          setTemplates(templateData);
        }
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar marketing.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleCreateTemplate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSavingTemplate(true);
    setError('');
    setNotice('');
    try {
      const created = await apiService.marketing.createTemplate({
        ...templateForm,
        asunto: templateForm.tipo === 'email' ? templateForm.asunto : '',
      });
      setTemplates((current) => [created, ...current]);
      setTemplateForm(emptyTemplate);
      setNotice('Plantilla creada correctamente.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible crear la plantilla.'));
    } finally {
      setSavingTemplate(false);
    }
  };

  const handleSend = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSending(true);
    setError('');
    setNotice('');
    setWhatsappUrl('');
    try {
      const response = await apiService.marketing.enviarCampana(
        Number(selection.clientId),
        Number(selection.templateId),
      );
      if (response.url) setWhatsappUrl(response.url);
      setNotice(response.status || 'Acción de marketing completada.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible ejecutar la acción de marketing.'));
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Marketing y comunicaciones</h1>
        <p className="mt-1 text-sm text-slate-500">Crea plantillas y registra cada envío en el historial del cliente.</p>
      </header>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
        {whatsappUrl && <a href={whatsappUrl} target="_blank" rel="noopener noreferrer" className="inline-flex rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800">Abrir conversación en WhatsApp</a>}
      </div>

      {loading ? <p className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">Cargando clientes y plantillas…</p> : (
        <div className="grid gap-6 lg:grid-cols-2">
          <form onSubmit={handleCreateTemplate} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="template-form-title">
            <h2 id="template-form-title" className="text-lg font-semibold text-slate-800">Nueva plantilla</h2>
            {!canManage && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">El rol de producción puede consultar plantillas, pero no crearlas ni enviar campañas.</p>}
            <div>
              <label htmlFor="template-name" className="block text-sm font-medium text-slate-700">Nombre</label>
              <input id="template-name" required disabled={!canManage} value={templateForm.nombre} onChange={(event) => setTemplateForm({ ...templateForm, nombre: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
            <div>
              <label htmlFor="template-type" className="block text-sm font-medium text-slate-700">Canal</label>
              <select id="template-type" disabled={!canManage} value={templateForm.tipo} onChange={(event) => setTemplateForm({ ...templateForm, tipo: event.target.value as MarketingTemplateInput['tipo'] })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                <option value="email">Correo electrónico</option><option value="whatsapp">WhatsApp</option>
              </select>
            </div>
            {templateForm.tipo === 'email' && (
              <div>
                <label htmlFor="template-subject" className="block text-sm font-medium text-slate-700">Asunto</label>
                <input id="template-subject" required disabled={!canManage} value={templateForm.asunto} onChange={(event) => setTemplateForm({ ...templateForm, asunto: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
              </div>
            )}
            <div>
              <label htmlFor="template-content" className="block text-sm font-medium text-slate-700">Mensaje</label>
              <p className="mb-1 text-xs text-slate-500">Usa {'{nombre}'} para personalizar el destinatario.</p>
              <textarea id="template-content" required rows={6} disabled={!canManage} value={templateForm.contenido} onChange={(event) => setTemplateForm({ ...templateForm, contenido: event.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2" />
            </div>
            <button type="submit" disabled={savingTemplate || !canManage} className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-400">{savingTemplate ? 'Guardando…' : 'Guardar plantilla'}</button>
          </form>

          <div className="space-y-6">
            <form onSubmit={handleSend} className="space-y-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="campaign-form-title">
              <h2 id="campaign-form-title" className="text-lg font-semibold text-slate-800">Enviar comunicación</h2>
              <div>
                <label htmlFor="campaign-client" className="block text-sm font-medium text-slate-700">Cliente</label>
                <select id="campaign-client" required disabled={!canManage} value={selection.clientId} onChange={(event) => setSelection({ ...selection, clientId: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                  <option value="">Selecciona un cliente</option>
                  {clients.map((client) => <option key={client.id} value={client.id}>{client.nombre} · {client.email}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="campaign-template" className="block text-sm font-medium text-slate-700">Plantilla</label>
                <select id="campaign-template" required disabled={!canManage} value={selection.templateId} onChange={(event) => setSelection({ ...selection, templateId: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">
                  <option value="">Selecciona una plantilla</option>
                  {templates.map((template) => <option key={template.id} value={template.id}>{template.nombre} · {template.tipo_display}</option>)}
                </select>
              </div>
              <button type="submit" disabled={sending || !canManage} className="w-full rounded-lg bg-emerald-700 px-4 py-3 font-semibold text-white hover:bg-emerald-800 disabled:bg-slate-400">{sending ? 'Procesando…' : 'Ejecutar acción'}</button>
            </form>

            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-labelledby="templates-title">
              <h2 id="templates-title" className="font-semibold text-slate-800">Plantillas activas ({templates.length})</h2>
              {templates.length === 0 ? <p className="mt-4 text-sm text-slate-500">No hay plantillas registradas.</p> : (
                <ul className="mt-3 max-h-80 divide-y divide-slate-100 overflow-y-auto">
                  {templates.map((template) => (
                    <li key={template.id} className="py-3">
                      <div className="flex items-center justify-between gap-3"><span className="font-medium text-slate-800">{template.nombre}</span><span className={`rounded-full px-2 py-1 text-xs font-semibold ${template.tipo === 'email' ? 'bg-blue-100 text-blue-800' : 'bg-emerald-100 text-emerald-800'}`}>{template.tipo_display}</span></div>
                      <p className="mt-1 line-clamp-2 text-sm text-slate-500">{template.contenido}</p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
