'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getFranchiseDetail } from '@/app/actions';
import { getFranchiseTerritories } from '../actions';
import Link from 'next/link';
import { ArrowLeft, Map as MapIcon, FileText, Loader2, Info, ExternalLink, Building2, Wallet, CheckCircle2, XCircle, Globe, Users, Briefcase, Award, GraduationCap, Lightbulb, ArrowRightLeft } from 'lucide-react';
import { MatchDetailModal } from '@/components/MatchDetailModal';
import FranchiseTerritoryMap from '@/components/FranchiseTerritoryMap';
import { useComparison } from '@/contexts/ComparisonContext';
import { ContentList } from '@/components/ContentList';

export default function FranchiseDetailPage() {
    const params = useParams();
    const id = Number(params.id);

    const [activeTab, setActiveTab] = useState<'overview' | 'territories'>('overview');
    const [franchise, setFranchise] = useState<any>(null);
    const [territoryData, setTerritoryData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const { isInComparison, toggleComparison } = useComparison();
    const inComparison = isInComparison(String(id));

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
        <div className="min-h-screen bg-slate-50 flex flex-col pb-24">
            {/* Header */}
            <header className="bg-white border-b border-slate-200 px-8 py-6">
                <div className="max-w-7xl mx-auto">
                    <div className="flex justify-between items-start mb-6">
                        <Link href="/franchises" className="inline-flex items-center text-slate-500 hover:text-slate-900 transition-colors">
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Back to Directory
                        </Link>
                        <div className="flex gap-3">
                            <button
                                onClick={() => toggleComparison(String(id))}
                                className={`inline-flex items-center px-4 py-2 border rounded-lg text-sm font-medium transition-colors ${
                                    inComparison
                                    ? 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100'
                                    : 'bg-white border-slate-300 text-slate-700 hover:bg-slate-50'
                                }`}
                            >
                                <ArrowRightLeft className={`w-4 h-4 mr-2 ${inComparison ? 'text-indigo-600' : 'text-slate-500'}`} />
                                {inComparison ? 'In Comparison' : 'Add to Comparison'}
                            </button>

                            {franchise.website_url && (
                                <a 
                                    href={normalizeWebsiteUrl(franchise.website_url)} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-4 py-2 bg-white border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
                                >
                                    <Globe className="w-4 h-4 mr-2 text-slate-500" />
                                    Visit Website
                                </a>
                            )}
                        </div>
                    </div>
                    
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-3xl font-bold text-slate-900">{franchise.franchise_name}</h1>
                                {franchise.business_model_type && (
                                    <span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border border-indigo-100">
                                        {franchise.business_model_type}
                                    </span>
                                )}
                            </div>
                            
                            <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-500">
                                <span className="bg-slate-100 px-2.5 py-1 rounded text-slate-700 font-medium">
                                    {Array.isArray(franchise.primary_category) ? franchise.primary_category[0] : franchise.primary_category}
                                </span>
                                {franchise.founded_year && (
                                    <span className="flex items-center">
                                        <span className="w-1 h-1 bg-slate-300 rounded-full mr-2"></span>
                                        Founded {franchise.founded_year}
                                    </span>
                                )}
                                {franchise.corporate_address && (
                                    <span className="flex items-center" title="Corporate Address">
                                        <span className="w-1 h-1 bg-slate-300 rounded-full mr-2"></span>
                                        <Building2 className="w-3.5 h-3.5 mr-1.5" />
                                        {franchise.corporate_address}
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-slate-500 mb-1">Total Investment</div>
                            <div className="text-3xl font-bold text-emerald-600">
                                ${franchise.total_investment_min_usd?.toLocaleString()} - ${franchise.total_investment_max_usd?.toLocaleString()}
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
                    <div className="space-y-8">
                        
                        {/* 1. Financial Dashboard */}
                        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                                <Wallet className="w-5 h-5 text-emerald-600" />
                                <h2 className="font-bold text-slate-800">Financial Requirements & Investment</h2>
                            </div>
                            <div className="p-6">
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                                    <div className="md:col-span-1 p-4 bg-emerald-50 rounded-xl border border-emerald-100 flex flex-col justify-center">
                                        <div className="text-xs font-bold uppercase text-emerald-600 mb-1">Liquid Capital Req.</div>
                                        <div className="text-2xl font-bold text-emerald-700">
                                            ${franchise.required_cash_investment_usd?.toLocaleString() || 'N/A'}
                                        </div>
                                        <p className="text-xs text-emerald-600/80 mt-1">Cash required</p>
                                    </div>
                                    <div className="md:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
                                        <div>
                                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">Net Worth</div>
                                            <div className="font-semibold text-xl text-slate-900">
                                                ${franchise.required_net_worth_usd?.toLocaleString() || 'N/A'}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">Franchise Fee</div>
                                            <div className="font-semibold text-xl text-slate-900">
                                                ${franchise.franchise_fee_usd?.toLocaleString() || 'N/A'}
                                            </div>
                                        </div>
                                        <div>
                                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">Royalties</div>
                                            <div className="font-medium text-slate-900 text-sm">
                                                {franchise.royalty_details_text || 'See FDD'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="mt-6 flex flex-wrap gap-4 pt-6 border-t border-slate-100">
                                    {franchise.sba_approved && (
                                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                                            SBA Approved
                                        </span>
                                    )}
                                    {franchise.vetfran_member && (
                                        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
                                            <Award className="w-3.5 h-3.5 mr-1.5" />
                                            VetFran Member
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* 2. Operations & Business Model */}
                        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                <Briefcase className="w-5 h-5 text-indigo-600" />
                                Operations & Business Model
                            </h2>
                            <div className="flex flex-wrap gap-3">
                                <ModelBadge label="Home Based" value={franchise.is_home_based} />
                                <ModelBadge label="Semi-Absentee" value={franchise.allows_semi_absentee} />
                                <ModelBadge label="Absentee Ownership" value={franchise.allows_absentee} />
                                <ModelBadge label="Master Franchise" value={franchise.master_franchise_opportunity} />
                                <ModelBadge label="E2 Visa Friendly" value={franchise.e2_visa_friendly} />
                            </div>
                        </div>

                        {/* 3. Description & Why Franchise */}
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            <div className="lg:col-span-2 space-y-8">
                                {/* Description */}
                                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8">
                                    <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                        <Info className="w-5 h-5 text-indigo-600" />
                                        About {franchise.franchise_name}
                                    </h2>
                                    <div className="prose max-w-none text-slate-600 text-sm leading-relaxed whitespace-pre-line">
                                        {parseTextContent(franchise.description_text)}
                                    </div>
                                </div>

                                {/* Why Choose Us */}
                                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8">
                                    <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                        <Lightbulb className="w-5 h-5 text-amber-500" />
                                        Why {franchise.franchise_name}?
                                    </h2>
                                    <div className="prose max-w-none text-slate-600 text-sm">
                                        <ContentList content={franchise.why_franchise_summary} />
                                    </div>
                                </div>
                            </div>

                            {/* Sidebar: Ideal Candidate & Training */}
                            <div className="space-y-8">
                                {/* Ideal Candidate */}
                                <div className="bg-indigo-50 rounded-xl border border-indigo-100 p-6">
                                    <h2 className="text-lg font-bold text-indigo-900 mb-4 flex items-center gap-2">
                                        <Users className="w-5 h-5" />
                                        Ideal Candidate
                                    </h2>
                                    <div className="text-indigo-800/80 text-sm">
                                        <ContentList content={franchise.ideal_candidate_profile_text} />
                                    </div>
                                </div>

                                {/* Support & Training */}
                                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                                    <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                        <GraduationCap className="w-5 h-5 text-indigo-600" />
                                        Support & Training
                                    </h2>
                                    <div className="text-slate-600 text-sm space-y-3">
                                        <TrainingDetails data={franchise.franchises_data} />
                                    </div>
                                </div>

                                {/* Company Info */}
                                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                                    <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                                        <Building2 className="w-5 h-5 text-slate-500" />
                                        Company Details
                                    </h2>
                                    <dl className="space-y-3 text-sm">
                                        <div>
                                            <dt className="text-xs uppercase text-slate-400 font-bold">Founded</dt>
                                            <dd className="font-medium text-slate-900">{franchise.founded_year || 'N/A'}</dd>
                                        </div>
                                        <div>
                                            <dt className="text-xs uppercase text-slate-400 font-bold">Franchised Since</dt>
                                            <dd className="font-medium text-slate-900">{franchise.franchised_year || 'N/A'}</dd>
                                        </div>
                                        <div>
                                            <dt className="text-xs uppercase text-slate-400 font-bold">Headquarters</dt>
                                            <dd className="font-medium text-slate-900">{franchise.corporate_address || 'N/A'}</dd>
                                        </div>
                                    </dl>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6">
                         {/* Territory Overview Header */}
                         <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex justify-between items-center">
                            <div>
                                <h2 className="text-lg font-bold text-slate-900">Territory Availability Map</h2>
                                <p className="text-slate-500 text-sm">Visualizing {territoryData?.territory_count || 0} recent availability checks</p>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-medium text-slate-600">Unavailable States</div>
                                <div className="text-xs text-slate-400 max-w-xs mt-1">
                                    {parseUnavailableStates(franchise.unavailable_states)}
                                </div>
                            </div>
                         </div>

                         <div className="h-[600px] bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex">
                            {/* Interactive Map Component */}
                            <div className="flex-1 relative">
                                <FranchiseTerritoryMap data={territoryData} />
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

// --- Helper Components & Functions ---

function normalizeWebsiteUrl(url: string): string {
    if (!url) return '';
    let normalized = url.trim();
    // Remove any whitespace
    normalized = normalized.replace(/\s/g, '');
    
    // Check if it starts with http:// or https://
    if (!/^https?:\/\//i.test(normalized)) {
        return `https://${normalized}`;
    }
    return normalized;
}

function ModelBadge({ label, value }: { label: string; value: boolean }) {
    if (!value) return null;
    
    // Determine color based on type (simple logic for now)
    const isOperations = label.includes('Absentee') || label.includes('Home');
    const bgClass = isOperations ? 'bg-purple-50 border-purple-100 text-purple-700' : 'bg-blue-50 border-blue-100 text-blue-700';
    
    return (
        <span className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border ${bgClass}`}>
            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 opacity-70" />
            {label}
        </span>
    );
}

function parseTextContent(text: any): string {
    if (!text) return 'No description available.';
    if (typeof text === 'string') {
        // Remove outer quotes if they exist (common artifact)
        return text.replace(/^"|"$/g, '');
    }
    return JSON.stringify(text);
}

// ContentList is now imported from @/components/ContentList

function TrainingDetails({ data }: { data: any }) {
    if (!data) return <p className="text-slate-400 italic">No details available.</p>;
    
    let supportData = null;
    try {
        const parsed = typeof data === 'string' ? JSON.parse(data) : data;
        supportData = parsed.support_and_training;
    } catch {
        return <p className="text-slate-400 italic">No details available.</p>;
    }

    if (!supportData || Object.keys(supportData).length === 0) {
         return <p className="text-slate-400 italic">No details available.</p>;
    }

    return (
         <dl className="space-y-3">
            {Object.entries(supportData).map(([key, value]) => (
                <div key={key}>
                    <dt className="text-xs uppercase text-slate-400 font-bold mb-0.5">
                        {key.replace(/_/g, ' ')}
                    </dt>
                    <dd className="font-medium text-slate-900">
                        {String(value)}
                    </dd>
                </div>
            ))}
        </dl>
    );
}

function parseUnavailableStates(data: any): string {
    if (!data) return 'None specified';
    try {
        const states = typeof data === 'string' ? JSON.parse(data) : data;
        if (Array.isArray(states) && states.length > 0) {
            return states.join(', ');
        }
    } catch {
        return String(data);
    }
    return 'None specified';
}
