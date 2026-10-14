import React from 'react';
import { 
  Play, 
  XOctagon, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ShieldCheck, 
  HelpCircle,
  FileText,
  Calendar,
  Sparkles
} from 'lucide-react';
import { Task, TaskStatus } from '../types';
import { PlanCard } from './PlanCard';
import { ApprovalCard } from './ApprovalCard';
import { TimelineCard } from './TimelineCard';
import { EvidenceVerificationPanel } from './EvidenceVerificationPanel';

interface TaskWorkspaceProps {
  task: Task | null;
  onRunTask: (taskId: string) => void;
  onCancelTask: (taskId: string) => void;
  onApprovalDecision: (approvalId: string, decision: 'APPROVED' | 'REJECTED', clarificationValue?: string) => Promise<void>;
}

export const TaskWorkspace: React.FC<TaskWorkspaceProps> = ({
  task,
  onRunTask,
  onCancelTask,
  onApprovalDecision,
}) => {
  if (!task) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-500">
        <Sparkles className="w-8 h-8 text-blue-500/50 mx-auto mb-3 animate-pulse" />
        <h3 className="text-base font-semibold text-slate-300">No Task Selected</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Select an existing task from the sidebar or click "New Business Goal" to launch an autonomous operator run.
        </p>
      </div>
    );
  }

  const getStatusBadge = (status: TaskStatus) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 shadow-sm">
            <CheckCircle2 className="w-3.5 h-3.5" /> Completed & Verified
          </span>
        );
      case 'WAITING_FOR_APPROVAL':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500 text-slate-950 flex items-center gap-1.5 shadow animate-pulse">
            <Clock className="w-3.5 h-3.5" /> Awaiting Approval
          </span>
        );
      case 'WAITING_FOR_INPUT':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500 text-slate-950 flex items-center gap-1.5 shadow animate-pulse">
            <HelpCircle className="w-3.5 h-3.5" /> Clarification Required
          </span>
        );
      case 'RUNNING':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Executing
          </span>
        );
      case 'PLANNING':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Planning
          </span>
        );
      case 'VERIFYING':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 animate-pulse" /> Verifying State
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" /> Failed
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-400 border border-slate-700">
            Cancelled
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-800 text-slate-400">
            Pending
          </span>
        );
    }
  };

  const isExecutionActive = task.status === 'RUNNING' || task.status === 'PLANNING' || task.status === 'VERIFYING';

  return (
    <div className="space-y-6">
      {/* Top Task Control Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono font-bold text-blue-400">Task #{task.id}</span>
            {getStatusBadge(task.status)}
          </div>
          <p className="text-xs text-slate-400">
            Scenario: <strong className="text-slate-200 capitalize">{task.scenario.replace('_', ' ')}</strong> • Created: {new Date(task.created_at).toLocaleTimeString()}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {task.status === 'PENDING' && (
            <button
              onClick={() => onRunTask(task.id)}
              className="bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-3.5 py-2 rounded-lg flex items-center gap-1.5 shadow transition-all active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Start Execution</span>
            </button>
          )}

          {isExecutionActive && (
            <button
              onClick={() => onCancelTask(task.id)}
              className="border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 font-medium text-xs px-3 py-2 rounded-lg flex items-center gap-1.5 transition-all"
            >
              <XOctagon className="w-3.5 h-3.5" />
              <span>Cancel Task</span>
            </button>
          )}
        </div>
      </div>

      {/* Two-Column Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Plan, Approval, and Completion Summary */}
        <div className="lg:col-span-5 space-y-4">
          <PlanCard 
            steps={task.steps || []} 
            goal={task.goal} 
            scenario={task.scenario} 
          />

          {/* Interactive Approval / Clarification Gate */}
          <ApprovalCard
            approvals={task.approvals || []}
            taskStatus={task.status}
            onDecision={onApprovalDecision}
          />

          {/* Final Completion Summary Card */}
          {task.result_summary && (
            <div className={`p-4 rounded-xl border text-xs space-y-2 ${
              task.status === 'COMPLETED' 
                ? 'bg-emerald-950/20 border-emerald-500/30' 
                : 'bg-rose-950/20 border-rose-500/30'
            }`}>
              <div className="flex items-center gap-2 font-bold text-sm">
                {task.status === 'COMPLETED' ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-emerald-200">Execution Complete & Verified</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-4 h-4 text-rose-400" />
                    <span className="text-rose-200">Execution Finished with Discrepancy</span>
                  </>
                )}
              </div>
              <p className="text-slate-300 leading-relaxed font-sans font-medium">
                {task.result_summary}
              </p>
              {task.completed_at && (
                <div className="text-[11px] text-slate-400 font-mono pt-1">
                  Finished At: {new Date(task.completed_at).toLocaleTimeString()}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Live Event Timeline & Evidence Verification */}
        <div className="lg:col-span-7 space-y-4">
          <TimelineCard 
            events={task.events || []} 
            toolExecutions={task.tool_executions || []} 
          />

          <EvidenceVerificationPanel 
            verifications={task.verifications || []} 
          />
        </div>
      </div>
    </div>
  );
};
