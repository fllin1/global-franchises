import { Sidebar } from './Sidebar';
import { ComparisonProvider } from '@/contexts/ComparisonContext';
import PersistentComparisonBar from './PersistentComparisonBar';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <ComparisonProvider>
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <Sidebar />
        <div className="md:pl-64 flex flex-col flex-1 min-h-screen transition-all duration-300 ease-in-out">
          <main className="flex-1 pb-24"> {/* Add padding bottom for sticky bar */}
            {children}
          </main>
          <PersistentComparisonBar />
        </div>
      </div>
    </ComparisonProvider>
  );
}

