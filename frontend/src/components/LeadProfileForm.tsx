'use client';

import { useState, useEffect } from 'react';
import { 
  ChevronDown, 
  ChevronRight, 
  Wallet, 
  MapPin, 
  Briefcase, 
  Target, 
  Save, 
  Plus, 
  X,
  Building2,
  Users,
  Clock
} from 'lucide-react';
import { LeadProfile } from '@/types';

interface LeadProfileFormProps {
  initialProfile: LeadProfile;
  onSave: (profile: LeadProfile) => Promise<void>;
}

type SectionKey = 'money' | 'interest' | 'territories' | 'motives';

export function LeadProfileForm({ initialProfile, onSave }: LeadProfileFormProps) {
  const [profile, setProfile] = useState<LeadProfile>(initialProfile);
  const [expanded, setExpanded] = useState<Record<SectionKey, boolean>>({
    money: true,
    interest: true,
    territories: true,
    motives: true
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  
  // Territory local state
  const [newTerritoryLocation, setNewTerritoryLocation] = useState('');
  const [newTerritoryState, setNewTerritoryState] = useState('');
  
  // Categories local state
  const [newCategory, setNewCategory] = useState('');

  const toggleSection = (key: SectionKey) => {
    setExpanded(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleChange = (field: keyof LeadProfile, value: any) => {
    setProfile(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(profile);
      setIsDirty(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const addTerritory = () => {
    if (!newTerritoryLocation) return;
    
    const currentTerritories = profile.territories || [];
    const newTerritories = [
      ...currentTerritories, 
      { location: newTerritoryLocation, state_code: newTerritoryState || undefined }
    ];
    
    // Update both territories array and legacy fields if it's the first one
    const updates: Partial<LeadProfile> = { territories: newTerritories };
    if (newTerritories.length === 1) {
      updates.location = newTerritoryLocation;
      updates.state_code = newTerritoryState || undefined;
    }
    
    setProfile(prev => ({ ...prev, ...updates }));
    setNewTerritoryLocation('');
    setNewTerritoryState('');
    setIsDirty(true);
  };

  const removeTerritory = (index: number) => {
    const currentTerritories = profile.territories || [];
    const newTerritories = currentTerritories.filter((_, i) => i !== index);
    
    const updates: Partial<LeadProfile> = { territories: newTerritories };
    // If we removed the first one, update legacy fields with new first one or null
    if (index === 0) {
      if (newTerritories.length > 0) {
        updates.location = newTerritories[0].location;
        updates.state_code = newTerritories[0].state_code;
      } else {
        updates.location = null;
        updates.state_code = null;
      }
    }
    
    setProfile(prev => ({ ...prev, ...updates }));
    setIsDirty(true);
  };

  const addCategory = () => {
    if (!newCategory) return;
    const currentCategories = profile.franchise_categories || [];
    if (!currentCategories.includes(newCategory)) {
      handleChange('franchise_categories', [...currentCategories, newCategory]);
    }
    setNewCategory('');
  };

  const removeCategory = (category: string) => {
    const currentCategories = profile.franchise_categories || [];
    handleChange('franchise_categories', currentCategories.filter(c => c !== category));
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-8">
      <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h2 className="font-semibold text-slate-800 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-indigo-600" />
          Lead Profile
        </h2>
        {isDirty && (
          <button 
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        )}
      </div>

      <div className="divide-y divide-slate-100">
        
        {/* MONEY SECTION */}
        <Section 
          title="Money" 
          icon={Wallet} 
          expanded={expanded.money} 
          onToggle={() => toggleSection('money')}
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <NumberInput 
              label="Liquidity (Cash)" 
              value={profile.liquidity} 
              onChange={(v) => handleChange('liquidity', v)}
              prefix="$"
            />
            <NumberInput 
              label="Net Worth" 
              value={profile.net_worth} 
              onChange={(v) => handleChange('net_worth', v)}
              prefix="$"
            />
            <NumberInput 
              label="Investment Cap" 
              value={profile.investment_cap} 
              onChange={(v) => handleChange('investment_cap', v)}
              prefix="$"
            />
            <div className="md:col-span-2">
              <TextInput 
                label="Investment Source" 
                value={profile.investment_source} 
                onChange={(v) => handleChange('investment_source', v)}
                placeholder="e.g., HELOC, 401k Rollover, SBA Loan"
              />
            </div>
            <div className="md:col-span-1">
               <TextInput 
                label="Credit Score / Financial Notes" 
                value={profile.interest} // Using 'interest' field for financial notes/interest as discussed
                onChange={(v) => handleChange('interest', v)}
                placeholder="e.g. 720+, Bankruptcy 2010"
              />
            </div>
          </div>
        </Section>

        {/* INTEREST SECTION */}
        <Section 
          title="Interest & Preferences" 
          icon={Briefcase} 
          expanded={expanded.interest} 
          onToggle={() => toggleSection('interest')}
        >
          <div className="space-y-6">
             <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <SelectInput
                  label="Role Preference"
                  value={profile.role_preference}
                  onChange={(v) => handleChange('role_preference', v)}
                  options={['Owner-Operator', 'Semi-Absentee', 'Absentee', 'Executive']}
                />
                <SelectInput
                  label="Business Model"
                  value={profile.business_model_preference}
                  onChange={(v) => handleChange('business_model_preference', v)}
                  options={['B2B', 'B2C', 'B2B & B2C']}
                />
                <SelectInput
                  label="Staff Preference"
                  value={profile.staff_preference}
                  onChange={(v) => handleChange('staff_preference', v)}
                  options={['No Staff / Solopreneur', 'Small Staff (1-5)', 'Medium Staff (5-15)', 'Large Staff (15+)']}
                />
             </div>

             <div className="flex flex-wrap gap-6 p-4 bg-slate-50 rounded-lg border border-slate-100">
                <Checkbox 
                  label="Home Based" 
                  checked={profile.home_based_preference} 
                  onChange={(v) => handleChange('home_based_preference', v)} 
                />
                <Checkbox 
                  label="Semi-Absentee" 
                  checked={profile.semi_absentee_preference} 
                  onChange={(v) => handleChange('semi_absentee_preference', v)} 
                />
                <Checkbox 
                  label="Absentee" 
                  checked={profile.absentee_preference} 
                  onChange={(v) => handleChange('absentee_preference', v)} 
                />
                <Checkbox 
                  label="Multi-Unit Opportunity" 
                  checked={profile.multi_unit_preference} 
                  onChange={(v) => handleChange('multi_unit_preference', v)} 
                />
             </div>

             <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Interested Categories</label>
                <div className="flex gap-2 mb-3">
                   <input 
                      type="text" 
                      value={newCategory}
                      onChange={(e) => setNewCategory(e.target.value)}
                      placeholder="Add category (e.g. Fitness)"
                      className="flex-1 rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                      onKeyDown={(e) => e.key === 'Enter' && addCategory()}
                   />
                   <button 
                      onClick={addCategory}
                      type="button"
                      className="px-3 py-2 bg-indigo-50 text-indigo-600 rounded-md hover:bg-indigo-100"
                   >
                      <Plus className="w-4 h-4" />
                   </button>
                </div>
                <div className="flex flex-wrap gap-2">
                   {profile.franchise_categories?.map((cat) => (
                      <span key={cat} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                        {cat}
                        <button onClick={() => removeCategory(cat)} className="ml-1.5 text-indigo-600 hover:text-indigo-900">
                           <X className="w-3 h-3" />
                        </button>
                      </span>
                   ))}
                   {(!profile.franchise_categories || profile.franchise_categories.length === 0) && (
                      <span className="text-sm text-slate-400 italic">No specific categories selected</span>
                   )}
                </div>
             </div>
          </div>
        </Section>

        {/* TERRITORIES SECTION */}
        <Section 
          title="Territories" 
          icon={MapPin} 
          expanded={expanded.territories} 
          onToggle={() => toggleSection('territories')}
        >
           <div className="space-y-4">
              <div className="flex gap-3 items-end">
                 <div className="flex-1">
                    <label className="block text-sm font-medium text-slate-700 mb-1">Location / City</label>
                    <input 
                      type="text"
                      value={newTerritoryLocation}
                      onChange={(e) => setNewTerritoryLocation(e.target.value)}
                      className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                      placeholder="e.g. Austin"
                    />
                 </div>
                 <div className="w-24">
                    <label className="block text-sm font-medium text-slate-700 mb-1">State</label>
                    <input 
                      type="text"
                      value={newTerritoryState}
                      onChange={(e) => setNewTerritoryState(e.target.value.toUpperCase().slice(0, 2))}
                      className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                      placeholder="TX"
                      maxLength={2}
                    />
                 </div>
                 <button 
                    onClick={addTerritory}
                    type="button"
                    className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 flex items-center gap-2"
                 >
                    <Plus className="w-4 h-4" /> Add
                 </button>
              </div>

              <div className="space-y-2">
                 {profile.territories?.map((terr, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded border border-slate-200">
                       <span className="text-sm text-slate-800">
                          {terr.location} {terr.state_code ? `, ${terr.state_code}` : ''}
                       </span>
                       <button 
                          onClick={() => removeTerritory(index)}
                          className="text-slate-400 hover:text-red-500"
                       >
                          <X className="w-4 h-4" />
                       </button>
                    </div>
                 ))}
                 {(!profile.territories || profile.territories.length === 0) && (
                    <div className="text-sm text-slate-500 italic text-center py-4">
                       No territories added. Add at least one preferred territory.
                    </div>
                 )}
              </div>
           </div>
        </Section>

        {/* MOTIVES SECTION */}
        <Section 
          title="Motives & Goals" 
          icon={Target} 
          expanded={expanded.motives} 
          onToggle={() => toggleSection('motives')}
        >
           <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <TextInput 
                 label="Trigger Event" 
                 value={profile.trigger_event} 
                 onChange={(v) => handleChange('trigger_event', v)}
                 placeholder="Why now? e.g. Layoff, Burnout"
              />
              <TextInput 
                 label="Current Status" 
                 value={profile.current_status} 
                 onChange={(v) => handleChange('current_status', v)}
                 placeholder="e.g. Employed, Unemployed, Retired"
              />
              <SelectInput 
                 label="Experience Level" 
                 value={profile.experience_level} 
                 onChange={(v) => handleChange('experience_level', v)}
                 options={['First-time Business Owner', 'Serial Entrepreneur', 'Investor', 'Transitioning Executive']}
              />
              <SelectInput 
                 label="Timeline" 
                 value={profile.timeline} 
                 onChange={(v) => handleChange('timeline', v)}
                 options={['ASAP', '1-3 Months', '3-6 Months', '6+ Months', 'Just Looking']}
              />
              <div className="md:col-span-2">
                 <label className="block text-sm font-medium text-slate-700 mb-1">Primary Goals</label>
                 <textarea 
                    className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border h-20"
                    value={profile.goals?.join(', ') || ''}
                    onChange={(e) => handleChange('goals', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    placeholder="Separate goals by comma, e.g. Wealth Building, Time Freedom, Legacy"
                 />
                 <p className="text-xs text-slate-500 mt-1">Separate goals with commas</p>
              </div>
           </div>
        </Section>

      </div>
    </div>
  );
}

// --- Helper Components ---

function Section({ title, icon: Icon, expanded, onToggle, children }: any) {
  return (
    <div className="border-b border-slate-100 last:border-0">
      <button 
        onClick={onToggle}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3">
           <div className={`p-2 rounded-lg ${expanded ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
             <Icon className="w-5 h-5" />
           </div>
           <span className="font-medium text-slate-900">{title}</span>
        </div>
        {expanded ? <ChevronDown className="w-5 h-5 text-slate-400" /> : <ChevronRight className="w-5 h-5 text-slate-400" />}
      </button>
      {expanded && (
        <div className="px-6 pb-6 pt-2 animate-in slide-in-from-top-2 duration-200">
          {children}
        </div>
      )}
    </div>
  );
}

function NumberInput({ label, value, onChange, prefix }: any) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <div className="relative rounded-md shadow-sm">
        {prefix && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <span className="text-slate-500 sm:text-sm">{prefix}</span>
          </div>
        )}
        <input
          type="number"
          value={value || ''}
          onChange={(e) => onChange(e.target.value ? parseInt(e.target.value) : null)}
          className={`block w-full rounded-md border-slate-300 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border ${prefix ? 'pl-7' : ''}`}
        />
      </div>
    </div>
  );
}

function TextInput({ label, value, onChange, placeholder }: any) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
      <input
        type="text"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
        placeholder={placeholder}
      />
    </div>
  );
}

function SelectInput({ label, value, onChange, options }: any) {
  return (
    <div>
       <label className="block text-sm font-medium text-slate-700 mb-1">{label}</label>
       <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value || null)}
          className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border bg-white"
       >
          <option value="">Select...</option>
          {options.map((opt: string) => (
             <option key={opt} value={opt}>{opt}</option>
          ))}
       </select>
    </div>
  );
}

function Checkbox({ label, checked, onChange }: any) {
  return (
    <div className="flex items-center">
      <input
        id={`checkbox-${label}`}
        type="checkbox"
        checked={checked || false}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
      />
      <label htmlFor={`checkbox-${label}`} className="ml-2 block text-sm text-slate-900 cursor-pointer select-none">
        {label}
      </label>
    </div>
  );
}


