import React, { useState } from 'react';
import { 
  ShieldAlert, 
  CheckCircle, 
  XCircle, 
  HelpCircle, 
  Send, 
  DollarSign, 
  FileText,
  AlertTriangle,
  UserCheck
} from 'lucide-react';
import { ApprovalRequest, TaskStatus } from '../types';

interface ApprovalCardProps {
  approvals: ApprovalRequest[];
  taskStatus: TaskStatus;
  onDecision: (approvalId: string, decision: 'APPROVED' | 'REJECTED', clarificationValue?: string) => Promise<void>;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approvals,
  taskStatus,
  onDecision
}) => {
  const [clarificationText, setClarificationText] = useState('2026-11-15');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const pendingApproval = approvals.find(a => a.status === 'PENDING');

  if (!pendingApproval) return null;

  let parsedPayload: any = {};
  try {
    parsedPayload = JSON.parse(pendingApproval.payload_json);
  } catch (e) {
    parsedPayload = {};
  }

  const isClarificationRequest = pendingApproval.action_name.includes('clarify') || taskStatus === 'WAITING_FOR_INPUT';

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      await onDecision(pendingApproval.id, 'APPROVED');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      await onDecision(pendingApproval.id, 'REJECTED');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitClarification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clarificationText.trim()) return;
    setIsSubmitting(true);
    try {
      await onDecision(pendingApproval.id, 'APPROVED', clarificationText.trim());
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-gradient-to-b from-amber-950/40 to-slate-900 border-2 border-amber-500/50 rounded-xl overflow-hidden shadow-xl shadow-amber-950/20 my-4 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="bg-amber-500/20 border-b border-amber-500/30 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isClarificationRequest ? (
            <HelpCircle className="w-5 h-5 text-amber-400 shrink-0" />
          ) : (
            <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0" />
          )}
          <span className="font-bold text-sm text-amber-200">
            {isClarificationRequest ? 'Human Clarification Required' : 'Supervisor Authorization Required'}
          </span>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-500 text-slate-950">
          Action Paused
        </span>
      </div>

      <div className="p-4 space-y-3">
        {/* Explanation */}
        <p className="text-xs text-slate-200 leading-relaxed font-medium">
          {pendingApproval.reason}
        </p>

        {/* Proposed Action Payload Preview */}
        <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs font-mono">
          <div className="flex items-center justify-between text-slate-400 mb-2 border-b border-slate-800 pb-1.5 font-sans">
            <span className="font-semibold text-slate-300">Action: {pendingApproval.action_name}</span>
            <span className="text-[11px] text-amber-400">Policy: Company Financial Gate</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-slate-300">
            {parsedPayload.vendor && (
              <div>
                <span className="text-slate-500 text-[10px] block font-sans">VENDOR</span>
                <span className="font-semibold text-white">{parsedPayload.vendor}</span>
              </div>
            )}
            {parsedPayload.invoice_number && (
              <div>
                <span className="text-slate-500 text-[10px] block font-sans">INVOICE NUMBER</span>
                <span className="text-blue-400 font-semibold">{parsedPayload.invoice_number}</span>
              </div>
            )}
            {parsedPayload.total_amount !== undefined && (
              <div>
                <span className="text-slate-500 text-[10px] block font-sans">TOTAL AMOUNT</span>
                <span className="text-emerald-400 font-bold">{parsedPayload.currency || 'USD'} {Number(parsedPayload.total_amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              </div>
            )}
            {parsedPayload.due_date && (
              <div>
                <span className="text-slate-500 text-[10px] block font-sans">SOURCE DUE DATE</span>
                <span className={parsedPayload.due_date.includes('AMBIGUOUS') ? 'text-amber-400 font-bold' : 'text-slate-300'}>
                  {parsedPayload.due_date}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Interactive Clarification Input Form */}
        {isClarificationRequest ? (
          <form onSubmit={handleSubmitClarification} className="pt-2 border-t border-slate-800 space-y-2">
            <label className="block text-xs font-semibold text-slate-300">
              Provide Validated Due Date (YYYY-MM-DD):
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={clarificationText}
                onChange={(e) => setClarificationText(e.target.value)}
                placeholder="2026-11-15"
                className="bg-slate-950 border border-slate-700 text-white rounded-lg px-3 py-2 text-xs flex-1 focus:outline-none focus:border-blue-500 font-mono"
              />
              <button
                type="submit"
                disabled={isSubmitting || !clarificationText.trim()}
                className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 shadow transition-all"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit & Resume</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-400">
              The autonomous operator will resume execution, update the verified record with your input, and persist to the database.
            </p>
          </form>
        ) : (
          /* Consequential Action Approval Controls */
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2.5">
            <button
              onClick={handleReject}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg text-xs font-semibold border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 transition-all flex items-center gap-1.5 disabled:opacity-50"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Reject Action</span>
            </button>
            <button
              onClick={handleApprove}
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all flex items-center gap-1.5 shadow-md shadow-emerald-900/30 disabled:opacity-50 active:scale-95"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Authorize & Create Record</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
