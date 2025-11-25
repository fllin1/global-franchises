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

  // Helper to parse content arrays (same logic as ContentList)
  const parseContentToArray = (content: any): string[] => {
    if (!content) return [];
    
    let items: string[] = [];
    
    try {
      if (Array.isArray(content)) {
        items = content;
      } else if (typeof content === 'string') {
        const trimmed = content.trim();
        
        if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
          try {
            items = JSON.parse(trimmed);
          } catch {
            const jsonCompatible = trimmed.replace(/'/g, '"');
            try {
              items = JSON.parse(jsonCompatible);
            } catch {
              const matches = trimmed.match(/'([^']+)'/g);
              if (matches) {
                items = matches.map(m => m.replace(/'/g, ''));
              } else {
                items = trimmed.split('\n').filter(line => line.trim().length > 0);
              }
            }
          }
        } else {
          items = trimmed.split('\n').filter(line => line.trim().length > 0);
        }
      } else {
        items = [String(content)];
      }
    } catch {
      items = [String(content)];
    }

    return items.map(item => {
      if (typeof item === 'string') {
        return item.replace(/^["']|["']$/g, '').trim();
      }
      return String(item).trim();
    }).filter(item => item.length > 0);
  };

  // PDF Export function using jsPDF + AutoTable
  const handleExportPDF = async () => {
    if (isExporting) return;
    
    if (typeof window === 'undefined') {
      console.error('PDF export is only available in browser');
      return;
    }
    
    setIsExporting(true);
    
    try {
      // Dynamic imports for jsPDF
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      
      const leadName = selectedLead?.candidate_name || 'Comparison';
      const filename = `${leadName.replace(/[^a-zA-Z0-9]/g, '_')}_Franchise_Matrix_${new Date().toISOString().split('T')[0]}.pdf`;
      
      // Create PDF document (Letter size, portrait)
      const doc = new jsPDF({
        orientation: 'portrait',
        unit: 'pt',
        format: 'letter'
      });
      
      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 40;
      const contentWidth = pageWidth - (margin * 2);
      
      // Colors
      const colors = {
        primary: [79, 70, 229] as [number, number, number],      // Indigo-600
        secondary: [100, 116, 139] as [number, number, number],  // Slate-500
        success: [34, 197, 94] as [number, number, number],      // Green-500
        warning: [234, 179, 8] as [number, number, number],      // Yellow-500
        danger: [239, 68, 68] as [number, number, number],       // Red-500
        headerBg: [241, 245, 249] as [number, number, number],   // Slate-100
        text: [15, 23, 42] as [number, number, number],          // Slate-900
        muted: [100, 116, 139] as [number, number, number],      // Slate-500
      };
      
      // ===============================
      // COVER PAGE
      // ===============================
      let yPos = margin + 60;
      
      // Title
      doc.setFontSize(28);
      doc.setTextColor(...colors.primary);
      doc.setFont('helvetica', 'bold');
      doc.text('Franchise Comparison Matrix', pageWidth / 2, yPos, { align: 'center' });
      
      yPos += 30;
      doc.setFontSize(12);
      doc.setTextColor(...colors.muted);
      doc.setFont('helvetica', 'normal');
      doc.text('AI-Powered "Kill Sheet" Analysis', pageWidth / 2, yPos, { align: 'center' });
      
      yPos += 50;
      
      // Lead Info Box
      if (selectedLead) {
        doc.setFillColor(248, 250, 252); // Slate-50
        doc.roundedRect(margin, yPos, contentWidth, 80, 8, 8, 'F');
        
        yPos += 25;
        doc.setFontSize(11);
        doc.setTextColor(...colors.secondary);
        doc.setFont('helvetica', 'bold');
        doc.text('CANDIDATE', margin + 20, yPos);
        
        yPos += 18;
        doc.setFontSize(16);
        doc.setTextColor(...colors.text);
        doc.text(selectedLead.candidate_name || 'Unknown', margin + 20, yPos);
        
        yPos += 18;
        doc.setFontSize(10);
        doc.setTextColor(...colors.muted);
        const location = selectedLead.profile_data.location || 'No location';
        const stateCode = selectedLead.profile_data.state_code ? ` (${selectedLead.profile_data.state_code})` : '';
        doc.text(`Location: ${location}${stateCode}`, margin + 20, yPos);
        
        // Financial info on right side
        const rightX = pageWidth - margin - 150;
        yPos -= 36;
        doc.setFontSize(10);
        doc.setTextColor(...colors.secondary);
        doc.text('Liquidity:', rightX, yPos);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text(selectedLead.profile_data.liquidity ? `$${selectedLead.profile_data.liquidity.toLocaleString()}` : 'N/A', rightX + 60, yPos);
        
        yPos += 15;
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...colors.secondary);
        doc.text('Net Worth:', rightX, yPos);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text(selectedLead.profile_data.net_worth ? `$${selectedLead.profile_data.net_worth.toLocaleString()}` : 'N/A', rightX + 60, yPos);
        
        yPos += 65;
      }
      
      // Franchises being compared
      yPos += 20;
      doc.setFontSize(14);
      doc.setTextColor(...colors.text);
      doc.setFont('helvetica', 'bold');
      doc.text(`Franchises Compared (${items.length})`, margin, yPos);
      
      yPos += 20;
      
      // Summary table of all franchises
      const summaryData = items.map((item, idx) => [
        (idx + 1).toString(),
        item.franchise_name,
        item.overview?.industry || 'N/A',
        item.money.investment_range,
        item.money.traffic_light === 'green' ? '✓ Good Fit' : item.money.traffic_light === 'yellow' ? '⚠ Caution' : '✗ Mismatch'
      ]);
      
      autoTable(doc, {
        startY: yPos,
        head: [['#', 'Franchise', 'Industry', 'Investment', 'Fit']],
        body: summaryData,
        margin: { left: margin, right: margin },
        headStyles: { 
          fillColor: colors.headerBg, 
          textColor: colors.text,
          fontStyle: 'bold',
          fontSize: 9
        },
        bodyStyles: { 
          fontSize: 9,
          textColor: colors.text
        },
        alternateRowStyles: { fillColor: [250, 250, 250] },
        columnStyles: {
          0: { cellWidth: 25, halign: 'center' },
          1: { cellWidth: 150 },
          2: { cellWidth: 100 },
          3: { cellWidth: 100 },
          4: { cellWidth: 70, halign: 'center' }
        }
      });
      
      yPos = (doc as any).lastAutoTable.finalY + 30;
      
      // Export info
      doc.setFontSize(9);
      doc.setTextColor(...colors.muted);
      doc.text(`Generated: ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}`, margin, yPos);
      
      // ===============================
      // FRANCHISE DETAIL PAGES
      // ===============================
      items.forEach((item, index) => {
        doc.addPage();
        let y = margin;
        
        // Franchise Header
        doc.setFillColor(...colors.primary);
        doc.rect(0, 0, pageWidth, 70, 'F');
        
        doc.setFontSize(22);
        doc.setTextColor(255, 255, 255);
        doc.setFont('helvetica', 'bold');
        doc.text(item.franchise_name, margin, 35);
        
        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.text(item.overview?.industry || 'Uncategorized', margin, 52);
        
        // Page number indicator
        doc.setFontSize(10);
        doc.text(`${index + 1} of ${items.length}`, pageWidth - margin - 50, 35, { align: 'right' });
        
        y = 90;
        
        // Verdict Box
        doc.setFillColor(238, 242, 255); // Indigo-50
        doc.roundedRect(margin, y, contentWidth, 45, 6, 6, 'F');
        doc.setDrawColor(...colors.primary);
        doc.setLineWidth(1);
        doc.roundedRect(margin, y, contentWidth, 45, 6, 6, 'S');
        
        doc.setFontSize(10);
        doc.setTextColor(...colors.primary);
        doc.setFont('helvetica', 'italic');
        const verdictLines = doc.splitTextToSize(`"${item.verdict}"`, contentWidth - 30);
        doc.text(verdictLines, margin + 15, y + 20);
        
        y += 60;
        
        // ---- OVERVIEW TABLE ----
        doc.setFontSize(12);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text('Overview', margin, y);
        y += 15;
        
        autoTable(doc, {
          startY: y,
          body: [
            ['Year Started', item.overview?.year_started?.toString() || 'N/A'],
            ['Year Franchised', item.overview?.year_franchised?.toString() || 'N/A'],
            ['Operating Franchises', item.overview?.operating_franchises || 'N/A']
          ],
          margin: { left: margin, right: margin },
          theme: 'plain',
          bodyStyles: { fontSize: 9, textColor: colors.text, cellPadding: 6 },
          columnStyles: {
            0: { cellWidth: 140, fontStyle: 'bold', textColor: colors.secondary },
            1: { cellWidth: contentWidth - 140 }
          }
        });
        
        y = (doc as any).lastAutoTable.finalY + 15;
        
        // ---- FINANCIALS TABLE ----
        doc.setFontSize(12);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text('Financials (The "Wallet")', margin, y);
        
        // Fit indicator
        const fitColor = item.money.traffic_light === 'green' ? colors.success : 
                         item.money.traffic_light === 'yellow' ? colors.warning : colors.danger;
        const fitText = item.money.traffic_light === 'green' ? 'Good Fit' : 
                        item.money.traffic_light === 'yellow' ? 'Caution' : 'Mismatch';
        doc.setFillColor(...fitColor);
        doc.roundedRect(pageWidth - margin - 70, y - 12, 70, 18, 4, 4, 'F');
        doc.setFontSize(9);
        doc.setTextColor(255, 255, 255);
        doc.text(fitText, pageWidth - margin - 35, y - 1, { align: 'center' });
        
        y += 15;
        
        autoTable(doc, {
          startY: y,
          body: [
            ['Total Investment', item.money.investment_range],
            ['Required Liquidity', item.money.liquidity_req ? `$${item.money.liquidity_req.toLocaleString()}` : 'N/A'],
            ['Net Worth Requirement', item.money.net_worth_req ? `$${item.money.net_worth_req.toLocaleString()}` : 'N/A'],
            ['Royalty', item.money.royalty || 'N/A'],
            ['SBA Registered', item.money.sba_registered ? 'Yes' : 'No'],
            ['In-House Financing', item.money.in_house_financing || 'N/A'],
            ['Financial Model', item.money.financial_model],
            ['Overhead Level', item.money.overhead_level]
          ],
          margin: { left: margin, right: margin },
          theme: 'striped',
          headStyles: { fillColor: colors.headerBg, textColor: colors.text },
          bodyStyles: { fontSize: 9, textColor: colors.text, cellPadding: 5 },
          alternateRowStyles: { fillColor: [250, 250, 250] },
          columnStyles: {
            0: { cellWidth: 140, fontStyle: 'bold', textColor: colors.secondary },
            1: { cellWidth: contentWidth - 140 }
          }
        });
        
        y = (doc as any).lastAutoTable.finalY + 15;
        
        // ---- MOTIVES TABLE ----
        doc.setFontSize(12);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text('Growth & Stability (The "Motives")', margin, y);
        y += 15;
        
        autoTable(doc, {
          startY: y,
          body: [
            ['Recession Resistance', item.motives.recession_resistance],
            ['Scalability', item.motives.scalability],
            ['Market Demand', item.motives.market_demand],
            ['Passive Income Potential', item.motives.passive_income_potential]
          ],
          margin: { left: margin, right: margin },
          theme: 'striped',
          bodyStyles: { fontSize: 9, textColor: colors.text, cellPadding: 5 },
          alternateRowStyles: { fillColor: [250, 250, 250] },
          columnStyles: {
            0: { cellWidth: 140, fontStyle: 'bold', textColor: colors.secondary },
            1: { cellWidth: contentWidth - 140 }
          }
        });
        
        y = (doc as any).lastAutoTable.finalY + 15;
        
        // ---- OPERATIONS TABLE ----
        doc.setFontSize(12);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text('Operations (The "Life")', margin, y);
        
        // Role Fit indicator
        const roleFitColor = item.interest.traffic_light === 'green' ? colors.success : 
                             item.interest.traffic_light === 'yellow' ? colors.warning : colors.danger;
        const roleFitText = item.interest.traffic_light === 'green' ? 'Good Fit' : 
                            item.interest.traffic_light === 'yellow' ? 'Caution' : 'Mismatch';
        doc.setFillColor(...roleFitColor);
        doc.roundedRect(pageWidth - margin - 70, y - 12, 70, 18, 4, 4, 'F');
        doc.setFontSize(9);
        doc.setTextColor(255, 255, 255);
        doc.text(roleFitText, pageWidth - margin - 35, y - 1, { align: 'center' });
        
        y += 15;
        
        autoTable(doc, {
          startY: y,
          body: [
            ['Role Type', item.interest.role],
            ['Sales Model', item.interest.sales_requirement],
            ['Employees', item.interest.employees_count],
            ['Inventory Level', item.interest.inventory_level]
          ],
          margin: { left: margin, right: margin },
          theme: 'striped',
          bodyStyles: { fontSize: 9, textColor: colors.text, cellPadding: 5 },
          alternateRowStyles: { fillColor: [250, 250, 250] },
          columnStyles: {
            0: { cellWidth: 140, fontStyle: 'bold', textColor: colors.secondary },
            1: { cellWidth: contentWidth - 140 }
          }
        });
        
        y = (doc as any).lastAutoTable.finalY + 15;
        
        // ---- TERRITORY TABLE ----
        doc.setFontSize(12);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text('Territory (The "Empire")', margin, y);
        y += 15;
        
        const unavailableStates = item.territories?.unavailable_states?.length 
          ? item.territories.unavailable_states.join(', ') 
          : 'All states available';
        
        autoTable(doc, {
          startY: y,
          body: [
            ['Availability Status', item.territories.availability_status],
            ['Unavailable States', unavailableStates]
          ],
          margin: { left: margin, right: margin },
          theme: 'striped',
          bodyStyles: { fontSize: 9, textColor: colors.text, cellPadding: 5 },
          alternateRowStyles: { fillColor: [250, 250, 250] },
          columnStyles: {
            0: { cellWidth: 140, fontStyle: 'bold', textColor: colors.secondary },
            1: { cellWidth: contentWidth - 140 }
          }
        });
        
        y = (doc as any).lastAutoTable.finalY + 15;
        
        // ---- VALUE PROPOSITION ----
        // Check if we need a new page
        if (y > pageHeight - 200) {
          doc.addPage();
          y = margin;
        }
        
        doc.setFontSize(12);
        doc.setTextColor(...colors.text);
        doc.setFont('helvetica', 'bold');
        doc.text('Value Proposition', margin, y);
        y += 15;
        
        // Why This Franchise (bullet points)
        const whyItems = parseContentToArray(item.value?.why_franchise);
        if (whyItems.length > 0) {
          doc.setFontSize(10);
          doc.setTextColor(...colors.secondary);
          doc.setFont('helvetica', 'bold');
          doc.text('Why This Franchise:', margin, y);
          y += 12;
          
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(...colors.text);
          doc.setFontSize(9);
          
          whyItems.forEach(point => {
            const bulletLines = doc.splitTextToSize(`• ${point}`, contentWidth - 20);
            bulletLines.forEach((line: string) => {
              if (y > pageHeight - 50) {
                doc.addPage();
                y = margin;
              }
              doc.text(line, margin + 10, y);
              y += 12;
            });
          });
          
          y += 5;
        }
        
        // Description
        if (item.value?.value_proposition) {
          doc.setFontSize(10);
          doc.setTextColor(...colors.secondary);
          doc.setFont('helvetica', 'bold');
          doc.text('Description:', margin, y);
          y += 12;
          
          doc.setFont('helvetica', 'normal');
          doc.setTextColor(...colors.text);
          doc.setFontSize(9);
          
          const descLines = doc.splitTextToSize(item.value.value_proposition, contentWidth - 20);
          descLines.forEach((line: string) => {
            if (y > pageHeight - 50) {
              doc.addPage();
              y = margin;
            }
            doc.text(line, margin + 10, y);
            y += 12;
          });
        }
      });
      
      // ===============================
      // ADD PAGE NUMBERS TO ALL PAGES
      // ===============================
      const pageCount = doc.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(9);
        doc.setTextColor(...colors.muted);
        doc.text(
          `Page ${i} of ${pageCount}`,
          pageWidth / 2,
          pageHeight - 20,
          { align: 'center' }
        );
      }
      
      // Save the PDF
      doc.save(filename);
      
    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Failed to export PDF. Please try again.');
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
