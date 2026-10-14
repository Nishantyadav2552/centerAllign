import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  ListOrdered, 
  Play, 
  Database, 
  Globe, 
  BarChart3, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Plus,
  RefreshCw,
  Search,
  Layers
} from 'lucide-react';
import { Task, TaskStatus } from './types';
import { api } from './services/api';
import { Header } from './components/Header';
import { TaskWorkspace } from './components/TaskWorkspace';
import { FinanceExplorer } from './components/FinanceExplorer';
import { VendorPortalModal } from './components/VendorPortalModal';
import { EvaluationDashboard } from './components/EvaluationDashboard';
import { NewTaskModal } from './components/NewTaskModal';

export const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'workspace' | 'finance' | 'portal' | 'eval'>('workspace');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load all tasks
  const loadTasks = async () => {
    try {
      const data = await api.getTasks();
      setTasks(data);
      if (!selectedTaskId && data.length > 0) {
        setSelectedTaskId(data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  // Poll selected task for live progress updates
  useEffect(() => {
    if (!selectedTaskId) return;

    const interval = setInterval(async () => {
      try {
        const updated = await api.getTask(selectedTaskId);
        setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)));
      } catch (e) {
        // Poll error
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [selectedTaskId]);

  const selectedTask = tasks.find(t => t.id === selectedTaskId) || null;

  const handleCreateTask = async (goal: string, scenario: string) => {
    try {
      const newTask = await api.createTask(goal, scenario);
      setTasks(prev => [newTask, ...prev]);
      setSelectedTaskId(newTask.id);
      setActiveTab('workspace');
    } catch (e) {
      console.error(e);
    }
  };

  const handleRunTask = async (taskId: string) => {
    try {
      const updated = await api.runTask(taskId);
      setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)));
    } catch (e) {
      console.error(e);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      const updated = await api.cancelTask(taskId);
      setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)));
    } catch (e) {
      console.error(e);
    }
  };

  const handleApprovalDecision = async (
    approvalId: string, 
    decision: 'APPROVED' | 'REJECTED', 
    clarificationValue?: string
  ) => {
    try {
      await api.submitApprovalDecision(approvalId, decision, 'Human Supervisor', clarificationValue);
      if (selectedTaskId) {
        const updated = await api.getTask(selectedTaskId);
        setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleQuickScenario = (scenario: string, goal: string) => {
    handleCreateTask(goal, scenario);
  };

  const getStatusBadgeSmall = (status: TaskStatus) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="w-2 h-2 rounded-full bg-emerald-400" title="Completed" />;
      case 'WAITING_FOR_APPROVAL':
      case 'WAITING_FOR_INPUT':
        return <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" title="Needs Action" />;
      case 'RUNNING':
      case 'PLANNING':
      case 'VERIFYING':
        return <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" title="Running" />;
      case 'FAILED':
        return <span className="w-2 h-2 rounded-full bg-rose-400" title="Failed" />;
      default:
        return <span className="w-2 h-2 rounded-full bg-slate-600" title="Pending" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Enterprise Header */}
      <Header
        tasks={tasks}
        activeTab={activeTab}
        setActiveTab={setActiveTab as any}
        onNewTaskClick={() => setIsModalOpen(true)}
        onQuickScenario={handleQuickScenario}
      />

      {/* Main Content Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Recent Tasks Drawer */}
        <aside className="w-80 border-r border-slate-800 bg-slate-900/40 p-4 shrink-0 hidden md:flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                <span>Task Sessions</span>
              </span>
              <button
                onClick={() => setIsModalOpen(true)}
                className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
                title="Launch New Task"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {/* Tasks List */}
            <div className="space-y-1.5 overflow-y-auto max-h-[calc(100vh-220px)] pr-1">
              {tasks.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500">
                  No tasks recorded. Launch one to see execution!
                </div>
              ) : (
                tasks.map((t) => {
                  const isSelected = t.id === selectedTaskId;
                  return (
                    <button
                      key={t.id}
                      onClick={() => {
                        setSelectedTaskId(t.id);
                        setActiveTab('workspace');
                      }}
                      className={`w-full text-left p-3 rounded-xl border text-xs transition-all flex flex-col gap-1.5 ${
                        isSelected
                          ? 'bg-blue-600/10 border-blue-500/50 shadow-sm'
                          : 'bg-slate-900/60 border-slate-800/80 hover:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-1">
                        <div className="flex items-center gap-1.5">
                          {getStatusBadgeSmall(t.status)}
                          <span className="font-mono font-bold text-[11px] text-slate-300">
                            #{t.id.slice(-6)}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {t.created_at ? new Date(t.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                        </span>
                      </div>
                      <p className="text-slate-300 line-clamp-2 leading-relaxed">
                        {t.goal}
                      </p>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Sidebar Footer Info */}
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
            <div className="flex items-center justify-between text-slate-300 font-semibold">
              <span>Environment:</span>
              <span className="text-emerald-400 font-mono">Controlled Sandbox</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Engine:</span>
              <span className="text-blue-400 font-mono">CentrAlign 1.0</span>
            </div>
          </div>
        </aside>

        {/* Center Main Tab View */}
        <main className="flex-1 overflow-y-auto p-6">
          {activeTab === 'workspace' && (
            <TaskWorkspace
              task={selectedTask}
              onRunTask={handleRunTask}
              onCancelTask={handleCancelTask}
              onApprovalDecision={handleApprovalDecision}
            />
          )}

          {activeTab === 'finance' && <FinanceExplorer />}

          {activeTab === 'portal' && <VendorPortalModal />}

          {activeTab === 'eval' && <EvaluationDashboard />}
        </main>
      </div>

      {/* New Task Launch Modal */}
      <NewTaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateTask}
      />
    </div>
  );
};

export default App;
