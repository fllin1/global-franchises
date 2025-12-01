'use client';

import React from 'react';

interface ContentListProps {
  content: any;
  bulletClassName?: string;
  textClassName?: string;
  compact?: boolean;
}

/**
 * ContentList - Renders content that may be in various formats as a consistent bullet list.
 * Handles JSON arrays, Python-style arrays, newline-separated text, and plain strings.
 */
export function ContentList({ 
  content, 
  bulletClassName = "bg-indigo-400",
  textClassName = "text-slate-700 dark:text-slate-300",
  compact = false
}: ContentListProps) {
  if (!content) return <p className="text-slate-400 dark:text-slate-500 italic">Information not available.</p>;
  
  let items: string[] = [];
  
  try {
    if (Array.isArray(content)) {
      items = content;
    } else if (typeof content === 'string') {
      const trimmed = content.trim();
      
      // Handle JSON arrays: ["item1", "item2"]
      if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
        try {
          items = JSON.parse(trimmed);
        } catch {
          // Handle Python-style arrays: ['item1', 'item2']
          // Convert single quotes to double quotes for JSON parsing
          const jsonCompatible = trimmed
            .replace(/'/g, '"')  // Replace single quotes with double quotes
            .replace(/\["/g, '["')  // Ensure proper JSON format
            .replace(/"\]/g, '"]');
          try {
            items = JSON.parse(jsonCompatible);
          } catch {
            // If still fails, try to extract items manually
            const matches = trimmed.match(/'([^']+)'/g);
            if (matches) {
              items = matches.map(m => m.replace(/'/g, ''));
            } else {
              // Fallback: split by newlines
              items = trimmed.split('\n').filter(line => line.trim().length > 0);
            }
          }
        }
      } else {
        // Split by newlines if it's a long string
        items = trimmed.split('\n').filter(line => line.trim().length > 0);
      }
    } else {
      items = [String(content)];
    }
  } catch (e) {
    // If all parsing fails, try to display as-is but clean it up
    const contentStr = String(content);
    // Try to extract array-like content
    const arrayMatch = contentStr.match(/\[(.*?)\]/s);
    if (arrayMatch) {
      const innerContent = arrayMatch[1];
      // Extract quoted strings
      const quotedMatches = innerContent.match(/'([^']+)'/g);
      if (quotedMatches) {
        items = quotedMatches.map(m => m.replace(/'/g, ''));
      } else {
        items = [contentStr];
      }
    } else {
      items = [contentStr];
    }
  }

  // Clean up items: remove quotes, trim whitespace
  items = items.map(item => {
    if (typeof item === 'string') {
      return item.replace(/^["']|["']$/g, '').trim();
    }
    return String(item).trim();
  }).filter(item => item.length > 0);

  if (items.length === 0) return <p className="text-slate-400 dark:text-slate-500 italic">Information not available.</p>;

  return (
    <ul className={compact ? "space-y-1" : "space-y-2"}>
      {items.map((item, idx) => (
        <li key={idx} className="flex items-start gap-2">
          <span className={`${compact ? 'mt-1' : 'mt-1.5'} w-1.5 h-1.5 ${bulletClassName} rounded-full shrink-0`} />
          <span className={`${textClassName} ${compact ? 'text-[10px]' : ''} leading-relaxed`}>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default ContentList;









