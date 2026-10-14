export type TaskStatus = 
  | 'PENDING'
  | 'PLANNING'
  | 'RUNNING'
  | 'WAITING_FOR_APPROVAL'
  | 'WAITING_FOR_INPUT'
  | 'VERIFYING'
  | 'COMPLETED'
  | 'PARTIALLY_COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type StepStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED';

export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED';

export interface TaskStep {
  id: string;
  task_id: string;
  step_order: number;
  description: string;
  status: StepStatus;
  tool_name?: string;
  created_at: string;
  completed_at?: string;
}

export interface TaskEvent {
  id: string;
  task_id: string;
  event_type: string;
  message: string;
  details_json?: string;
  created_at: string;
}

export interface ToolExecution {
  id: string;
  task_id: string;
  step_id?: string;
  tool_name: string;
  input_data_json?: string;
  output_data_json?: string;
  duration_ms: number;
  status: string;
  error_message?: string;
  retry_count: number;
  created_at: string;
}

export interface ApprovalRequest {
  id: string;
  task_id: string;
  action_name: string;
  payload_json: string;
  reason: string;
  status: ApprovalStatus;
  decision_by?: string;
  decision_at?: string;
  created_at: string;
}

export interface VerificationRecord {
  id: string;
  task_id: string;
  target_type: string;
  target_id: string;
  verified: boolean;
  field_results_json?: string;
  evidence_json?: string;
  details?: string;
  created_at: string;
}

export interface Task {
  id: string;
  goal: string;
  status: TaskStatus;
  scenario: string;
  result_summary?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  steps: TaskStep[];
  events: TaskEvent[];
  tool_executions: ToolExecution[];
  approvals: ApprovalRequest[];
  verifications: VerificationRecord[];
}

export interface InvoiceRecord {
  id: string;
  vendor: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  currency: string;
  subtotal: number;
  tax: number;
  total_amount: number;
  source_document_id?: string;
  status: string;
  created_at: string;
  updated_at: string;
}
