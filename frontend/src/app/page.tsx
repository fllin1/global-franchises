'use client';
import Link from 'next/link';
import { Users, TrendingUp, Map } from 'lucide-react';

export default function DashboardHome() {
  return (
    <div className="p-10">
       <h1 className="text-2xl font-bold mb-6 text-slate-900">Dashboard Overview</h1>
       <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <Link href="/leads" className="block p-6 bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-all group">
             <div className="flex items-center gap-4">
                <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg group-hover:bg-indigo-100 transition-colors">
                   <Users className="w-6 h-6" />
                </div>
                <div>
                   <div className="text-sm text-slate-500 font-medium">Active Leads</div>
                   <div className="text-2xl font-bold text-slate-900">Manage Pipeline</div>
                </div>
             </div>
          </Link>
          
          <Link href="/territory" className="block p-6 bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-all group">
             <div className="flex items-center gap-4">
                <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg group-hover:bg-emerald-100 transition-colors">
                   <Map className="w-6 h-6" />
                </div>
                <div>
                   <div className="text-sm text-slate-500 font-medium">Territories</div>
                   <div className="text-2xl font-bold text-slate-900">Explore Availability</div>
                </div>
             </div>
          </Link>

          <Link href="/leads/new" className="block p-6 bg-white rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-all group">
             <div className="flex items-center gap-4">
                <div className="p-3 bg-purple-50 text-purple-600 rounded-lg group-hover:bg-purple-100 transition-colors">
                   <TrendingUp className="w-6 h-6" />
                </div>
                <div>
                   <div className="text-sm text-slate-500 font-medium">Quick Action</div>
                   <div className="text-2xl font-bold text-slate-900">Analyze New Lead</div>
                </div>
             </div>
          </Link>
       </div>
       
       <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
           <h2 className="text-xl font-medium text-slate-900 mb-2">Welcome to BrokerAI Co-Pilot v2.0</h2>
           <p className="text-slate-500 max-w-md mx-auto leading-relaxed">
               Your workspace has evolved. Use the sidebar to navigate between your saved leads, territory maps, and new analysis tools.
           </p>
       </div>
    </div>
  );
}
