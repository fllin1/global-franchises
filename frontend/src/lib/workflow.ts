/**
 * Workflow status configuration for GHL Lead Nurturing pipeline.
 * These statuses map to the 12 stages in the GHL pipeline.
 */
export const WORKFLOW_STATUSES = {
  new_lead: {
    label: 'New Lead',
    color: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700',
    dotColor: 'bg-slate-400',
  },
  initial_sms_sent: {
    label: 'Initial SMS Sent',
    color: 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800',
    dotColor: 'bg-blue-500',
  },
  sms_engaged_scheduling: {
    label: 'SMS Engaged',
    color: 'bg-sky-50 text-sky-700 border-sky-100 dark:bg-sky-900/30 dark:text-sky-300 dark:border-sky-800',
    dotColor: 'bg-sky-500',
  },
  deeper_dive_scheduled: {
    label: 'Deeper Dive Scheduled',
    color: 'bg-cyan-50 text-cyan-700 border-cyan-100 dark:bg-cyan-900/30 dark:text-cyan-300 dark:border-cyan-800',
    dotColor: 'bg-cyan-500',
  },
  needs_manual_followup: {
    label: 'Needs Follow-up',
    color: 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800',
    dotColor: 'bg-amber-500',
  },
  qualified_post_deeper_dive: {
    label: 'Qualified',
    color: 'bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800',
    dotColor: 'bg-purple-500',
  },
  franchises_presented: {
    label: 'Franchises Presented',
    color: 'bg-indigo-50 text-indigo-700 border-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800',
    dotColor: 'bg-indigo-500',
  },
  funding_intro_made: {
    label: 'Funding Intro Made',
    color: 'bg-violet-50 text-violet-700 border-violet-100 dark:bg-violet-900/30 dark:text-violet-300 dark:border-violet-800',
    dotColor: 'bg-violet-500',
  },
  franchisor_intro_made: {
    label: 'Franchisor Intro Made',
    color: 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-100 dark:bg-fuchsia-900/30 dark:text-fuchsia-300 dark:border-fuchsia-800',
    dotColor: 'bg-fuchsia-500',
  },
  closed_won: {
    label: 'Closed Won',
    color: 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800',
    dotColor: 'bg-emerald-500',
  },
  disqualified: {
    label: 'Disqualified',
    color: 'bg-red-50 text-red-700 border-red-100 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800',
    dotColor: 'bg-red-500',
  },
  nurturing_long_term: {
    label: 'Nurturing',
    color: 'bg-orange-50 text-orange-700 border-orange-100 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-800',
    dotColor: 'bg-orange-500',
  },
} as const;

export type WorkflowStatus = keyof typeof WORKFLOW_STATUSES;

/** Default status for new leads or when status is unknown */
export const DEFAULT_WORKFLOW_STATUS: WorkflowStatus = 'new_lead';

/**
 * Legacy status mapping for backwards compatibility.
 * Maps old status values to new ones during migration.
 */
export const LEGACY_STATUS_MAP: Record<string, WorkflowStatus> = {
  new: 'new_lead',
  contacted: 'initial_sms_sent',
  qualified: 'qualified_post_deeper_dive',
  presented: 'franchises_presented',
  closed_won: 'closed_won',
  closed_lost: 'disqualified',
};

/**
 * Get the workflow status config, handling legacy status values.
 * Falls back to default status if unknown.
 */
export function getWorkflowStatusConfig(status: string | undefined | null) {
  if (!status) {
    return { key: DEFAULT_WORKFLOW_STATUS, ...WORKFLOW_STATUSES[DEFAULT_WORKFLOW_STATUS] };
  }

  // Check if it's a valid new status
  if (status in WORKFLOW_STATUSES) {
    return { key: status as WorkflowStatus, ...WORKFLOW_STATUSES[status as WorkflowStatus] };
  }

  // Check if it's a legacy status that needs mapping
  if (status in LEGACY_STATUS_MAP) {
    const mappedStatus = LEGACY_STATUS_MAP[status];
    return { key: mappedStatus, ...WORKFLOW_STATUSES[mappedStatus] };
  }

  // Unknown status, use default
  return { key: DEFAULT_WORKFLOW_STATUS, ...WORKFLOW_STATUSES[DEFAULT_WORKFLOW_STATUS] };
}
