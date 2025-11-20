import { Sidebar } from './Sidebar';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar />
      <div className="md:pl-64 flex flex-col flex-1 min-h-screen transition-all duration-300 ease-in-out">
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}

