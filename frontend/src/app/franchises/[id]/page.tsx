'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getFranchiseDetail } from '@/app/actions';
import { getFranchiseTerritories } from '../actions';
import Link from 'next/link';
import { ArrowLeft, Map as MapIcon, FileText, Loader2, Info } from 'lucide-react';
import { MatchDetailModal } from '@/components/MatchDetailModal'; // We'll reuse parts of this logic or just the view
import FranchiseTerritoryMap from '@/components/FranchiseTerritoryMap'; // New component

export default function FranchiseDetailPage() {
    const params = useParams();
    const id = Number(params.id);

    const [activeTab, setActiveTab] = useState<'overview' | 'territories'>('overview');
    const [franchise, setFranchise] = useState<any>(null);
    const [territoryData, setTerritoryData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function load() {
            try {
                const [fData, tData] = await Promise.all([
                    getFranchiseDetail(id),
                    getFranchiseTerritories(id)
                ]);
                setFranchise(fData);
                setTerritoryData(tData);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        }
        if (id) load();
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
        );
    }

    if (!franchise) return <div>Franchise not found</div>;

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 px-8 py-6">
                <div className="max-w-7xl mx-auto">
                    <Link href="/franchises" className="inline-flex items-center text-slate-500 hover:text-slate-900 mb-6 transition-colors">
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Directory
                    </Link>
                    
                    <div className="flex justify-between items-end">
                        <div>
                            <h1 className="text-3xl font-bold text-slate-900 mb-2">{franchise.franchise_name}</h1>
                            <div className="flex items-center gap-4 text-sm text-slate-500">
                                <span className="bg-slate-100 px-2 py-1 rounded text-slate-700 font-medium">
                                    {franchise.primary_category}
                                </span>
                                <span>Founded {franchise.founded_year}</span>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-slate-500 mb-1">Min Investment</div>
                            <div className="text-2xl font-bold text-emerald-600">
                                ${franchise.total_investment_min_usd?.toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Tabs */}
            <div className="bg-white border-b border-slate-200 px-8 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto flex gap-8">
                    <button
                        onClick={() => setActiveTab('overview')}
                        className={`py-4 px-2 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
                            activeTab === 'overview' 
                                ? 'border-indigo-600 text-indigo-600' 
                                : 'border-transparent text-slate-500 hover:text-slate-700'
                        }`}
                    >
                        <FileText className="w-4 h-4" />
                        FDD Overview
                    </button>
                    <button
                        onClick={() => setActiveTab('territories')}
                        className={`py-4 px-2 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
                            activeTab === 'territories' 
                                ? 'border-indigo-600 text-indigo-600' 
                                : 'border-transparent text-slate-500 hover:text-slate-700'
                        }`}
                    >
                        <MapIcon className="w-4 h-4" />
                        Territory Availability
                        <span className="bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded-full text-xs">
                            {territoryData?.territory_count || 0}
                        </span>
                    </button>
                </div>
            </div>

            {/* Content */}
            <main className="flex-1 max-w-7xl mx-auto w-full p-8">
                {activeTab === 'overview' ? (
                    <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm">
                         {/* We can render the same content as MatchDetailModal here but inline */}
                         <div className="prose max-w-none text-slate-600">
                            <h3 className="text-lg font-bold text-slate-900 mb-4">Description</h3>
                            <p className="whitespace-pre-line mb-8">
                                {typeof franchise.description_text === 'string' 
                                    ? franchise.description_text.replace(/^"|"$/g, '') 
                                    : 'No description available.'}
                            </p>
                            
                            <div className="grid grid-cols-3 gap-8 border-t border-slate-100 pt-8">
                                <div>
                                    <div className="text-xs font-bold uppercase text-slate-400 mb-1">Liquid Capital</div>
                                    <div className="font-semibold text-lg text-slate-900">
                                        ${franchise.required_cash_investment_usd?.toLocaleString() || 'N/A'}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs font-bold uppercase text-slate-400 mb-1">Net Worth</div>
                                    <div className="font-semibold text-lg text-slate-900">
                                        ${franchise.required_net_worth_usd?.toLocaleString() || 'N/A'}
                                    </div>
                                </div>
                                <div>
                                    <div className="text-xs font-bold uppercase text-slate-400 mb-1">Franchise Fee</div>
                                    <div className="font-semibold text-lg text-slate-900">
                                        ${franchise.franchise_fee_usd?.toLocaleString() || 'N/A'}
                                    </div>
                                </div>
                            </div>
                         </div>
                    </div>
                ) : (
                    <div className="h-[600px] bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex">
                        {/* Interactive Map Component */}
                        <div className="flex-1 relative">
                            <FranchiseTerritoryMap data={territoryData} />
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

