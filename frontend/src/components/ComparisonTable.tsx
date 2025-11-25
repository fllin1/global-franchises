import React, { useState, useMemo, useRef } from 'react';
import { ComparisonItem, ComparisonResponse, Lead } from '../types';
import { Save, ArrowLeft, UserPlus, Check, AlertTriangle, X, MapPin, Wallet, Tag, FileDown } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { saveLeadComparisonAnalysis } from '@/app/actions';
import { ContentList } from './ContentList';

interface ComparisonTableProps {
  data: ComparisonResponse;
  leads?: Lead[]; // Optional list of leads for assignment
  initialLeadId?: number;
  onClose: () => void;
}

export default function ComparisonTable({ data, leads = [], initialLeadId, onClose }: ComparisonTableProps) {
  const { items } = data;
  const router = useRouter();
  
  const [selectedLeadId, setSelectedLeadId] = useState<number | undefined>(initialLeadId);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [showMisfits, setShowMisfits] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  
  const tableRef = useRef<HTMLDivElement>(null);

  // Get full selected lead object
  const selectedLead = useMemo(() => 
    leads.find(l => l.id === selectedLeadId), 
    [selectedLeadId, leads]
  );

  // PDF Export function
  const handleExportPDF = async () => {
    if (!tableRef.current || isExporting) return;
    
    // Ensure we're in the browser
    if (typeof window === 'undefined') {
      console.error('PDF export is only available in browser');
      return;
    }
    
    setIsExporting(true);
    
    try {
      // Dynamic import to avoid SSR issues
      const html2pdfModule = await import('html2pdf.js');
      const html2pdf = html2pdfModule.default;
      
      if (!html2pdf) {
        throw new Error('html2pdf module not loaded correctly');
      }
      
      const element = tableRef.current;
      const leadName = selectedLead?.candidate_name || 'Comparison';
      const filename = `${leadName.replace(/[^a-zA-Z0-9]/g, '_')}_Franchise_Matrix_${new Date().toISOString().split('T')[0]}.pdf`;
      
      const opt = {
        margin: [0.3, 0.3, 0.3, 0.3],
        filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
          scale: 2, 
          useCORS: true,
          logging: false,
          allowTaint: true,
          scrollX: 0,
          scrollY: 0,
          backgroundColor: '#ffffff'
        },
        jsPDF: { 
          unit: 'in', 
          format: 'letter', 
          orientation: 'landscape' 
        },
        pagebreak: { mode: ['css', 'legacy'] }
      };
      
      // Clone element for PDF export
      const clonedElement = element.cloneNode(true) as HTMLElement;
      
      // Create a wrapper with forced light mode and explicit colors
      const wrapper = document.createElement('div');
      wrapper.style.cssText = `
        position: absolute;
        left: -9999px;
        top: 0;
        width: ${element.offsetWidth}px;
        background: #ffffff;
        color-scheme: light;
      `;
      
      // Force light mode colors - comprehensive CSS reset for html2canvas compatibility
      // html2canvas doesn't support modern CSS color functions like lab(), oklch()
      const styleOverride = document.createElement('style');
      styleOverride.textContent = `
        * {
          color-scheme: light !important;
          --background: #ffffff !important;
          --foreground: #1f2937 !important;
          --color-background: #ffffff !important;
          --color-foreground: #1f2937 !important;
        }
        
        /* Force explicit colors on all elements to avoid lab()/oklch() */
        .bg-white, [class*="bg-white"] { background-color: #ffffff !important; }
        .bg-slate-50, [class*="bg-slate-50"] { background-color: #f8fafc !important; }
        .bg-slate-100, [class*="bg-slate-100"] { background-color: #f1f5f9 !important; }
        .bg-slate-800, [class*="bg-slate-800"] { background-color: #1e293b !important; }
        .bg-slate-900, [class*="bg-slate-900"] { background-color: #0f172a !important; }
        .bg-indigo-50, [class*="bg-indigo-50"] { background-color: #eef2ff !important; }
        .bg-indigo-100, [class*="bg-indigo-100"] { background-color: #e0e7ff !important; }
        .bg-green-100, [class*="bg-green-100"] { background-color: #dcfce7 !important; }
        .bg-green-500, [class*="bg-green-500"] { background-color: #22c55e !important; }
        .bg-yellow-100, [class*="bg-yellow-100"] { background-color: #fef9c3 !important; }
        .bg-yellow-500, [class*="bg-yellow-500"] { background-color: #eab308 !important; }
        .bg-red-50, [class*="bg-red-50"] { background-color: #fef2f2 !important; }
        .bg-red-100, [class*="bg-red-100"] { background-color: #fee2e2 !important; }
        .bg-red-500, [class*="bg-red-500"] { background-color: #ef4444 !important; }
        .bg-indigo-400, [class*="bg-indigo-400"] { background-color: #818cf8 !important; }
        
        .text-slate-300, [class*="text-slate-300"] { color: #cbd5e1 !important; }
        .text-slate-400, [class*="text-slate-400"] { color: #94a3b8 !important; }
        .text-slate-500, [class*="text-slate-500"] { color: #64748b !important; }
        .text-slate-600, [class*="text-slate-600"] { color: #475569 !important; }
        .text-slate-700, [class*="text-slate-700"] { color: #334155 !important; }
        .text-slate-800, [class*="text-slate-800"] { color: #1e293b !important; }
        .text-slate-900, [class*="text-slate-900"] { color: #0f172a !important; }
        .text-white, [class*="text-white"] { color: #ffffff !important; }
        .text-indigo-700, [class*="text-indigo-700"] { color: #4338ca !important; }
        .text-indigo-300, [class*="text-indigo-300"] { color: #a5b4fc !important; }
        .text-green-600, [class*="text-green-600"] { color: #16a34a !important; }
        .text-green-800, [class*="text-green-800"] { color: #166534 !important; }
        .text-green-300, [class*="text-green-300"] { color: #86efac !important; }
        .text-yellow-800, [class*="text-yellow-800"] { color: #854d0e !important; }
        .text-red-700, [class*="text-red-700"] { color: #b91c1c !important; }
        .text-red-800, [class*="text-red-800"] { color: #991b1b !important; }
        
        .border-slate-100, [class*="border-slate-100"] { border-color: #f1f5f9 !important; }
        .border-slate-200, [class*="border-slate-200"] { border-color: #e2e8f0 !important; }
        .border-slate-700, [class*="border-slate-700"] { border-color: #334155 !important; }
        .border-slate-800, [class*="border-slate-800"] { border-color: #1e293b !important; }
        .border-indigo-100, [class*="border-indigo-100"] { border-color: #e0e7ff !important; }
        .border-indigo-800, [class*="border-indigo-800"] { border-color: #3730a3 !important; }
        .border-green-200, [class*="border-green-200"] { border-color: #bbf7d0 !important; }
        .border-yellow-200, [class*="border-yellow-200"] { border-color: #fef08a !important; }
        .border-red-100, [class*="border-red-100"] { border-color: #fee2e2 !important; }
        .border-red-200, [class*="border-red-200"] { border-color: #fecaca !important; }
        .border-red-800, [class*="border-red-800"] { border-color: #991b1b !important; }
        
        /* Remove dark mode variants entirely */
        .dark\\:bg-slate-800, .dark\\:bg-slate-900, .dark\\:bg-slate-950,
        [class*="dark:bg-"] { background-color: inherit !important; }
        .dark\\:text-white, .dark\\:text-slate-300, .dark\\:text-slate-400,
        [class*="dark:text-"] { color: inherit !important; }
        .dark\\:border-slate-700, .dark\\:border-slate-800,
        [class*="dark:border-"] { border-color: inherit !important; }
      `;
      wrapper.appendChild(styleOverride);
      wrapper.appendChild(clonedElement);
      
      // Remove dark mode classes from clone
      clonedElement.classList.remove('dark');
      clonedElement.querySelectorAll('.dark').forEach(el => el.classList.remove('dark'));
      
      // Also remove any data-theme="dark" attributes
      clonedElement.removeAttribute('data-theme');
      clonedElement.querySelectorAll('[data-theme]').forEach(el => el.removeAttribute('data-theme'));
      
      // Apply inline styles to ensure colors work with html2canvas
      const applyInlineColors = (el: HTMLElement) => {
        const computed = window.getComputedStyle(el);
        const bgColor = computed.backgroundColor;
        const textColor = computed.color;
        const borderColor = computed.borderColor;
        
        // Only override if it looks like a modern CSS function
        if (bgColor && (bgColor.includes('lab') || bgColor.includes('oklch') || bgColor.includes('color('))) {
          el.style.backgroundColor = '#ffffff';
        }
        if (textColor && (textColor.includes('lab') || textColor.includes('oklch') || textColor.includes('color('))) {
          el.style.color = '#1f2937';
        }
        if (borderColor && (borderColor.includes('lab') || borderColor.includes('oklch') || borderColor.includes('color('))) {
          el.style.borderColor = '#e2e8f0';
        }
      };
      
      // Apply to all elements
      applyInlineColors(clonedElement);
      clonedElement.querySelectorAll('*').forEach(el => {
        if (el instanceof HTMLElement) {
          applyInlineColors(el);
        }
      });
      
      document.body.appendChild(wrapper);
      
      try {
        await html2pdf().set(opt).from(clonedElement).save();
      } finally {
        document.body.removeChild(wrapper);
      }
    } catch (error) {
      console.error('Error exporting PDF:', error);
      // Fallback to browser print dialog
      const userChoice = confirm('PDF export failed due to CSS compatibility. Would you like to use the browser\'s print dialog instead?\n\nTip: Select "Save as PDF" in the print dialog.');
      if (userChoice) {
        window.print();
      }
    } finally {
      setIsExporting(false);
    }
  };

  // Helper to render traffic light
  const TrafficLight = ({ color }: { color: 'green' | 'yellow' | 'red' }) => {
    const bgColors = {
      green: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800',
      yellow: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800',
      red: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800',
    };
    const dotColors = {
      green: 'bg-green-500 dark:bg-green-400',
      yellow: 'bg-yellow-500 dark:bg-yellow-400',
      red: 'bg-red-500 dark:bg-red-400',
    };

    return (
      <span className={`inline-flex items-center px-1.5 py-0.5 rounded-full text-[10px] font-medium border ${bgColors[color]}`}>
        <span className={`w-1.5 h-1.5 mr-1 rounded-full ${dotColors[color]}`}></span>
        {color === 'green' ? 'Good Fit' : color === 'yellow' ? 'Caution' : 'Mismatch'}
      </span>
    );
  };

  // Helper to check for misfits
  const isMisfit = (item: ComparisonItem, type: 'money' | 'interest' | 'territory') => {
    if (type === 'money') return item.money.traffic_light === 'red' || item.money.traffic_light === 'yellow';
    if (type === 'interest') return item.interest.traffic_light === 'red' || item.interest.traffic_light === 'yellow';
    if (type === 'territory') return item.territories.availability_status.includes("Sold Out");
    return false;
  };

  // Style for highlighted cells
  const getHighlightClass = (isMisfit: boolean) => {
    if (!showMisfits || !isMisfit) return '';
    return 'bg-red-50 dark:bg-red-900/20 border-l-2 border-l-red-400 dark:border-l-red-500';
  };

  const handleSaveAnalysis = async () => {
    if (!selectedLeadId) return;
    setIsSaving(true);
    setSaveStatus('idle');

    try {
      // Save full analysis data structure
      await saveLeadComparisonAnalysis(selectedLeadId, data);
      
      setSaveStatus('success');
      // Optional: Don't navigate away immediately, let user see success
      setTimeout(() => {
          setSaveStatus('idle');
      }, 3000);
    } catch (err) {
      console.error(err);
      setSaveStatus('error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleLeadChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const val = e.target.value;
      if (val) {
          const newLeadId = parseInt(val);
          setSelectedLeadId(newLeadId);
          const currentUrl = new URL(window.location.href);
          currentUrl.searchParams.set('leadId', val);
          router.push(currentUrl.toString());
      }
  };

  return (
    // Fullscreen overlay with z-index high enough to cover sidebar (sidebar is usually z-30 or z-40)
    // We use z-[100] to be safe.
    <div className="fixed inset-0 z-[100] bg-slate-50 dark:bg-slate-950 flex flex-col text-xs overflow-hidden">
      {/* Header / Toolbar */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm sticky top-0 z-30 flex-shrink-0">
        <div className="max-w-[1600px] mx-auto px-4 py-2 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button onClick={onClose} className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 p-1 rounded-full hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Comparison Matrix
                <span className="px-2 py-0.5 rounded-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-[10px] font-medium">
                  {items.length} Franchises
                </span>
              </h1>
              <p className="text-[10px] text-slate-500 dark:text-slate-400">AI-Powered "Kill Sheet" Analysis</p>
            </div>
          </div>

          {/* Action Area */}
          <div className="flex items-center gap-3 w-full md:w-auto bg-slate-50 dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700">
            {/* Misfit Toggle */}
            <button
              onClick={() => setShowMisfits(!showMisfits)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all border
                ${showMisfits 
                  ? 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800' 
                  : 'bg-white dark:bg-slate-700 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600'
                }
              `}
            >
              <AlertTriangle className={`w-3.5 h-3.5 ${showMisfits ? 'text-red-600 dark:text-red-400' : 'text-slate-400 dark:text-slate-500'}`} />
              {showMisfits ? 'Hide Misfits' : 'Highlight Misfits'}
            </button>

            <div className="h-4 w-px bg-slate-300 dark:bg-slate-600 mx-1"></div>

            <div className="relative flex-1 md:w-56">
                <select
                    value={selectedLeadId || ''}
                    onChange={handleLeadChange}
                    className="w-full pl-8 pr-3 py-1.5 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-md text-xs dark:text-white focus:ring-2 focus:ring-indigo-500 outline-none appearance-none"
                >
                    <option value="">Select Lead to Attach...</option>
                    {leads.map(lead => (
                        <option key={lead.id} value={lead.id}>
                            {lead.candidate_name || `Lead #${lead.id}`}
                        </option>
                    ))}
                </select>
                <UserPlus className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2 pointer-events-none" />
            </div>
            
            <button
                onClick={handleSaveAnalysis}
                disabled={!selectedLeadId || isSaving || saveStatus === 'success'}
                className={`
                    flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all shadow-sm
                    ${!selectedLeadId 
                        ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
                        : saveStatus === 'success'
                            ? 'bg-green-600 text-white'
                            : 'bg-indigo-600 text-white hover:bg-indigo-700'
                    }
                `}
            >
                {saveStatus === 'success' ? (
                    <>
                        <Check className="w-3.5 h-3.5" />
                        Saved
                    </>
                ) : isSaving ? (
                    <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Saving...
                    </>
                ) : (
                    <>
                        <Save className="w-3.5 h-3.5" />
                        Save Analysis
                    </>
                )}
            </button>

            <button
                onClick={handleExportPDF}
                disabled={isExporting}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all shadow-sm bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {isExporting ? (
                    <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Exporting...
                    </>
                ) : (
                    <>
                        <FileDown className="w-3.5 h-3.5" />
                        Export PDF
                    </>
                )}
            </button>
          </div>
        </div>
      </div>

      {/* Content Area (Flex container for Table + Sidebar) */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Lead Profile Sidebar - Moved to Left */}
        <div className={`
          border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xl z-20 transition-all duration-300 ease-in-out overflow-hidden flex flex-col
          ${showMisfits ? 'w-80 opacity-100' : 'w-0 opacity-0'}
        `}>
          <div className="p-4 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex items-center justify-between flex-shrink-0">
             <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2">
               <UserPlus className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
               Lead Profile
             </h3>
             <button onClick={() => setShowMisfits(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                <X className="w-4 h-4" />
             </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
             {selectedLead ? (
               <>
                 <div>
                    <div className="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wider font-bold mb-2">Candidate</div>
                    <div className="text-sm font-semibold text-slate-900 dark:text-white">{selectedLead.candidate_name || 'Unknown'}</div>
                    <div className="flex flex-col gap-1 mt-1">
                        {/* Primary Location */}
                        <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                           <MapPin className="w-3 h-3" />
                           {selectedLead.profile_data.location || 'No location'} 
                           {selectedLead.profile_data.state_code && ` (${selectedLead.profile_data.state_code})`}
                        </div>
                        
                        {/* Additional Territories */}
                        {selectedLead.profile_data.territories && selectedLead.profile_data.territories.length > 1 && (
                            <div className="pl-4 text-xs text-slate-400 dark:text-slate-500 italic">
                                + {selectedLead.profile_data.territories.slice(1).map(t => t.location).join(', ')}
                            </div>
                        )}
                    </div>
                 </div>

                 <div>
                    <div className="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wider font-bold mb-2">Financials</div>
                    <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-3 border border-slate-100 dark:border-slate-800 space-y-2">
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-600 dark:text-slate-400">Liquidity</span>
                          <span className="text-sm font-medium text-slate-900 dark:text-white flex items-center gap-1">
                             <Wallet className="w-3 h-3 text-emerald-500" />
                             {selectedLead.profile_data.liquidity ? `$${selectedLead.profile_data.liquidity.toLocaleString()}` : 'N/A'}
                          </span>
                       </div>
                       <div className="flex justify-between items-center pt-2 border-t border-slate-200 dark:border-slate-700">
                          <span className="text-xs text-slate-600 dark:text-slate-400">Invest Cap</span>
                          <span className="text-sm font-medium text-slate-900 dark:text-white">
                             {selectedLead.profile_data.investment_cap ? `$${selectedLead.profile_data.investment_cap.toLocaleString()}` : 'N/A'}
                          </span>
                       </div>
                       {selectedLead.profile_data.net_worth && (
                           <div className="flex justify-between items-center pt-2 border-t border-slate-200 dark:border-slate-700">
                              <span className="text-xs text-slate-600 dark:text-slate-400">Net Worth</span>
                              <span className="text-sm font-medium text-slate-900 dark:text-white">
                                 ${selectedLead.profile_data.net_worth.toLocaleString()}
                              </span>
                           </div>
                       )}
                       {selectedLead.profile_data.investment_source && (
                           <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                              <span className="text-xs text-slate-600 dark:text-slate-400 block mb-1">Source</span>
                              <span className="text-xs font-medium text-slate-900 dark:text-white">
                                 {selectedLead.profile_data.investment_source}
                              </span>
                           </div>
                       )}
                    </div>
                 </div>

                 <div>
                    <div className="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wider font-bold mb-2">Motives & Goals</div>
                    <div className="space-y-2 text-xs">
                        {selectedLead.profile_data.trigger_event && (
                            <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-1">
                                <span className="text-slate-500 dark:text-slate-400">Trigger</span>
                                <span className="font-medium text-slate-900 dark:text-white">{selectedLead.profile_data.trigger_event}</span>
                            </div>
                        )}
                        {selectedLead.profile_data.experience_level && (
                            <div className="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-1">
                                <span className="text-slate-500 dark:text-slate-400">Experience</span>
                                <span className="font-medium text-slate-900 dark:text-white">{selectedLead.profile_data.experience_level}</span>
                            </div>
                        )}
                        {selectedLead.profile_data.goals && selectedLead.profile_data.goals.length > 0 && (
                            <div>
                                <span className="text-slate-500 dark:text-slate-400 block mb-1">Goals</span>
                                <div className="flex flex-wrap gap-1">
                                    {selectedLead.profile_data.goals.map((g, i) => (
                                        <span key={i} className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-1.5 py-0.5 rounded text-[10px]">{g}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                 </div>

                 <div>
                    <div className="text-xs text-slate-400 dark:text-slate-500 uppercase tracking-wider font-bold mb-2">Preferences</div>
                    <div className="space-y-2">
                        <div className="text-xs text-slate-600 dark:text-slate-300 italic bg-slate-50 dark:bg-slate-800/50 p-2 rounded border border-slate-100 dark:border-slate-800">
                          "{selectedLead.profile_data.semantic_query}"
                        </div>
                        
                        <div className="flex flex-wrap gap-1 mt-2">
                            {selectedLead.profile_data.role_preference && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-100 dark:border-blue-800">
                                    {selectedLead.profile_data.role_preference}
                                </span>
                            )}
                            {selectedLead.profile_data.home_based_preference && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border border-blue-100 dark:border-blue-800">
                                    Home Based
                                </span>
                            )}
                            {selectedLead.profile_data.multi_unit_preference && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border border-purple-100 dark:border-purple-800">
                                    Multi-Unit
                                </span>
                            )}
                            {selectedLead.profile_data.franchise_categories?.map((cat, i) => (
                              <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800">
                                <Tag className="w-2.5 h-2.5 mr-1" />
                                {cat}
                              </span>
                            ))}
                        </div>
                    </div>
                 </div>
               </>
             ) : (
               <div className="text-center py-10 text-slate-400 dark:text-slate-600">
                  <UserPlus className="w-10 h-10 mx-auto mb-2 opacity-20" />
                  <p className="text-xs">Select a lead from the dropdown above to see their profile data here.</p>
               </div>
             )}
          </div>
        </div>

        {/* Main Table */}
        <div className="flex-1 overflow-auto p-2 md:p-4">
          <div ref={tableRef} className="max-w-[1600px] mx-auto bg-white dark:bg-slate-900 rounded-lg shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr>
                    <th className="sticky top-0 left-0 z-20 bg-slate-50/95 dark:bg-slate-800/95 backdrop-blur p-3 border-b border-r border-slate-200 dark:border-slate-700 w-48 min-w-[180px]">
                      <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Evaluation Criteria</span>
                    </th>
                    {items.map((item) => (
                      <th key={item.franchise_id} className="sticky top-0 z-10 bg-white dark:bg-slate-900 p-3 border-b border-slate-200 dark:border-slate-700 min-w-[220px]">
                        <div className="flex flex-col space-y-2">
                          <div className="flex items-start justify-between gap-2">
                              <h3 className="text-sm font-bold text-slate-900 dark:text-white leading-tight line-clamp-2">{item.franchise_name}</h3>
                              {/* Placeholder for logo */}
                              <div className="w-8 h-8 bg-slate-100 dark:bg-slate-800 rounded flex-shrink-0" /> 
                          </div>
                          <div className="bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-[10px] p-2 rounded border border-indigo-100 dark:border-indigo-800 italic leading-snug relative mt-1">
                            "{item.verdict}"
                          </div>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  
                  {/* Section: Overview */}
                  <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td className="p-2 px-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800 border-y border-r border-slate-200 dark:border-slate-700 sticky left-0 z-10">
                      Overview
                    </td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 bg-slate-50 dark:bg-slate-800 border-y border-slate-200 dark:border-slate-700"></td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Industry</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800">
                          {item.overview?.industry || 'N/A'}
                        </span>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Year Started</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                        {item.overview?.year_started || 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Year Franchised</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                        {item.overview?.year_franchised || 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Operating Franchises</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                        {item.overview?.operating_franchises || 'N/A'}
                      </td>
                    ))}
                  </tr>
                  
                  {/* Section: Money */}
                  <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td className="p-2 px-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800 border-y border-r border-slate-200 dark:border-slate-700 sticky left-0 z-10">
                      The "Wallet" (Financials)
                    </td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 bg-slate-50 dark:bg-slate-800 border-y border-slate-200 dark:border-slate-700"></td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-900 dark:text-white bg-white dark:bg-slate-900 sticky left-0 z-10">Fit Assessment</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        <TrafficLight color={item.money.traffic_light} />
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Total Investment</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 font-medium text-slate-900 dark:text-white ${getHighlightClass(isMisfit(item, 'money'))}`}>{item.money.investment_range}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Required Liquidity</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        {item.money.liquidity_req ? `$${item.money.liquidity_req.toLocaleString()}` : 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Net Worth Requirement</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        {item.money.net_worth_req ? `$${item.money.net_worth_req.toLocaleString()}` : 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Royalty</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        {item.money?.royalty || 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">SBA Registered</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          item.money?.sba_registered 
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' 
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                        }`}>
                          {item.money?.sba_registered ? 'Yes' : 'No'}
                        </span>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">In-House Financing</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        {item.money?.in_house_financing || 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Financial Model</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'money'))}`}>{item.money.financial_model}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Overhead</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'money'))}`}>{item.money.overhead_level}</td>
                    ))}
                  </tr>

                  {/* Section: Motives */}
                  <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td className="p-2 px-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800 border-y border-r border-slate-200 dark:border-slate-700 sticky left-0 z-10">
                      The "Motives" (Growth & Stability)
                    </td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 bg-slate-50 dark:bg-slate-800 border-y border-slate-200 dark:border-slate-700"></td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Recession Resistance</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">{item.motives.recession_resistance}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Scalability</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">{item.motives.scalability}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Market Demand</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">{item.motives.market_demand}</td>
                    ))}
                  </tr>
                   <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Passive Potential</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">{item.motives.passive_income_potential}</td>
                    ))}
                  </tr>

                  {/* Section: Interest */}
                  <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td className="p-2 px-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800 border-y border-r border-slate-200 dark:border-slate-700 sticky left-0 z-10">
                      The "Life" (Operations)
                    </td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 bg-slate-50 dark:bg-slate-800 border-y border-slate-200 dark:border-slate-700"></td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-900 dark:text-white bg-white dark:bg-slate-900 sticky left-0 z-10">Role Fit</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 ${getHighlightClass(isMisfit(item, 'interest'))}`}>
                        <TrafficLight color={item.interest.traffic_light} />
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Role Type</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 font-medium text-slate-900 dark:text-white ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.role}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Sales Model</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.sales_requirement}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Employees</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.employees_count}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Inventory</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.inventory_level}</td>
                    ))}
                  </tr>

                  {/* Section: Territories */}
                  <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td className="p-2 px-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800 border-y border-r border-slate-200 dark:border-slate-700 sticky left-0 z-10">
                      The "Empire" (Territory)
                    </td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 bg-slate-50 dark:bg-slate-800 border-y border-slate-200 dark:border-slate-700"></td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Availability</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 ${getHighlightClass(isMisfit(item, 'territory'))}`}>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          item.territories.availability_status.includes("Sold Out") 
                          ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300' 
                          : 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                        }`}>
                          {item.territories.availability_status}
                        </span>
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Unavailable States</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 dark:border-slate-800 ${getHighlightClass(isMisfit(item, 'territory'))}`}>
                        {item.territories?.unavailable_states && item.territories.unavailable_states.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {item.territories.unavailable_states.slice(0, 8).map((state, idx) => (
                              <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-medium bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-100 dark:border-red-800">
                                {state}
                              </span>
                            ))}
                            {item.territories.unavailable_states.length > 8 && (
                              <span className="text-[9px] text-slate-500 dark:text-slate-400">+{item.territories.unavailable_states.length - 8} more</span>
                            )}
                          </div>
                        ) : (
                          <span className="text-[10px] text-green-600 dark:text-green-400">All states available</span>
                        )}
                      </td>
                    ))}
                  </tr>

                  {/* Section: Value Proposition */}
                  <tr className="bg-slate-50/50 dark:bg-slate-800/30">
                    <td className="p-2 px-3 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider bg-slate-50 dark:bg-slate-800 border-y border-r border-slate-200 dark:border-slate-700 sticky left-0 z-10">
                      Value Proposition
                    </td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 bg-slate-50 dark:bg-slate-800 border-y border-slate-200 dark:border-slate-700"></td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Why This Franchise</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                        <ContentList 
                          content={item.value?.why_franchise} 
                          compact={true}
                          bulletClassName="bg-indigo-400"
                          textClassName="text-slate-700 dark:text-slate-300"
                        />
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 dark:border-slate-800 font-medium text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-900 sticky left-0 z-10">Description</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                        {item.value?.value_proposition ? (
                          <p className="text-[10px] leading-relaxed">{item.value.value_proposition}</p>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500 italic">N/A</span>
                        )}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
