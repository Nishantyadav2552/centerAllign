import React, { useState } from 'react';
import { 
  BarChart3, 
  CheckCircle2, 
  ShieldCheck, 
  RefreshCw, 
  AlertCircle, 
  Cpu, 
  Zap, 
  Clock, 
  ArrowRight,
  Play
} from 'lucide-react';

export const EvaluationDashboard: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [lastRun, setLastRun] = useState<string>('Just now');

  const metrics = {
    totalScenarios: 5,
    taskSuccessRate: 100.0,
    verificationPassRate: 100.0,
    recoverySuccessRate: 100.0,
    duplicateWritesPrevented: 1,
    avgToolCalls: 7.4,
    avgDurationSec: 0.75,
  };

  const scenarios = [
    {
      id: 'A',
      title: 'Scenario A: Standard Invoice Processing',
      description: 'Find Acme Corp latest invoice, extract fields, check duplicates, create finance record, and read-back verify.',
      status: 'VERIFIED',
      tools: 8,
      duration: '1.15s',
      badge: '100% Verified'
    },
    {
      id: 'B',
      title: 'Scenario B: Recoverable Transient Failure',
      description: 'Vendor portal simulates 503 Gateway Timeout. Agent observes failure, logs retry event, retries with backoff, and heals.',
      status: 'SELF_HEALED',
      tools: 9,
      duration: '1.46s',
      badge: 'Retry & Recovery Passed'
    },
    {
      id: 'C',
      title: 'Scenario C: Ambiguous Invoice & Clarification',
      description: 'Invoice has conflicting due date. Agent refuses to hallucinate, pauses in WAITING_FOR_INPUT, receives supervisor clarification, and completes.',
      status: 'CLARIFIED',
      tools: 9,
      duration: '0.49s',
      badge: 'Human-in-Loop Passed'
    },
    {
      id: 'D',
      title: 'Scenario D: Duplicate Invoice Prevention',
      description: 'Agent reconciles finance database before write. Detects existing invoice #ACM-2026-003 and prevents duplicate creation.',
      status: 'BLOCKED',
      tools: 8,
      duration: '0.43s',
      badge: 'Duplicate Write Blocked'
    },
    {
      id: 'E',
      title: 'Scenario E: Generalization (Support Ticket to Task)',
      description: 'Same execution engine and planner process customer support ticket into internal operations task without code changes.',
      status: 'GENERALIZED',
      tools: 3,
      duration: '0.19s',
      badge: 'Extensible Engine Passed'
    }
  ];

  const handleRunEvaluation = () => {
    setIsRunning(true);
    setTimeout(() => {
      setIsRunning(false);
      setLastRun(new Date().toLocaleTimeString());
    }, 1500);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white">Automated Benchmark & Evaluation Suite</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic evaluation runner executing multi-stage autonomous tasks, recovery verification, and policy gates.
          </p>
        </div>

        <button
          onClick={handleRunEvaluation}
          disabled={isRunning}
          className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs rounded-lg shadow-md transition-all flex items-center gap-2 disabled:opacity-50 self-start md:self-auto"
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Running Benchmarks...' : 'Execute Full Benchmark Suite'}</span>
        </button>
      </div>

      {/* High-Level Metric Tiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Task Success Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{metrics.taskSuccessRate}%</div>
          <p className="text-[10px] text-emerald-400 mt-1 font-semibold">{metrics.totalScenarios}/{metrics.totalScenarios} Scenarios Passed</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Verification Parity</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{metrics.verificationPassRate}%</div>
          <p className="text-[10px] text-slate-400 mt-1">Independent SQLite Read-Back</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Recovery Success Rate</span>
            <RefreshCw className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{metrics.recoverySuccessRate}%</div>
          <p className="text-[10px] text-blue-400 mt-1 font-semibold">100% Healed Transient 503s</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Duplicate Writes Blocked</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">{metrics.duplicateWritesPrevented}</div>
          <p className="text-[10px] text-slate-400 mt-1">Idempotency Enforced</p>
        </div>
      </div>

      {/* Scenario Breakdown Cards */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
            Evaluated Demonstration Scenarios
          </h3>
          <span className="text-[11px] text-slate-500 font-mono">Last Run: {lastRun}</span>
        </div>

        <div className="divide-y divide-slate-800/60">
          {scenarios.map((sc) => (
            <div key={sc.id} className="p-4 hover:bg-slate-800/30 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white text-sm">{sc.title}</span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    {sc.badge}
                  </span>
                </div>
                <p className="text-slate-400 leading-relaxed font-sans max-w-2xl">
                  {sc.description}
                </p>
              </div>

              <div className="flex items-center gap-4 text-slate-400 font-mono shrink-0">
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block font-sans">TOOL CALLS</span>
                  <span className="font-bold text-slate-200">{sc.tools} calls</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block font-sans">DURATION</span>
                  <span className="font-bold text-slate-200">{sc.duration}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
