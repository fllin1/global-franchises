import React, { useState, useMemo } from 'react';
import { ComparisonItem, ComparisonResponse, Lead } from '../types';
import { Save, ArrowLeft, UserPlus, Check, AlertTriangle, X, MapPin, Wallet, Tag } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { saveLeadComparisonAnalysis } from '@/app/actions';

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

  // Get full selected lead object
  const selectedLead = useMemo(() => 
    leads.find(l => l.id === selectedLeadId), 
    [selectedLeadId, leads]
  );

  // Helper to render traffic light
  const TrafficLight = ({ color }: { color: 'green' | 'yellow' | 'red' }) => {
    const bgColors = {
      green: 'bg-green-100 text-green-800 border-green-200',
      yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      red: 'bg-red-100 text-red-800 border-red-200',
    };
    const dotColors = {
      green: 'bg-green-500',
      yellow: 'bg-yellow-500',
      red: 'bg-red-500',
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
    return 'bg-red-50 border-l-2 border-l-red-400';
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
    <div className="fixed inset-0 z-[100] bg-slate-50 flex flex-col text-xs overflow-hidden">
      {/* Header / Toolbar */}
      <div className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-30 flex-shrink-0">
        <div className="max-w-[1600px] mx-auto px-4 py-2 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-50 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                Comparison Matrix
                <span className="px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 text-[10px] font-medium">
                  {items.length} Franchises
                </span>
              </h1>
              <p className="text-[10px] text-slate-500">AI-Powered "Kill Sheet" Analysis</p>
            </div>
          </div>

          {/* Action Area */}
          <div className="flex items-center gap-3 w-full md:w-auto bg-slate-50 p-1 rounded-lg border border-slate-200">
            {/* Misfit Toggle */}
            <button
              onClick={() => setShowMisfits(!showMisfits)}
              className={`
                flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all border
                ${showMisfits 
                  ? 'bg-red-50 text-red-700 border-red-200' 
                  : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }
              `}
            >
              <AlertTriangle className={`w-3.5 h-3.5 ${showMisfits ? 'text-red-600' : 'text-slate-400'}`} />
              {showMisfits ? 'Hide Misfits' : 'Highlight Misfits'}
            </button>

            <div className="h-4 w-px bg-slate-300 mx-1"></div>

            <div className="relative flex-1 md:w-56">
                <select
                    value={selectedLeadId || ''}
                    onChange={handleLeadChange}
                    className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs focus:ring-2 focus:ring-indigo-500 outline-none appearance-none"
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
          </div>
        </div>
      </div>

      {/* Content Area (Flex container for Table + Sidebar) */}
      <div className="flex flex-1 overflow-hidden relative">
        
        {/* Lead Profile Sidebar - Moved to Left */}
        <div className={`
          border-r border-slate-200 bg-white shadow-xl z-20 transition-all duration-300 ease-in-out overflow-hidden flex flex-col
          ${showMisfits ? 'w-80 opacity-100' : 'w-0 opacity-0'}
        `}>
          <div className="p-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between flex-shrink-0">
             <h3 className="font-bold text-slate-800 flex items-center gap-2">
               <UserPlus className="w-4 h-4 text-indigo-600" />
               Lead Profile
             </h3>
             <button onClick={() => setShowMisfits(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
             </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
             {selectedLead ? (
               <>
                 <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider font-bold mb-2">Candidate</div>
                    <div className="text-sm font-semibold text-slate-900">{selectedLead.candidate_name || 'Unknown'}</div>
                    <div className="flex flex-col gap-1 mt-1">
                        {/* Primary Location */}
                        <div className="flex items-center gap-1 text-xs text-slate-500">
                           <MapPin className="w-3 h-3" />
                           {selectedLead.profile_data.location || 'No location'} 
                           {selectedLead.profile_data.state_code && ` (${selectedLead.profile_data.state_code})`}
                        </div>
                        
                        {/* Additional Territories */}
                        {selectedLead.profile_data.territories && selectedLead.profile_data.territories.length > 1 && (
                            <div className="pl-4 text-xs text-slate-400 italic">
                                + {selectedLead.profile_data.territories.slice(1).map(t => t.location).join(', ')}
                            </div>
                        )}
                    </div>
                 </div>

                 <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider font-bold mb-2">Financials</div>
                    <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 space-y-2">
                       <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-600">Liquidity</span>
                          <span className="text-sm font-medium text-slate-900 flex items-center gap-1">
                             <Wallet className="w-3 h-3 text-emerald-500" />
                             {selectedLead.profile_data.liquidity ? `$${selectedLead.profile_data.liquidity.toLocaleString()}` : 'N/A'}
                          </span>
                       </div>
                       <div className="flex justify-between items-center pt-2 border-t border-slate-200">
                          <span className="text-xs text-slate-600">Invest Cap</span>
                          <span className="text-sm font-medium text-slate-900">
                             {selectedLead.profile_data.investment_cap ? `$${selectedLead.profile_data.investment_cap.toLocaleString()}` : 'N/A'}
                          </span>
                       </div>
                       {selectedLead.profile_data.net_worth && (
                           <div className="flex justify-between items-center pt-2 border-t border-slate-200">
                              <span className="text-xs text-slate-600">Net Worth</span>
                              <span className="text-sm font-medium text-slate-900">
                                 ${selectedLead.profile_data.net_worth.toLocaleString()}
                              </span>
                           </div>
                       )}
                       {selectedLead.profile_data.investment_source && (
                           <div className="pt-2 border-t border-slate-200">
                              <span className="text-xs text-slate-600 block mb-1">Source</span>
                              <span className="text-xs font-medium text-slate-900">
                                 {selectedLead.profile_data.investment_source}
                              </span>
                           </div>
                       )}
                    </div>
                 </div>

                 <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider font-bold mb-2">Motives & Goals</div>
                    <div className="space-y-2 text-xs">
                        {selectedLead.profile_data.trigger_event && (
                            <div className="flex justify-between border-b border-slate-100 pb-1">
                                <span className="text-slate-500">Trigger</span>
                                <span className="font-medium text-slate-900">{selectedLead.profile_data.trigger_event}</span>
                            </div>
                        )}
                        {selectedLead.profile_data.experience_level && (
                            <div className="flex justify-between border-b border-slate-100 pb-1">
                                <span className="text-slate-500">Experience</span>
                                <span className="font-medium text-slate-900">{selectedLead.profile_data.experience_level}</span>
                            </div>
                        )}
                        {selectedLead.profile_data.goals && selectedLead.profile_data.goals.length > 0 && (
                            <div>
                                <span className="text-slate-500 block mb-1">Goals</span>
                                <div className="flex flex-wrap gap-1">
                                    {selectedLead.profile_data.goals.map((g, i) => (
                                        <span key={i} className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">{g}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                 </div>

                 <div>
                    <div className="text-xs text-slate-400 uppercase tracking-wider font-bold mb-2">Preferences</div>
                    <div className="space-y-2">
                        <div className="text-xs text-slate-600 italic bg-slate-50 p-2 rounded border border-slate-100">
                          "{selectedLead.profile_data.semantic_query}"
                        </div>
                        
                        <div className="flex flex-wrap gap-1 mt-2">
                            {selectedLead.profile_data.role_preference && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                    {selectedLead.profile_data.role_preference}
                                </span>
                            )}
                            {selectedLead.profile_data.home_based_preference && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-blue-50 text-blue-700 border border-blue-100">
                                    Home Based
                                </span>
                            )}
                            {selectedLead.profile_data.multi_unit_preference && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-purple-50 text-purple-700 border border-purple-100">
                                    Multi-Unit
                                </span>
                            )}
                            {selectedLead.profile_data.franchise_categories?.map((cat, i) => (
                              <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-100">
                                <Tag className="w-2.5 h-2.5 mr-1" />
                                {cat}
                              </span>
                            ))}
                        </div>
                    </div>
                 </div>
               </>
             ) : (
               <div className="text-center py-10 text-slate-400">
                  <UserPlus className="w-10 h-10 mx-auto mb-2 opacity-20" />
                  <p className="text-xs">Select a lead from the dropdown above to see their profile data here.</p>
               </div>
             )}
          </div>
        </div>

        {/* Main Table */}
        <div className="flex-1 overflow-auto p-2 md:p-4">
          <div className="max-w-[1600px] mx-auto bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr>
                    <th className="sticky top-0 left-0 z-20 bg-slate-50/95 backdrop-blur p-3 border-b border-r border-slate-200 w-48 min-w-[180px]">
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Evaluation Criteria</span>
                    </th>
                    {items.map((item) => (
                      <th key={item.franchise_id} className="sticky top-0 z-10 bg-white p-3 border-b border-slate-200 min-w-[220px]">
                        <div className="flex flex-col space-y-2">
                          <div className="flex items-start justify-between gap-2">
                              <h3 className="text-sm font-bold text-slate-900 leading-tight line-clamp-2">{item.franchise_name}</h3>
                              {/* Placeholder for logo */}
                              <div className="w-8 h-8 bg-slate-100 rounded flex-shrink-0" /> 
                          </div>
                          <div className="bg-indigo-50 text-indigo-700 text-[10px] p-2 rounded border border-indigo-100 italic leading-snug relative mt-1">
                            "{item.verdict}"
                          </div>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  
                  {/* Section: Money */}
                  <tr className="bg-slate-50/50">
                    <td colSpan={items.length + 1} className="p-2 px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider bg-slate-50 border-y border-slate-200">
                      The "Wallet" (Financials)
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-900 bg-white sticky left-0 z-10">Fit Assessment</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        <TrafficLight color={item.money.traffic_light} />
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Total Investment</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 font-medium text-slate-900 ${getHighlightClass(isMisfit(item, 'money'))}`}>{item.money.investment_range}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Financial Model</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 text-slate-700 ${getHighlightClass(isMisfit(item, 'money'))}`}>{item.money.financial_model}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Overhead</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 text-slate-700 ${getHighlightClass(isMisfit(item, 'money'))}`}>{item.money.overhead_level}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Required Liquidity</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 text-slate-700 ${getHighlightClass(isMisfit(item, 'money'))}`}>
                        {item.money.liquidity_req ? `$${item.money.liquidity_req.toLocaleString()}` : 'N/A'}
                      </td>
                    ))}
                  </tr>

                  {/* Section: Motives */}
                  <tr className="bg-slate-50/50">
                    <td colSpan={items.length + 1} className="p-2 px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider bg-slate-50 border-y border-slate-200">
                      The "Motives" (Growth & Stability)
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Recession Resistance</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 text-slate-700">{item.motives.recession_resistance}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Scalability</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 text-slate-700">{item.motives.scalability}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Market Demand</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 text-slate-700">{item.motives.market_demand}</td>
                    ))}
                  </tr>
                   <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Passive Potential</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className="p-2 px-3 border-r border-slate-50 text-slate-700">{item.motives.passive_income_potential}</td>
                    ))}
                  </tr>

                  {/* Section: Interest */}
                  <tr className="bg-slate-50/50">
                    <td colSpan={items.length + 1} className="p-2 px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider bg-slate-50 border-y border-slate-200">
                      The "Life" (Operations)
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-900 bg-white sticky left-0 z-10">Role Fit</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 ${getHighlightClass(isMisfit(item, 'interest'))}`}>
                        <TrafficLight color={item.interest.traffic_light} />
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Role Type</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 font-medium text-slate-900 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.role}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Sales Model</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 text-slate-700 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.sales_requirement}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Employees</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 text-slate-700 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.employees_count}</td>
                    ))}
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Inventory</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 text-slate-700 ${getHighlightClass(isMisfit(item, 'interest'))}`}>{item.interest.inventory_level}</td>
                    ))}
                  </tr>

                  {/* Section: Territories */}
                  <tr className="bg-slate-50/50">
                    <td colSpan={items.length + 1} className="p-2 px-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider bg-slate-50 border-y border-slate-200">
                      The "Empire" (Territory)
                    </td>
                  </tr>
                  <tr>
                    <td className="p-2 px-3 border-r border-slate-100 font-medium text-slate-500 bg-white sticky left-0 z-10">Availability</td>
                    {items.map((item) => (
                      <td key={item.franchise_id} className={`p-2 px-3 border-r border-slate-50 ${getHighlightClass(isMisfit(item, 'territory'))}`}>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${
                          item.territories.availability_status.includes("Sold Out") 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                        }`}>
                          {item.territories.availability_status}
                        </span>
                        {item.territories.territory_notes && (
                          <p className="text-[10px] text-slate-500 mt-1">{item.territories.territory_notes}</p>
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
