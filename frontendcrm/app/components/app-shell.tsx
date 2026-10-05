'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  apiService,
  getErrorMessage,
  getSessionClaims,
  hasStoredSession,
  type UserRole,
} from '@/services/api';

const links: Array<{ href: string; label: string; roles: readonly UserRole[] }> = [
  { href: '/', label: 'Inicio', roles: ['admin', 'sales', 'production'] as const },
  { href: '/dashboard', label: 'Analítica', roles: ['admin', 'sales', 'production'] as const },
  { href: '/clients', label: 'Clientes', roles: ['admin', 'sales', 'production'] as const },
  { href: '/projects', label: 'Proyectos', roles: ['admin', 'sales', 'production'] as const },
  { href: '/quotations', label: 'Cotizaciones', roles: ['admin', 'sales', 'production'] as const },
  { href: '/marketing', label: 'Marketing', roles: ['admin', 'sales', 'production'] as const },
  { href: '/users', label: 'Usuarios', roles: ['admin'] as const },
  { href: '/settings', label: 'Ajustes SMTP', roles: ['admin'] as const },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [authenticated, setAuthenticated] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [logoutError, setLogoutError] = useState('');
  const isAuthPage = pathname === '/login' || pathname === '/register';
  const role = getSessionClaims()?.role;

  useEffect(() => {
    const updateAuth = () => {
      const sessionAvailable = hasStoredSession();
      setAuthenticated(sessionAvailable);
      setAuthChecked(true);
      if (!sessionAvailable && !isAuthPage) router.replace('/login');
    };
    updateAuth();
    window.addEventListener('crm-auth-changed', updateAuth);
    window.addEventListener('storage', updateAuth);
    return () => {
      window.removeEventListener('crm-auth-changed', updateAuth);
      window.removeEventListener('storage', updateAuth);
    };
  }, [isAuthPage, pathname, router]);

  const handleLogout = async () => {
    setLogoutError('');
    try {
      await apiService.auth.logout();
      router.replace('/login');
    } catch (error) {
      setLogoutError(getErrorMessage(error, 'No fue posible cerrar la sesión en el servidor.'));
      router.replace('/login');
    }
  };

  if (isAuthPage) return <main className="min-h-screen bg-slate-100">{children}</main>;

  if (!authChecked || !authenticated) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-100 text-sm text-slate-500">Validando sesión…</main>;
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 lg:flex">
      <aside className="bg-slate-950 text-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-64 lg:flex-col lg:justify-between">
        <div>
          <div className="flex items-center justify-between gap-4 px-4 py-4 lg:block lg:px-5 lg:py-6">
            <Link href="/" className="text-xl font-bold tracking-tight text-indigo-300">
              CRM ANC
            </Link>
            {authenticated && (
              <button
                type="button"
                onClick={handleLogout}
                className="rounded-md border border-slate-700 px-3 py-2 text-xs font-semibold text-slate-200 transition hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-300 lg:hidden"
              >
                Salir
              </button>
            )}
          </div>
          <nav aria-label="Navegación principal" className="flex gap-2 overflow-x-auto px-3 pb-4 lg:block lg:space-y-1 lg:overflow-visible lg:px-4">
            {links.filter((link) => role && link.roles.includes(role)).map((link) => {
              const active = link.href === '/' ? pathname === '/' : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? 'page' : undefined}
                  className={`whitespace-nowrap rounded-lg px-3 py-2 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-300 lg:block ${
                    active ? 'bg-indigo-600 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="hidden border-t border-slate-800 p-4 lg:block">
          {role && <p className="mb-2 text-xs capitalize text-slate-400">Rol: {role}</p>}
          {authenticated && (
            <button
              type="button"
              onClick={handleLogout}
              className="w-full rounded-lg border border-slate-700 px-3 py-2 text-sm font-semibold text-slate-200 transition hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-300"
            >
              Cerrar sesión
            </button>
          )}
          {logoutError && <p className="mt-2 text-xs text-red-300" role="alert">{logoutError}</p>}
          <p className="mt-4 text-center text-xs text-slate-500">ANC Agency · 2026</p>
        </div>
      </aside>
      <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">{children}</main>
    </div>
  );
}
