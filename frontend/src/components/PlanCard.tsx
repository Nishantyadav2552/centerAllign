import React from 'react';
import { 
  CheckCircle2, 
  Circle, 
  Loader2, 
  AlertCircle, 
  ListOrdered, 
  Wrench,
  Clock,
  ChevronRight
} from 'lucide-react';
import { TaskStep, StepStatus } from '../types';

interface PlanCardProps {
  steps: TaskStep[];
  goal: string;
  scenario: string;
}

export const PlanCard: React.FC<PlanCardProps> = ({ steps, goal, scenario }) => {
  const getStatusIcon = (status: StepStatus) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
      case 'RUNNING':
        return <Loader2 className="w-4 h-4 text-blue-400 animate-spin shrink-0" />;
      case 'FAILED':
        return <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
      default:
        return <Circle className="w-4 h-4 text-slate-500 shrink-0" />;
    }
  };

  const getStatusBadge = (status: StepStatus) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Done</span>;
      case 'RUNNING':
        return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse">Running</span>;
      case 'FAILED':
        return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Failed</span>;
      default:
        return <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/50">Queued</span>;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <ListOrdered className="w-4 h-4 text-blue-400" />
          <span>Execution Plan</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">
            {steps.filter(s => s.status === 'COMPLETED').length}/{steps.length} Steps
          </span>
          <span className="px-2 py-0.5 text-[10px] rounded font-medium bg-slate-800 text-slate-300 border border-slate-700">
            {scenario}
          </span>
        </div>
      </div>

      {/* Goal Summary */}
      <div className="px-4 py-3 bg-blue-950/20 border-b border-blue-900/30 text-xs">
        <span className="text-blue-300 font-semibold uppercase tracking-wider block text-[10px] mb-1">Target Objective:</span>
        <p className="text-slate-200 leading-relaxed font-sans">{goal}</p>
      </div>

      {/* Step List */}
      <div className="divide-y divide-slate-800/60 p-2">
        {steps.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            <span>Analyzing natural language goal and synthesizing plan...</span>
          </div>
        ) : (
          steps.map((step) => {
            const isCurrent = step.status === 'RUNNING';
            return (
              <div
                key={step.id || step.step_order}
                className={`p-3 rounded-lg transition-all flex items-start gap-3 text-xs ${
                  isCurrent
                    ? 'bg-blue-950/30 border border-blue-500/30'
                    : 'hover:bg-slate-800/40'
                }`}
              >
                <div className="pt-0.5">{getStatusIcon(step.status)}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="font-semibold text-slate-200">
                      Step {step.step_order}
                    </span>
                    {getStatusBadge(step.status)}
                  </div>
                  <p className="text-slate-300 font-normal leading-snug">
                    {step.description}
                  </p>
                  {step.tool_name && (
                    <div className="mt-2 flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
                      <Wrench className="w-3 h-3 text-blue-400" />
                      <span className="bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 text-blue-300">
                        {step.tool_name}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
