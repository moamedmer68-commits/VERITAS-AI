export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "customer" | "agent" | "admin";
};

export type Conversation = {
  id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations_json: string;
  created_at: string;
};

export type Citation = {
  title: string;
  source: string;
  score: number;
  excerpt: string;
};

export type ToolTrace = {
  tool: string;
  status: string;
  duration_ms: number;
  preview: string;
};

export type AgentResponse = {
  conversation_id: string;
  message_id: string | null;
  answer: string;
  citations: Citation[];
  traces: ToolTrace[];
  pending_approval_id: string | null;
  mode: string;
};

export type Order = {
  id: string;
  product_name: string;
  amount: number;
  status: string;
  tracking_number: string | null;
  refundable: boolean;
};

export type Approval = {
  id: string;
  thread_id: string;
  tool_name: string;
  tool_args_json: string;
  risk_level: string;
  status: string;
  reviewer_note: string;
  created_at: string;
};

export type Ticket = {
  id: string;
  subject: string;
  description: string;
  priority: string;
  status: string;
  created_at: string;
};

export type KnowledgeDocument = {
  id: string;
  title: string;
  source: string;
  status: string;
  chunk_count: number;
  created_at: string;
};

export type Metrics = {
  conversations: number;
  open_tickets: number;
  pending_approvals: number;
  knowledge_documents: number;
  tool_success_rate: number;
  average_tool_latency_ms: number;
  recent_tools: Array<Record<string, string | number>>;
};

