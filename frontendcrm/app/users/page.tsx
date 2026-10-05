'use client';

import { useEffect, useState } from 'react';
import {
  UserRole,
  UserSummary,
  apiService,
  getErrorMessage,
  getSessionClaims,
} from '@/services/api';

const roleLabels: Record<UserRole, string> = {
  admin: 'Administrador',
  sales: 'Ventas',
  production: 'Producción',
};

export default function UsersPage() {
  const [users, setUsers] = useState<UserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const claims = getSessionClaims();
  const isAdmin = claims?.role === 'admin';
  const currentUserId = claims?.user_id;

  useEffect(() => {
    let active = true;
    void (async () => {
      try {
        const data = await apiService.usuarios.getAll();
        if (active) setUsers(data);
      } catch (requestError) {
        if (active) setError(getErrorMessage(requestError, 'No fue posible cargar los usuarios.'));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const updateUser = async (
    user: UserSummary,
    changes: Partial<Pick<UserSummary, 'role' | 'is_active'>>,
  ) => {
    setUpdatingId(user.id);
    setError('');
    setNotice('');
    try {
      const updated = await apiService.usuarios.update(user.id, changes);
      setUsers((current) => current.map((entry) => (entry.id === updated.id ? updated : entry)));
      setNotice(`Usuario ${updated.username} actualizado.`);
    } catch (requestError) {
      setError(getErrorMessage(requestError, 'No fue posible actualizar el usuario.'));
    } finally {
      setUpdatingId(null);
    }
  };

  if (!isAdmin) {
    return <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700" role="alert">Solo los administradores pueden gestionar usuarios.</p>;
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">Usuarios y accesos</h1>
        <p className="mt-1 text-sm text-slate-500">Aprueba solicitudes, desactiva cuentas y asigna roles operativos.</p>
      </header>

      <div aria-live="polite" className="space-y-2">
        {error && <p className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
        {notice && <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800" role="status">{notice}</p>}
      </div>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm" aria-labelledby="users-title">
        <div className="border-b border-slate-200 p-4">
          <h2 id="users-title" className="font-semibold text-slate-800">Cuentas registradas ({users.length})</h2>
        </div>
        {loading ? <p className="p-8 text-center text-sm text-slate-500">Cargando usuarios…</p> : users.length === 0 ? <p className="p-8 text-center text-sm text-slate-500">No hay usuarios registrados.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <caption className="sr-only">Gestión de usuarios y roles</caption>
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr><th className="p-3">Usuario</th><th className="p-3">Correo</th><th className="p-3">Rol</th><th className="p-3">Estado</th><th className="p-3 text-right">Acción</th></tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((user) => {
                  const isCurrentUser = user.id === currentUserId;
                  return (
                  <tr key={user.id}>
                    <td className="p-3"><strong className="text-slate-900">{user.username}</strong>{isCurrentUser && <span className="ml-2 rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-semibold text-indigo-700">Tu cuenta</span>}<span className="block text-xs text-slate-500">{[user.first_name, user.last_name].filter(Boolean).join(' ') || 'Sin nombre'}</span></td>
                    <td className="p-3 text-slate-600">{user.email || 'Sin correo'}</td>
                    <td className="p-3">
                      <select aria-label={`Rol de ${user.username}`} disabled={isCurrentUser || updatingId === user.id} value={user.role} onChange={(event) => updateUser(user, { role: event.target.value as UserRole })} className="rounded-lg border border-slate-300 bg-white px-3 py-2 disabled:bg-slate-100">
                        {(Object.keys(roleLabels) as UserRole[]).map((role) => <option key={role} value={role}>{roleLabels[role]}</option>)}
                      </select>
                    </td>
                    <td className="p-3"><span className={`rounded-full px-2 py-1 text-xs font-semibold ${user.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}>{user.is_active ? 'Activo' : 'Pendiente / inactivo'}</span></td>
                    <td className="p-3 text-right"><button type="button" disabled={isCurrentUser || updatingId === user.id} onClick={() => updateUser(user, { is_active: !user.is_active })} className={`rounded-lg px-3 py-2 text-xs font-semibold text-white disabled:bg-slate-400 ${user.is_active ? 'bg-red-700 hover:bg-red-800' : 'bg-emerald-700 hover:bg-emerald-800'}`}>{isCurrentUser ? 'Protegida' : user.is_active ? 'Desactivar' : 'Activar'}</button></td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
