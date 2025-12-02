'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { getFranchiseDetail } from '@/app/actions';
import { getFranchiseTerritories } from '../actions';
import Link from 'next/link';
import { 
    ArrowLeft, Map as MapIcon, FileText, Loader2, Info, ExternalLink, Building2, 
    Wallet, CheckCircle2, XCircle, Globe, Users, Briefcase, Award, GraduationCap, 
    Lightbulb, ArrowRightLeft, Calendar, TrendingUp, FileDown, MapPin, Star,
    DollarSign, Package, Percent, ShieldCheck, Flame, Plane, Network
} from 'lucide-react';
import FranchiseTerritoryMap from '@/components/FranchiseTerritoryMap';
import { useComparison } from '@/contexts/ComparisonContext';
import { ContentList } from '@/components/ContentList';
import type { 
    FranchiseDetail, MarketGrowthStatistics, IdealCandidateProfile, 
    SupportTrainingDetails, IndustryAward, FranchiseDocuments, 
    CommissionStructure, FranchisePackage 
} from '@/types';

export default function FranchiseDetailPage() {
    const params = useParams();
    const id = Number(params.id);

    const [activeTab, setActiveTab] = useState<'overview' | 'territories'>('overview');
    const [franchise, setFranchise] = useState<FranchiseDetail | null>(null);
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

                            {franchise.schedule_call_url && (
                                <a 
                                    href={normalizeWebsiteUrl(franchise.schedule_call_url)} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center px-4 py-2 bg-indigo-600 border border-indigo-600 rounded-lg text-sm font-medium text-white hover:bg-indigo-700 transition-colors"
                                >
                                    <Calendar className="w-4 h-4 mr-2" />
                                    Schedule a Call
                                </a>
                            )}

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
                                {franchise.rating && (
                                    <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 px-2 py-1 rounded-full text-sm font-medium border border-amber-100">
                                        <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                                        {franchise.rating}
                                    </span>
                                )}
                                {franchise.business_model_type && (
                                    <span className="bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wide border border-indigo-100">
                                        {franchise.business_model_type}
                                    </span>
                                )}
                                {franchise.family_brand && (
                                    <Link 
                                        href={`/family-brands/${franchise.family_brand.id}`}
                                        className="inline-flex items-center gap-1.5 bg-violet-50 text-violet-700 px-2.5 py-1 rounded-full text-xs font-semibold border border-violet-100 hover:bg-violet-100 transition-colors"
                                    >
                                        <Network className="w-3.5 h-3.5" />
                                        Part of {franchise.family_brand.name}
                                    </Link>
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
                                ${franchise.total_investment_min_usd?.toLocaleString() || '?'} - ${franchise.total_investment_max_usd?.toLocaleString() || '?'}
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
                        
                        {/* 1. Financial Dashboard - Enhanced */}
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

                                {/* Additional Financial Info */}
                                {(franchise.additional_fees || franchise.financial_assistance_details) && (
                                    <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {franchise.additional_fees && (
                                            <div>
                                                <div className="text-xs font-bold uppercase text-slate-400 mb-2">Additional Fees</div>
                                                <p className="text-sm text-slate-600">{franchise.additional_fees}</p>
                                            </div>
                                        )}
                                        {franchise.financial_assistance_details && (
                                            <div>
                                                <div className="text-xs font-bold uppercase text-slate-400 mb-2">Financial Assistance</div>
                                                <p className="text-sm text-slate-600">{franchise.financial_assistance_details}</p>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Badges */}
                                <div className="mt-6 flex flex-wrap gap-3 pt-6 border-t border-slate-100">
                                    {franchise.sba_approved && (
                                        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                            <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                                            SBA Approved
                                        </span>
                                    )}
                                    {franchise.sba_registered && (
                                        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-sky-50 text-sky-700 border border-sky-100">
                                            <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
                                            SBA Registered
                                        </span>
                                    )}
                                    {franchise.providing_earnings_guidance_item19 && (
                                        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-100">
                                            <TrendingUp className="w-3.5 h-3.5 mr-1.5" />
                                            Item 19 Earnings Guidance
                                        </span>
                                    )}
                                    {franchise.vetfran_member && (
                                        <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-100">
                                            <Award className="w-3.5 h-3.5 mr-1.5" />
                                            VetFran Member
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Franchise Packages (if multiple) */}
                        <FranchisePackagesCard packages={franchise.franchise_packages} />

                        {/* Commission Structure (for brokers) */}
                        <CommissionStructureCard commission={franchise.commission_structure} />

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
                            {franchise.vetfran_discount_details && (
                                <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-100">
                                    <div className="text-xs font-bold uppercase text-amber-600 mb-1">VetFran Discount</div>
                                    <p className="text-sm text-amber-800">{franchise.vetfran_discount_details}</p>
                                </div>
                            )}
                        </div>

                        {/* Market Insights Card */}
                        <MarketInsightsCard marketData={franchise.market_growth_statistics} />

                        {/* Industry Awards */}
                        <IndustryAwardsCard awards={franchise.industry_awards} />

                        {/* Territory Quick View */}
                        <TerritoryQuickViewCard 
                            hotRegions={franchise.hot_regions}
                            canadianReferrals={franchise.canadian_referrals}
                            internationalReferrals={franchise.international_referrals}
                            resalesAvailable={franchise.resales_available}
                            unavailableStates={franchise.unavailable_states}
                        />

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

                                {/* Documents & Resources */}
                                <DocumentsCard documents={franchise.documents} />
                            </div>

                            {/* Sidebar: Ideal Candidate & Training */}
                            <div className="space-y-8">
                                {/* Ideal Candidate - Enhanced */}
                                <IdealCandidateCard 
                                    profile={franchise.ideal_candidate_profile}
                                    profileText={franchise.ideal_candidate_profile_text}
                                />

                                {/* Support & Training - Enhanced */}
                                <SupportTrainingCard 
                                    details={franchise.support_training_details}
                                    legacyData={franchise.franchises_data}
                                />

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
                                        {franchise.last_updated_from_source && (
                                            <div>
                                                <dt className="text-xs uppercase text-slate-400 font-bold">Last Updated</dt>
                                                <dd className="font-medium text-slate-900">
                                                    {new Date(franchise.last_updated_from_source).toLocaleDateString()}
                                                </dd>
                                            </div>
                                        )}
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
                                <FranchiseTerritoryMap data={{
                                    ...territoryData,
                                    // Merge unavailable_states from franchise data as fallback
                                    // (territories API may not return it in production)
                                    unavailable_states: territoryData?.unavailable_states || franchise.unavailable_states
                                }} />
                            </div>
                        </div>
                    </div>
                )}
            </main>
        </div>
    );
}

// --- Helper Components ---

function normalizeWebsiteUrl(url: string): string {
    if (!url) return '';
    let normalized = url.trim().replace(/\s/g, '');
    if (!/^https?:\/\//i.test(normalized)) {
        return `https://${normalized}`;
    }
    return normalized;
}

function ModelBadge({ label, value }: { label: string; value?: boolean }) {
    if (!value) return null;
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
        return text.replace(/^"|"$/g, '');
    }
    return JSON.stringify(text);
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

// --- New Card Components ---

function FranchisePackagesCard({ packages }: { packages?: FranchisePackage[] }) {
    if (!packages || packages.length === 0) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <Package className="w-5 h-5 text-indigo-600" />
                <h2 className="font-bold text-slate-800">Franchise Packages</h2>
            </div>
            <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {packages.map((pkg, idx) => (
                        <div key={idx} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                            <h3 className="font-semibold text-slate-900 mb-2">{pkg.name}</h3>
                            <div className="space-y-1 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-slate-500">Franchise Fee</span>
                                    <span className="font-medium text-slate-900">${pkg.franchise_fee?.toLocaleString()}</span>
                                </div>
                                {pkg.total_investment_min && (
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Investment</span>
                                        <span className="font-medium text-slate-900">
                                            ${pkg.total_investment_min?.toLocaleString()}
                                            {pkg.total_investment_max && ` - $${pkg.total_investment_max.toLocaleString()}`}
                                        </span>
                                    </div>
                                )}
                                {pkg.territories_count && (
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Territories</span>
                                        <span className="font-medium text-slate-900">{pkg.territories_count}</span>
                                    </div>
                                )}
                            </div>
                            {pkg.description && (
                                <p className="mt-2 text-xs text-slate-500">{pkg.description}</p>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function CommissionStructureCard({ commission }: { commission?: CommissionStructure }) {
    if (!commission) return null;
    
    const hasData = commission.single_unit || commission.multi_unit || commission.resales || commission.area_master_developer;
    if (!hasData) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <Percent className="w-5 h-5 text-emerald-600" />
                <h2 className="font-bold text-slate-800">Commission Structure</h2>
                <span className="ml-auto text-xs text-slate-400">For Brokers</span>
            </div>
            <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {commission.single_unit && (
                        <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100">
                            <h3 className="text-xs font-bold uppercase text-emerald-600 mb-1">Single Unit</h3>
                            {commission.single_unit.amount && (
                                <div className="text-xl font-bold text-emerald-700">${commission.single_unit.amount.toLocaleString()}</div>
                            )}
                            <p className="text-xs text-emerald-600 mt-1">{commission.single_unit.description}</p>
                        </div>
                    )}
                    {commission.multi_unit && (
                        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                            <h3 className="text-xs font-bold uppercase text-blue-600 mb-1">Multi Unit</h3>
                            {commission.multi_unit.percentage && (
                                <div className="text-xl font-bold text-blue-700">{commission.multi_unit.percentage}%</div>
                            )}
                            <p className="text-xs text-blue-600 mt-1">{commission.multi_unit.description}</p>
                        </div>
                    )}
                    {commission.resales && (
                        <div className="p-4 bg-amber-50 rounded-lg border border-amber-100">
                            <h3 className="text-xs font-bold uppercase text-amber-600 mb-1">Resales</h3>
                            {commission.resales.percentage && (
                                <div className="text-xl font-bold text-amber-700">{commission.resales.percentage}%</div>
                            )}
                            <p className="text-xs text-amber-600 mt-1">{commission.resales.description}</p>
                        </div>
                    )}
                    {commission.area_master_developer && (
                        <div className="p-4 bg-purple-50 rounded-lg border border-purple-100">
                            <h3 className="text-xs font-bold uppercase text-purple-600 mb-1">Area Developer</h3>
                            {commission.area_master_developer.amount && (
                                <div className="text-xl font-bold text-purple-700">${commission.area_master_developer.amount.toLocaleString()}</div>
                            )}
                            <p className="text-xs text-purple-600 mt-1">{commission.area_master_developer.description}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function MarketInsightsCard({ marketData }: { marketData?: MarketGrowthStatistics }) {
    if (!marketData) return null;
    
    const hasData = marketData.market_size || marketData.cagr || marketData.demographics || marketData.recession_resistance;
    if (!hasData) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-600" />
                <h2 className="font-bold text-slate-800">Market Insights</h2>
            </div>
            <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {marketData.market_size && (
                        <div>
                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">Market Size</div>
                            <div className="text-xl font-bold text-slate-900">{marketData.market_size}</div>
                        </div>
                    )}
                    {marketData.cagr && (
                        <div>
                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">CAGR</div>
                            <div className="text-xl font-bold text-emerald-600">{marketData.cagr}</div>
                            {marketData.growth_period && (
                                <p className="text-xs text-slate-400">{marketData.growth_period}</p>
                            )}
                        </div>
                    )}
                    {marketData.recession_resistance && (
                        <div>
                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">Recession Resistance</div>
                            <p className="text-sm text-slate-700">{marketData.recession_resistance}</p>
                        </div>
                    )}
                    {marketData.demographics && (
                        <div className="md:col-span-2 lg:col-span-1">
                            <div className="text-xs font-bold uppercase text-slate-400 mb-1">Demographics</div>
                            <p className="text-sm text-slate-700">{marketData.demographics}</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function IndustryAwardsCard({ awards }: { awards?: IndustryAward[] }) {
    if (!awards || awards.length === 0) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <Award className="w-5 h-5 text-amber-500" />
                <h2 className="font-bold text-slate-800">Industry Awards & Recognition</h2>
            </div>
            <div className="p-6">
                <div className="flex flex-wrap gap-3">
                    {awards.map((award, idx) => (
                        <div 
                            key={idx} 
                            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg"
                        >
                            <Award className="w-4 h-4 text-amber-500" />
                            <div>
                                <div className="text-sm font-medium text-amber-900">
                                    {award.award_name || award.source}
                                </div>
                                <div className="text-xs text-amber-600">
                                    {award.source} • {award.year}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function TerritoryQuickViewCard({ 
    hotRegions, 
    canadianReferrals, 
    internationalReferrals,
    resalesAvailable,
    unavailableStates
}: { 
    hotRegions?: string[]; 
    canadianReferrals?: boolean; 
    internationalReferrals?: boolean;
    resalesAvailable?: boolean;
    unavailableStates?: string[];
}) {
    const hasData = (hotRegions && hotRegions.length > 0) || canadianReferrals || internationalReferrals || resalesAvailable;
    if (!hasData) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-indigo-600" />
                <h2 className="font-bold text-slate-800">Territory Overview</h2>
            </div>
            <div className="p-6">
                <div className="flex flex-wrap gap-3 mb-4">
                    {canadianReferrals && (
                        <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 border border-red-100 text-red-700">
                            <Plane className="w-3.5 h-3.5 mr-1.5" />
                            Canadian Referrals Accepted
                        </span>
                    )}
                    {internationalReferrals && (
                        <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-50 border border-blue-100 text-blue-700">
                            <Globe className="w-3.5 h-3.5 mr-1.5" />
                            International Referrals
                        </span>
                    )}
                    {resalesAvailable && (
                        <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-50 border border-emerald-100 text-emerald-700">
                            <DollarSign className="w-3.5 h-3.5 mr-1.5" />
                            Resales Available
                        </span>
                    )}
                </div>
                
                {hotRegions && hotRegions.length > 0 && (
                    <div className="mb-4">
                        <div className="text-xs font-bold uppercase text-slate-400 mb-2 flex items-center gap-1">
                            <Flame className="w-3.5 h-3.5 text-orange-500" />
                            Hot Markets
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {hotRegions.map((region, idx) => (
                                <span 
                                    key={idx}
                                    className="px-2 py-1 bg-orange-50 text-orange-700 text-xs font-medium rounded border border-orange-100"
                                >
                                    {region}
                                </span>
                            ))}
                        </div>
                    </div>
                )}

                {unavailableStates && unavailableStates.length > 0 && (
                    <div>
                        <div className="text-xs font-bold uppercase text-slate-400 mb-2">Not Available In</div>
                        <div className="flex flex-wrap gap-1">
                            {unavailableStates.map((state, idx) => (
                                <span 
                                    key={idx}
                                    className="px-2 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded"
                                >
                                    {state}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function IdealCandidateCard({ 
    profile, 
    profileText 
}: { 
    profile?: IdealCandidateProfile; 
    profileText?: string;
}) {
    // Use structured profile if available, otherwise fall back to text
    const hasStructured = profile && (profile.skills?.length || profile.personality_traits?.length || profile.role_of_owner);

    return (
        <div className="bg-indigo-50 rounded-xl border border-indigo-100 p-6">
            <h2 className="text-lg font-bold text-indigo-900 mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Ideal Candidate
            </h2>
            
            {hasStructured ? (
                <div className="space-y-4">
                    {profile.skills && profile.skills.length > 0 && (
                        <div>
                            <div className="text-xs font-bold uppercase text-indigo-600 mb-2">Skills</div>
                            <div className="flex flex-wrap gap-1">
                                {profile.skills.map((skill, idx) => (
                                    <span key={idx} className="px-2 py-1 bg-white text-indigo-700 text-xs rounded border border-indigo-200">
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                    {profile.personality_traits && profile.personality_traits.length > 0 && (
                        <div>
                            <div className="text-xs font-bold uppercase text-indigo-600 mb-2">Traits</div>
                            <div className="flex flex-wrap gap-1">
                                {profile.personality_traits.map((trait, idx) => (
                                    <span key={idx} className="px-2 py-1 bg-white text-indigo-700 text-xs rounded border border-indigo-200">
                                        {trait}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                    {profile.role_of_owner && (
                        <div>
                            <div className="text-xs font-bold uppercase text-indigo-600 mb-2">Role of Owner</div>
                            <p className="text-sm text-indigo-800">{profile.role_of_owner}</p>
                        </div>
                    )}
                </div>
            ) : (
                <div className="text-indigo-800/80 text-sm">
                    <ContentList content={profileText} bulletClassName="bg-indigo-400" />
                </div>
            )}
        </div>
    );
}

function SupportTrainingCard({ 
    details, 
    legacyData 
}: { 
    details?: SupportTrainingDetails; 
    legacyData?: any;
}) {
    // Use structured details if available
    if (details) {
        const hasData = details.program_description || details.cost_included !== undefined || 
                       details.mentor_available !== undefined || details.site_selection_assistance !== undefined;
        
        if (hasData) {
            return (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                    <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                        <GraduationCap className="w-5 h-5 text-indigo-600" />
                        Support & Training
                    </h2>
                    <div className="space-y-4">
                        {details.program_description && (
                            <p className="text-sm text-slate-600">{details.program_description}</p>
                        )}
                        
                        <div className="grid grid-cols-2 gap-3">
                            <SupportBadge label="Training Cost Included" value={details.cost_included} />
                            <SupportBadge label="Lodging/Airfare Included" value={details.lodging_airfare_included} />
                            <SupportBadge label="Site Selection Help" value={details.site_selection_assistance} />
                            <SupportBadge label="Lease Negotiation Help" value={details.lease_negotiation_assistance} />
                            <SupportBadge label="Mentor Available" value={details.mentor_available} />
                        </div>

                        {details.mentoring_length && (
                            <div>
                                <div className="text-xs font-bold uppercase text-slate-400 mb-1">Mentoring Duration</div>
                                <p className="text-sm text-slate-700">{details.mentoring_length}</p>
                            </div>
                        )}

                        {details.cost_details && (
                            <div>
                                <div className="text-xs font-bold uppercase text-slate-400 mb-1">Cost Details</div>
                                <p className="text-sm text-slate-600">{details.cost_details}</p>
                            </div>
                        )}
                    </div>
                </div>
            );
        }
    }

    // Fallback to legacy data
    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-indigo-600" />
                Support & Training
            </h2>
            <div className="text-slate-600 text-sm space-y-3">
                <LegacyTrainingDetails data={legacyData} />
            </div>
        </div>
    );
}

function SupportBadge({ label, value }: { label: string; value?: boolean }) {
    if (value === undefined) return null;
    
    return (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${
            value ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-50 text-slate-500'
        }`}>
            {value ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
            ) : (
                <XCircle className="w-3.5 h-3.5" />
            )}
            {label}
        </div>
    );
}

function LegacyTrainingDetails({ data }: { data: any }) {
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

function DocumentsCard({ documents }: { documents?: FranchiseDocuments }) {
    if (!documents) return null;
    
    const hasDocuments = documents.regular?.length || documents.client_focused?.length || 
                        documents.recent_emails?.length || documents.magazine_articles?.length;
    if (!hasDocuments) return null;

    return (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                <FileDown className="w-5 h-5 text-indigo-600" />
                Documents & Resources
            </h2>
            <div className="space-y-4">
                {documents.regular && documents.regular.length > 0 && (
                    <DocumentSection title="Resources" items={documents.regular} />
                )}
                {documents.client_focused && documents.client_focused.length > 0 && (
                    <DocumentSection title="Client Resources" items={documents.client_focused} />
                )}
                {documents.recent_emails && documents.recent_emails.length > 0 && (
                    <DocumentSection title="Recent Communications" items={documents.recent_emails} />
                )}
                {documents.magazine_articles && documents.magazine_articles.length > 0 && (
                    <DocumentSection title="Magazine Articles" items={documents.magazine_articles} />
                )}
            </div>
        </div>
    );
}

function DocumentSection({ title, items }: { title: string; items: string[] }) {
    return (
        <div>
            <div className="text-xs font-bold uppercase text-slate-400 mb-2">{title}</div>
            <div className="flex flex-wrap gap-2">
                {items.map((item, idx) => {
                    const isUrl = item.startsWith('http');
                    const displayName = isUrl ? extractFileName(item) : item;
                    
                    return isUrl ? (
                        <a
                            key={idx}
                            href={item}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs rounded-lg border border-slate-200 transition-colors"
                        >
                            <ExternalLink className="w-3 h-3" />
                            {displayName}
                        </a>
                    ) : (
                        <span
                            key={idx}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 text-slate-700 text-xs rounded-lg border border-slate-200"
                        >
                            <FileDown className="w-3 h-3" />
                            {displayName}
                        </span>
                    );
                })}
            </div>
        </div>
    );
}

function extractFileName(url: string): string {
    try {
        const pathname = new URL(url).pathname;
        const filename = pathname.split('/').pop() || url;
        // Clean up and truncate
        return filename.length > 40 ? filename.substring(0, 37) + '...' : filename;
    } catch {
        return url.length > 40 ? url.substring(0, 37) + '...' : url;
    }
}
