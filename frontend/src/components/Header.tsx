import React from 'react';
import { 
  Bot, 
  Play, 
  Sparkles, 
  Database, 
  ExternalLink, 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  Clock, 
  BarChart3,
  Globe
} from 'lucide-react';
import { Task } from '../types';

interface HeaderProps {
  tasks: Task[];
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onNewTaskClick: () => void;
  onQuickScenario: (scenario: string, goal: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  tasks,
  activeTab,
  setActiveTab,
  onNewTaskClick,
  onQuickScenario,
}) => {
  const completedCount = tasks.filter(t => t.status === 'COMPLETED').length;
  const waitingApprovalCount = tasks.filter(t => t.status === 'WAITING_FOR_APPROVAL' || t.status === 'WAITING_FOR_INPUT').length;
  const runningCount = tasks.filter(t => t.status === 'RUNNING' || t.status === 'PLANNING' || t.status === 'VERIFYING').length;

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40 px-6 py-3">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Brand & Status */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                CentrAlign <span className="text-blue-400 font-semibold text-lg">Operator</span>
              </h1>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Autonomy Engine
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Autonomous AI Employee • Cross-System Execution & Verified Persistence
            </p>
          </div>
        </div>

        {/* Global Metric Indicators */}
        <div className="flex items-center gap-4 bg-slate-950/60 border border-slate-800/80 px-4 py-2 rounded-xl text-xs">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">Total:</span>
            <span className="font-semibold text-white">{tasks.length}</span>
          </div>
          <div className="w-px h-4 bg-slate-800" />
          <div className="flex items-center gap-1.5 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span className="text-slate-400">Verified:</span>
            <span className="font-semibold">{completedCount}</span>
          </div>
          <div className="w-px h-4 bg-slate-800" />
          <div className="flex items-center gap-1.5 text-amber-400">
            <Clock className="w-3.5 h-3.5" />
            <span className="text-slate-400">Awaiting Action:</span>
            <span className="font-semibold">{waitingApprovalCount}</span>
          </div>
          {runningCount > 0 && (
            <>
              <div className="w-px h-4 bg-slate-800" />
              <div className="flex items-center gap-1.5 text-blue-400 font-medium">
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                <span>Running ({runningCount})</span>
              </div>
            </>
          )}
        </div>

        {/* Navigation Tabs & Primary Actions */}
        <div className="flex items-center gap-2">
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setActiveTab('workspace')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeTab === 'workspace'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Workspace
            </button>
            <button
              onClick={() => setActiveTab('finance')}
              className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
                activeTab === 'finance'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Database className="w-3 h-3" />
              Finance DB
            </button>
            <button
              onClick={() => setActiveTab('portal')}
              className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
                activeTab === 'portal'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Globe className="w-3 h-3" />
              Vendor Portal
            </button>
            <button
              onClick={() => setActiveTab('eval')}
              className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
                activeTab === 'eval'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <BarChart3 className="w-3 h-3" />
              Evaluation Suite
            </button>
          </div>

          <button
            onClick={onNewTaskClick}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs px-3.5 py-2 rounded-lg shadow-md transition-all hover:shadow-blue-500/25 active:scale-95"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            New Business Goal
          </button>
        </div>
      </div>
    </header>
  );
};
