import { Task, InvoiceRecord, ApprovalRequest } from '../types';

const API_BASE = '/api';

export const api = {
  async getTasks(): Promise<Task[]> {
    const res = await fetch(`${API_BASE}/tasks`);
    if (!res.ok) throw new Error('Failed to fetch tasks');
    return res.json();
  },

  async getTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}`);
    if (!res.ok) throw new Error(`Failed to fetch task ${taskId}`);
    return res.json();
  },

  async createTask(goal: string, scenario: string = 'standard'): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal, scenario }),
    });
    if (!res.ok) throw new Error('Failed to create task');
    return res.json();
  },

  async runTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/run`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to run task ${taskId}`);
    return res.json();
  },

  async cancelTask(taskId: string): Promise<Task> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Failed to cancel task ${taskId}`);
    return res.json();
  },

  async submitApprovalDecision(
    approvalId: string,
    decision: 'APPROVED' | 'REJECTED',
    decisionBy: string = 'Human Supervisor',
    clarificationValue?: string
  ): Promise<ApprovalRequest> {
    const res = await fetch(`${API_BASE}/approvals/${approvalId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision,
        decision_by: decisionBy,
        clarification_value: clarificationValue,
      }),
    });
    if (!res.ok) throw new Error('Failed to submit approval decision');
    return res.json();
  },

  async getInvoices(): Promise<InvoiceRecord[]> {
    const res = await fetch(`${API_BASE}/finance/invoices`);
    if (!res.ok) throw new Error('Failed to fetch finance invoices');
    return res.json();
  },

  async getTaskReport(taskId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/tasks/${taskId}/report`);
    if (!res.ok) throw new Error('Failed to fetch report');
    return res.json();
  },

  async getHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  }
};
