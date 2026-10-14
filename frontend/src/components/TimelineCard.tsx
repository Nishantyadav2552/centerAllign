import React, { useState, useRef, useEffect } from 'react';
import { 
  Activity, 
  Terminal, 
  ChevronDown, 
  ChevronUp, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  Clock, 
  Wrench,
  ShieldCheck,
  FileCheck,
  Eye
} from 'lucide-react';
import { TaskEvent, ToolExecution } from '../types';

interface TimelineCardProps {
  events: TaskEvent[];
  toolExecutions: ToolExecution[];
}

export const TimelineCard: React.FC<TimelineCardProps> = ({ events, toolExecutions }) => {
  const [expandedItems, setExpandedItems] = useState<Record<string, boolean>>({});
  const scrollRef = useRef<HTMLDivElement>(null);

  const toggleExpand = (id: string) => {
    setExpandedItems(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const getEventBadge = (type: string) => {
    switch (type) {
      case 'TOOL_SUCCESS':
        return <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Success</span>;
      case 'RETRY_ATTEMPT':
        return <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
          <RefreshCw className="w-2.5 h-2.5 animate-spin" /> Retry
        </span>;
      case 'APPROVAL_REQUESTED':
      case 'INPUT_REQUESTED':
        return <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-500 text-slate-950">Gate</span>;
      case 'TASK_COMPLETED':
        return <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">Verified</span>;
      case 'UNRECOVERABLE_ERROR':
      case 'VERIFICATION_FAILED':
        return <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">Error</span>;
      default:
        return <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{type}</span>;
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'TOOL_SUCCESS':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
      case 'RETRY_ATTEMPT':
        return <RefreshCw className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
      case 'APPROVAL_REQUESTED':
      case 'INPUT_REQUESTED':
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
      case 'VERIFICATION_START':
      case 'TASK_COMPLETED':
        return <ShieldCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />;
      default:
        return <Activity className="w-3.5 h-3.5 text-slate-500 shrink-0" />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm flex flex-col h-[520px]">
      {/* Card Header */}
      <div className="p-4 border-b border-slate-800/80 bg-slate-950/40 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <span>Live Execution Trace & Tool Timeline</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span>{events.length} Events</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
        </div>
      </div>

      {/* Events Feed */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto divide-y divide-slate-800/50 p-2 space-y-1">
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500">
            Awaiting task launch...
          </div>
        ) : (
          events.map((evt, idx) => {
            const isExpanded = expandedItems[evt.id] || false;
            let parsedDetails: any = null;
            if (evt.details_json) {
              try {
                parsedDetails = JSON.parse(evt.details_json);
              } catch (e) {
                parsedDetails = evt.details_json;
              }
            }

            return (
              <div 
                key={evt.id || idx}
                className="p-2.5 rounded-lg hover:bg-slate-800/40 transition-colors text-xs space-y-1.5"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 min-w-0">
                    {getEventIcon(evt.event_type)}
                    <span className="font-semibold text-slate-200 truncate">
                      {evt.message}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {getEventBadge(evt.event_type)}
                    <span className="text-[10px] text-slate-500 font-mono">
                      {evt.created_at ? new Date(evt.created_at).toLocaleTimeString() : ''}
                    </span>
                  </div>
                </div>

                {/* Expandable Technical Data Payload */}
                {parsedDetails && (
                  <div>
                    <button
                      onClick={() => toggleExpand(evt.id)}
                      className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 font-mono transition-colors"
                    >
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      <span>{isExpanded ? 'Hide Payload' : 'View Observation Payload'}</span>
                    </button>
                    {isExpanded && (
                      <pre className="mt-1.5 p-2 bg-slate-950 rounded border border-slate-800/80 text-[10px] font-mono text-slate-300 overflow-x-auto max-h-48 leading-relaxed">
                        {JSON.stringify(parsedDetails, null, 2)}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
