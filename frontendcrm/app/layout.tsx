import Link from 'next/link';
import '@/app/globals.css'; 

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="bg-gray-100 text-gray-900 flex h-screen overflow-hidden">
        {/* SIDEBAR */}
        <aside className="w-64 bg-slate-900 text-white flex flex-col justify-between p-4">
          <div>
            <h1 className="text-2xl font-bold mb-8 text-indigo-400">CRM ANC</h1>
            <nav className="space-y-2">
              <Link href="/" className="block p-3 rounded hover:bg-slate-800 transition">Dashboard</Link>
              <Link href="/clients" className="block p-3 rounded hover:bg-slate-800 transition">Clientes</Link>
              <Link href="/projects" className="block p-3 rounded hover:bg-slate-800 transition">Proyectos</Link>
              <Link href="/quotations" className="block p-3 rounded hover:bg-slate-800 transition">Cotizaciones</Link>
              <Link href="/marketing" className="block p-3 rounded hover:bg-slate-800 transition">Marketing</Link>
              <Link href="/settings" className="block p-3 rounded hover:bg-slate-800 transition">Ajustes SMTP</Link>
            </nav>
          </div>
          <div className="text-xs text-slate-500 text-center">ANC Agency | Aniokku © 2026</div>
        </aside>

        {/* CONTENIDO PRINCIPAL */}
        <main className="flex-1 flex flex-col overflow-y-auto p-8">
          {children}
        </main>
      </body>
    </html>
  );
}