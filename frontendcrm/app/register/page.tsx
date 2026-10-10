'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FormEvent, useState } from 'react';
import { apiService, getErrorMessage } from '@/services/api';

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ username: '', password: '', email: '', first_name: '', last_name: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await apiService.auth.register(form);
      router.replace('/login?registered=1');
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible crear la cuenta.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 sm:p-6">
      <section className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8" aria-labelledby="register-title">
        <div className="mb-7 text-center">
          <p className="text-sm font-semibold uppercase tracking-widest text-indigo-600">ANC Agency</p>
          <h1 id="register-title" className="mt-2 text-3xl font-bold text-slate-900">Crear cuenta</h1>
          <p className="mt-2 text-sm text-slate-500">La solicitud crea un perfil de ventas inactivo hasta que un administrador lo apruebe.</p>
        </div>

        {error && <p className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="first-name" className="block text-sm font-medium text-slate-700">Nombre</label>
              <input id="first-name" autoComplete="given-name" required value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
            </div>
            <div>
              <label htmlFor="last-name" className="block text-sm font-medium text-slate-700">Apellido</label>
              <input id="last-name" autoComplete="family-name" required value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
            </div>
          </div>
          <div>
            <label htmlFor="register-email" className="block text-sm font-medium text-slate-700">Correo electrónico</label>
            <input id="register-email" type="email" autoComplete="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
          </div>
          <div>
            <label htmlFor="register-username" className="block text-sm font-medium text-slate-700">Usuario</label>
            <input id="register-username" autoComplete="username" required value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
          </div>
          <div>
            <label htmlFor="register-password" className="block text-sm font-medium text-slate-700">Contraseña</label>
            <input id="register-password" name="password" type="password" autoComplete="new-password" minLength={8} required value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2.5" />
          </div>
          <button type="submit" disabled={loading} className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white transition hover:bg-indigo-700 disabled:bg-slate-400">
            {loading ? 'Creando cuenta…' : 'Registrarme'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          ¿Ya tienes una cuenta?{' '}
          <Link href="/login" className="font-semibold text-indigo-600 hover:underline">Iniciar sesión</Link>
        </p>
      </section>
    </div>
  );
}
