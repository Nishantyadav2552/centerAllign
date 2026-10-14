import React, { useState } from 'react';
import { X, Play, Sparkles, AlertTriangle, ShieldCheck, Ticket, Layers } from 'lucide-react';

interface NewTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (goal: string, scenario: string) => void;
}

export const NewTaskModal: React.FC<NewTaskModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [goal, setGoal] = useState(
    'Find the latest invoice from Acme Corp, extract the invoice number, invoice date, total amount, and due date, enter the information into our finance system, and verify that it was saved correctly.'
  );
  const [scenario, setScenario] = useState('standard');

  if (!isOpen) return null;

  const examplePrompts = [
    {
      title: 'Scenario A: Standard Autonomous Workflow',
      scenario: 'standard',
      badge: 'Success',
      text: 'Find the latest invoice from Acme Corp, extract the invoice number, invoice date, total amount, and due date, enter the information into our finance system, and verify that it was saved correctly.',
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />
    },
    {
      title: 'Scenario B: Recoverable Transient Failure',
      scenario: 'recoverable_failure',
      badge: 'Self-Healing',
      text: 'Find the latest invoice from Acme Corp, extract fields, enter into finance system, and verify. (Simulates vendor 503 gateway failure with automated bounded retry recovery).',
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />
    },
    {
      title: 'Scenario C: Ambiguous Invoice Terms',
      scenario: 'ambiguous_invoice',
      badge: 'Human-in-Loop',
      text: 'Find the latest invoice from Acme Corp with ambiguous payment terms, pause to request human clarification without hallucinating, and complete upon supervisor input.',
      icon: <Sparkles className="w-4 h-4 text-blue-400" />
    },
    {
      title: 'Scenario E: Support Ticket Generalization',
      scenario: 'generalization',
      badge: 'Generalization',
      text: 'Find the latest support ticket from customer Acme Corp, summarize the issue, create an internal follow-up task, and verify that the task exists.',
      icon: <Ticket className="w-4 h-4 text-indigo-400" />
    }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    onSubmit(goal.trim(), scenario);
    onClose();
  };

  const handleSelectExample = (ex: typeof examplePrompts[0]) => {
    setGoal(ex.text);
    setScenario(ex.scenario);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center">
              <Play className="w-4 h-4 text-blue-400 fill-current" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Launch New Autonomous Goal</h3>
              <p className="text-xs text-slate-400">Natural-language business task delegation</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Example Suggestions */}
          <div>
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Select Preset Demonstration Scenario:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {examplePrompts.map((ex) => (
                <button
                  key={ex.title}
                  type="button"
                  onClick={() => handleSelectExample(ex)}
                  className={`p-3 rounded-xl border text-left text-xs transition-all flex flex-col justify-between gap-1.5 ${
                    scenario === ex.scenario
                      ? 'bg-blue-950/40 border-blue-500 shadow-sm'
                      : 'bg-slate-950/50 border-slate-800/80 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <div className="flex items-center gap-1.5 font-semibold text-white">
                      {ex.icon}
                      <span className="truncate">{ex.title.split(':')[0]}</span>
                    </div>
                    <span className="text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {ex.badge}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">
                    {ex.text}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Goal Input */}
          <div>
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
              Natural Language Instruction:
            </label>
            <textarea
              rows={4}
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="Describe the business task in natural language..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-blue-500 leading-relaxed font-sans"
            />
          </div>

          {/* Scenario Configuration Dropdown */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400">Execution Mode / Sandbox Hook:</span>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-mono"
            >
              <option value="standard">Standard (Scenario A)</option>
              <option value="recoverable_failure">Recoverable 503 Failure (Scenario B)</option>
              <option value="ambiguous_invoice">Ambiguous Due Date (Scenario C)</option>
              <option value="generalization">Support Ticket Generalization (Scenario E)</option>
            </select>
          </div>

          {/* Submit Controls */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-lg shadow-blue-600/25 transition-all flex items-center gap-2 active:scale-95"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Synthesize Plan & Execute</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
