'use client';

import { FormEvent, useEffect, useState } from 'react';
import { SMTPConfig, apiService, getErrorMessage, getSessionClaims } from '@/services/api';

export default function SettingsPage() {
  const [configId, setConfigId] = useState<number | null>(null);
  const [form, setForm] = useState({
    email_usuario: '',
    servidor_host: 'smtp.gmail.com',
    puerto: 587,
    use_tls: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const role = getSessionClaims()?.role;
  const canManage = role === 'admin';

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const configs = await apiService.marketing.getConfig();
        const current: SMTPConfig | undefined = configs[0];
        if (active && current) {
          setConfigId(current.id);
          setForm((previous) => ({
            ...previous,
            email_usuario: current.email_usuario,
            servidor_host: current.servidor_host,
            puerto: current.puerto,
            use_tls: current.use_tls,
          }));
        }
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar la configuración SMTP.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        email_usuario: form.email_usuario,
        servidor_host: form.servidor_host,
        puerto: form.puerto,
        use_tls: form.use_tls,
      };
      const saved = configId
        ? await apiService.marketing.updateConfig(configId, payload)
        : await apiService.marketing.saveConfig(payload);
      setConfigId(saved.id);
      setNotice('Configuración SMTP guardada correctamente.');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible guardar la configuración SMTP.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Ajustes SMTP</h1>
        <p className="mt-1 text-sm text-slate-500">Configura el servidor. La contraseña se suministra de forma segura con la variable CRM_SMTP_PASSWORD.</p>
      </header>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
      </div>

      {loading ? <p className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">Cargando configuración…</p> : (
        <form onSubmit={handleSubmit} className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          {!canManage && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">Solo los administradores pueden modificar la configuración SMTP.</p>}
          <div>
            <label htmlFor="smtp-email" className="block text-sm font-medium text-slate-700">Correo emisor</label>
            <input id="smtp-email" type="email" autoComplete="email" required disabled={!canManage} value={form.email_usuario} onChange={(event) => setForm({ ...form, email_usuario: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
          </div>
          <p className="rounded-lg border border-indigo-200 bg-indigo-50 p-3 text-sm text-indigo-800">
            El secreto SMTP no se almacena en la base de datos ni se acepta desde esta pantalla. Configura <code>CRM_SMTP_PASSWORD</code> en el entorno del backend.
          </p>
          <div className="grid gap-4 sm:grid-cols-[2fr_1fr]">
            <div>
              <label htmlFor="smtp-host" className="block text-sm font-medium text-slate-700">Servidor</label>
              <input id="smtp-host" required disabled={!canManage} value={form.servidor_host} onChange={(event) => setForm({ ...form, servidor_host: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
            </div>
            <div>
              <label htmlFor="smtp-port" className="block text-sm font-medium text-slate-700">Puerto</label>
              <input id="smtp-port" type="number" min={1} max={65535} required disabled={!canManage} value={form.puerto} onChange={(event) => setForm({ ...form, puerto: Number(event.target.value) })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
            </div>
          </div>
          <label className="flex items-center gap-3 text-sm font-medium text-slate-700">
            <input type="checkbox" disabled={!canManage} checked={form.use_tls} onChange={(event) => setForm({ ...form, use_tls: event.target.checked })} className="h-4 w-4 rounded border-slate-300 text-indigo-600" />
            Usar conexión segura TLS
          </label>
          <button type="submit" disabled={saving || !canManage} className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white hover:bg-indigo-700 disabled:bg-slate-400">{saving ? 'Guardando…' : configId ? 'Actualizar configuración' : 'Crear configuración'}</button>
        </form>
      )}
    </div>
  );
}
