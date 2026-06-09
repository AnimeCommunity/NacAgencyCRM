'use client';
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

export default function SettingsPage() {
  const [config, setConfig] = useState({ id: null, email_usuario: '', email_password: '', servidor_host: 'smtp.gmail.com', puerto: 587, use_tls: true });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    async function fetchConfig() {
      try {
        const res = await apiService.marketing.getConfig();
        if (res && res.length > 0) {
          setConfig(res[0]); // se carga la primera confi existente
          setSaved(true);
        }
      } catch (err) { console.error(err); }
    }
    fetchConfig();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (saved && config.id) {
        await apiService.marketing.updateConfig(config.id, config);
      } else {
        await apiService.marketing.saveConfig(config);
      }
      alert("¡Configuración de Servidor de Correo guardada con éxito!");
      setSaved(true);
    } catch (err: any) {
      alert(`Error al guardar: ${err.message}`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h2 className="text-3xl font-bold">Configuración Global del CRM</h2>
        <p className="text-gray-500">Ajusta los servidores de salida para los correos automáticos.</p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow-sm border space-y-4">
        <h3 className="text-lg font-semibold text-gray-700">Parámetros del Servidor SMTP</h3>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Correo Electrónico Emisor</label>
          <input type="email" required placeholder="ejemplo@empresa.com" value={config.email_usuario} onChange={e => setConfig({...config, email_usuario: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">Contraseña / Token de Aplicación</label>
          <input type="password" required placeholder="••••••••••••••••" value={config.email_password} onChange={e => setConfig({...config, email_password: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          <p className="text-xs text-gray-400 mt-1">Si usas Gmail, recuerda generar una contraseña de aplicación en tu cuenta de Google.</p>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700">Servidor Host</label>
            <input type="text" required value={config.servidor_host} onChange={e => setConfig({...config, servidor_host: e.target.value})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Puerto</label>
            <input type="number" required value={config.puerto} onChange={e => setConfig({...config, puerto: parseInt(e.target.value) || 587})} className="mt-1 block w-full p-2 border rounded-md" />
          </div>
        </div>

        <div className="flex items-center space-x-2 pt-2">
          <input type="checkbox" id="tls" checked={config.use_tls} onChange={e => setConfig({...config, use_tls: e.target.checked})} className="rounded text-indigo-600" />
          <label htmlFor="tls" className="text-sm text-gray-700 font-medium">Requerir conexión cifrada segura (TLS)</label>
        </div>

        <button type="submit" className="w-full mt-4 bg-indigo-600 text-white p-3 rounded-md font-medium hover:bg-indigo-700 transition">
          {saved ? 'Actualizar Configuración' : 'Guardar Configuración por Primera Vez'}
        </button>
      </form>
    </div>
  );
}