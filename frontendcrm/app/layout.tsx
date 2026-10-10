import type { Metadata } from 'next';
import '@/app/globals.css';
import AppShell from '@/app/components/app-shell';

export const metadata: Metadata = {
  title: 'CRM ANC',
  description: 'Sistema de gestión comercial y de eventos de ANC Agency',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
