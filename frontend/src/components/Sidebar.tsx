'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Users, 
  Map, 
  Building,
  Network,
  Settings, 
  Sparkles,
  Sun,
  Moon
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'My Leads', href: '/leads', icon: Users },
  { name: 'Franchises', href: '/franchises', icon: Building },
  { name: 'Family Brands', href: '/family-brands', icon: Network },
  { name: 'Territory Map', href: '/territory', icon: Map },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Determine current visual theme for display
  // Use resolvedTheme if theme is 'system' or undefined, otherwise use theme
  const currentTheme = (theme === 'system' || !theme) ? (resolvedTheme || 'light') : theme;
  
  const handleThemeToggle = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    // Test if click is firing
    console.log('Button clicked!', { theme, resolvedTheme, setTheme: typeof setTheme });
    
    if (!setTheme) {
      console.error('setTheme is not available!');
      return;
    }
    
    // Get the actual current theme state - check if HTML has 'dark' class as fallback
    let actualCurrentTheme: string;
    if (theme && theme !== 'system') {
      actualCurrentTheme = theme;
    } else if (resolvedTheme) {
      actualCurrentTheme = resolvedTheme;
    } else {
      // Fallback: check DOM directly
      actualCurrentTheme = typeof document !== 'undefined' && document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    }
    
    // Determine what the next theme should be
    const nextTheme = actualCurrentTheme === 'dark' ? 'light' : 'dark';
    
    // Explicitly set to 'light' or 'dark', overriding system preference
    try {
      setTheme(nextTheme);
      console.log('Theme set successfully:', { 
        theme, 
        resolvedTheme, 
        actualCurrent: actualCurrentTheme, 
        next: nextTheme,
        htmlHasDark: typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
      });
    } catch (error) {
      console.error('Error setting theme:', error);
    }
  };

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
        <div className="flex-1 flex flex-col min-h-0" />
      </div>
    );
  }

  return (
    <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800">
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between h-16 flex-shrink-0 px-4 bg-white dark:bg-slate-900 text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-800">
           <div className="flex items-center">
             <Sparkles className="h-6 w-6 text-indigo-600 dark:text-indigo-500 mr-2" />
             <span className="text-lg font-bold tracking-tight">BrokerAI</span>
           </div>
           
           {/* Theme Toggle in Header */}
           <button
             type="button"
             onClick={handleThemeToggle}
             className="p-1.5 rounded-md text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
             title={currentTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
             aria-label="Toggle theme"
           >
             {currentTheme === 'dark' ? (
               <Sun className="h-5 w-5 hover:text-yellow-400 transition-colors" />
             ) : (
               <Moon className="h-5 w-5 hover:text-indigo-600 transition-colors" />
             )}
           </button>
        </div>
        <div className="flex-1 flex flex-col overflow-y-auto">
          <nav className="flex-1 px-2 py-4 space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors
                    ${isActive 
                      ? 'bg-indigo-50 text-indigo-600 dark:bg-slate-800 dark:text-white' 
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'}
                  `}
                >
                  <item.icon
                    className={`
                      mr-3 flex-shrink-0 h-5 w-5
                      ${isActive ? 'text-indigo-600 dark:text-indigo-500' : 'text-slate-400 group-hover:text-slate-500 dark:text-slate-400 dark:group-hover:text-slate-300'}
                    `}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </div>
  );
}
