'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { 
  ArrowLeft, Network, Building, Globe, Mail, Phone, User, 
  Loader2, DollarSign, ArrowRight, ExternalLink, Calendar
} from 'lucide-react';
import { getFamilyBrandDetail } from '@/app/franchises/actions';
import { FamilyBrandDetail } from '@/types';

export default function FamilyBrandDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  
  const [familyBrand, setFamilyBrand] = useState<FamilyBrandDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getFamilyBrandDetail(id);
        setFamilyBrand(data);
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
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-violet-600" />
      </div>
    );
  }

  if (!familyBrand) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-900">
        <Network className="w-16 h-16 text-slate-300 dark:text-slate-600 mb-4" />
        <h1 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">Family Brand Not Found</h1>
        <p className="text-slate-500 dark:text-slate-400 mb-6">The family brand you're looking for doesn't exist.</p>
        <Link 
          href="/family-brands" 
          className="inline-flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Family Brands
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 pb-24">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-8 py-6">
        <div className="max-w-6xl mx-auto">
          <Link 
            href="/family-brands" 
            className="inline-flex items-center text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Family Brands
          </Link>
          
          <div className="flex flex-col md:flex-row gap-6 items-start">
            {/* Logo */}
            <div className="flex-shrink-0 w-24 h-24 bg-slate-100 dark:bg-slate-700 rounded-xl overflow-hidden flex items-center justify-center border border-slate-200 dark:border-slate-600">
              {familyBrand.logo_url ? (
                <Image
                  src={familyBrand.logo_url}
                  alt={familyBrand.name}
                  width={96}
                  height={96}
                  className="object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              ) : (
                <Network className="w-12 h-12 text-slate-400 dark:text-slate-500" />
              )}
            </div>
            
            {/* Info */}
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{familyBrand.name}</h1>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300">
                  <Network className="w-3.5 h-3.5" />
                  Family Brand
                </span>
              </div>
              
              {/* Contact & Website Row */}
              <div className="flex flex-wrap gap-4 mt-4">
                {familyBrand.website_url && (
                  <a
                    href={familyBrand.website_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-violet-600 text-white rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors"
                  >
                    <Globe className="w-4 h-4" />
                    Visit Website
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
                
                {familyBrand.contact_name && (
                  <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300">
                    <User className="w-4 h-4 text-slate-500" />
                    {familyBrand.contact_name}
                  </div>
                )}
                
                {familyBrand.contact_phone && (
                  <a 
                    href={`tel:${familyBrand.contact_phone}`}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                  >
                    <Phone className="w-4 h-4 text-slate-500" />
                    {familyBrand.contact_phone}
                  </a>
                )}
                
                {familyBrand.contact_email && (
                  <a 
                    href={`mailto:${familyBrand.contact_email}`}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-700 rounded-lg text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                  >
                    <Mail className="w-4 h-4 text-slate-500" />
                    {familyBrand.contact_email}
                  </a>
                )}
              </div>
            </div>
            
            {/* Stats */}
            <div className="text-right">
              <div className="text-sm text-slate-500 dark:text-slate-400 mb-1">Representing Brands</div>
              <div className="text-4xl font-bold text-indigo-600 dark:text-indigo-400">
                {familyBrand.franchise_count || 0}
              </div>
              <div className="text-xs text-slate-400 dark:text-slate-500 mt-1">Franchises</div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-8">
        {/* Representing Brands Section */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-6">
            <Building className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Representing Franchise Brands</h2>
          </div>
          
          {familyBrand.franchises && familyBrand.franchises.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {familyBrand.franchises.map((franchise) => (
                <Link
                  key={franchise.id}
                  href={`/franchises/${franchise.id}`}
                  className="group bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-5 hover:border-indigo-300 dark:hover:border-indigo-600 hover:shadow-md transition-all"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors truncate">
                        {franchise.franchise_name}
                      </h3>
                      {franchise.primary_category && (
                        <span className="inline-block mt-1 px-2 py-0.5 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs rounded">
                          {franchise.primary_category}
                        </span>
                      )}
                    </div>
                    <div className="flex-shrink-0 bg-slate-50 dark:bg-slate-700 p-2 rounded-lg group-hover:bg-indigo-50 dark:group-hover:bg-indigo-900/30 transition-colors ml-3">
                      <ArrowRight className="w-4 h-4 text-slate-400 dark:text-slate-500 group-hover:text-indigo-500 dark:group-hover:text-indigo-400" />
                    </div>
                  </div>
                  
                  {franchise.description_text && (
                    <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 mb-3">
                      {franchise.description_text}
                    </p>
                  )}
                  
                  {franchise.total_investment_min_usd && (
                    <div className="flex items-center gap-1.5 text-sm text-emerald-600 dark:text-emerald-400">
                      <DollarSign className="w-4 h-4" />
                      <span className="font-medium">
                        ${franchise.total_investment_min_usd.toLocaleString()}
                      </span>
                      <span className="text-slate-400 dark:text-slate-500">Min Investment</span>
                    </div>
                  )}
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 border-dashed">
              <Building className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">No franchises linked to this family brand yet.</p>
            </div>
          )}
        </div>
        
        {/* Last Updated */}
        {familyBrand.last_updated_from_source && (
          <div className="flex items-center gap-2 text-sm text-slate-400 dark:text-slate-500">
            <Calendar className="w-4 h-4" />
            Last updated: {new Date(familyBrand.last_updated_from_source).toLocaleDateString()}
          </div>
        )}
      </main>
    </div>
  );
}











