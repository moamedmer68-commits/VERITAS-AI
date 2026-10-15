"use client";

import Image from "next/image";
import { FormEvent, useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import {
  Activity,
  Archive,
  BookOpen,
  Bot,
  Check,
  ChevronRight,
  CircleAlert,
  Clock3,
  FileText,
  Headphones,
  LogOut,
  MessageSquare,
  PackageSearch,
  Plus,
  Send,
  ShieldCheck,
  ThumbsDown,
  ThumbsUp,
  TicketCheck,
  Upload,
  UserRound,
  X,
} from "lucide-react";

import { api, login, streamAgentMessage } from "@/lib/api";
import type {
  Approval,
  Citation,
  Conversation,
  KnowledgeDocument,
  Message,
  Metrics,
  Order,
  Ticket,
  ToolTrace,
  User,
} from "@/lib/types";

type View = "chat" | "orders" | "approvals" | "knowledge" | "tickets" | "metrics";
type Session = { token: string; user: User };

const AUTH_KEY = "resolveflow_session";
const AUTH_EVENT = "resolveflow-auth";

function subscribeAuth(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener(AUTH_EVENT, callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(AUTH_EVENT, callback);
  };
}

function getAuthSnapshot() {
  return window.localStorage.getItem(AUTH_KEY) ?? "";
}

function getServerAuthSnapshot() {
  return "";
}

const navigation = [
  { id: "chat" as View, label: "会话工作台", icon: MessageSquare },
  { id: "orders" as View, label: "订单上下文", icon: PackageSearch },
  { id: "approvals" as View, label: "人工审批", icon: ShieldCheck, staff: true },
  { id: "knowledge" as View, label: "知识库", icon: FileText, staff: true },
  { id: "tickets" as View, label: "工单中心", icon: TicketCheck },
  { id: "metrics" as View, label: "运行指标", icon: Activity, staff: true },
];

export default function Home() {
  const rawSession = useSyncExternalStore(subscribeAuth, getAuthSnapshot, getServerAuthSnapshot);
  const session = useMemo<Session | null>(() => {
    try {
      return rawSession ? JSON.parse(rawSession) as Session : null;
    } catch {
      return null;
    }
  }, [rawSession]);

  const handleLogin = (nextToken: string, nextUser: User) => {
    localStorage.setItem(AUTH_KEY, JSON.stringify({ token: nextToken, user: nextUser }));
    window.dispatchEvent(new Event(AUTH_EVENT));
  };

  const handleLogout = () => {
    localStorage.removeItem(AUTH_KEY);
    window.dispatchEvent(new Event(AUTH_EVENT));
  };

  if (!session) return <LoginScreen onLogin={handleLogin} />;
  return <Workspace token={session.token} user={session.user} onLogout={handleLogout} />;
}

function LoginScreen({ onLogin }: { onLogin: (token: string, user: User) => void }) {
  const [email, setEmail] = useState("customer@resolveflow.dev");
  const [password, setPassword] = useState("customer123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const result = await login(email, password);
      onLogin(result.access_token, result.user);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  const chooseDemo = (role: "customer" | "admin") => {
    setEmail(role === "customer" ? "customer@resolveflow.dev" : "admin@resolveflow.dev");
    setPassword(role === "customer" ? "customer123" : "admin123");
  };

  return (
    <main className="login-shell">
      <section className="login-brand">
        <Image src="/resolveflow-logo.png" alt="ResolveFlow" width={92} height={92} priority />
        <h1>ResolveFlow</h1>
        <p>企业智能客服与工单协同 Agent</p>
        <div className="system-strip">
          <span><Bot size={16} /> LangGraph Agent</span>
          <span><BookOpen size={16} /> RAG</span>
          <span><ShieldCheck size={16} /> Human approval</span>
        </div>
      </section>
      <form className="login-panel" onSubmit={submit}>
        <div>
          <span className="eyebrow">工作台登录</span>
          <h2>进入客服运营中心</h2>
        </div>
        <label>邮箱<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
        <label>密码<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        {error && <p className="error-line"><CircleAlert size={16} />{error}</p>}
        <button className="primary-button" disabled={loading}>{loading ? "正在连接…" : "登录"}<ChevronRight size={17} /></button>
        <div className="demo-actions">
          <button type="button" onClick={() => chooseDemo("customer")}><UserRound size={16} />客户账号</button>
          <button type="button" onClick={() => chooseDemo("admin")}><Headphones size={16} />主管账号</button>
        </div>
      </form>
    </main>
  );
}

function Workspace({ token, user, onLogout }: { token: string; user: User; onLogout: () => void }) {
  const [view, setView] = useState<View>("chat");
  const isStaff = user.role !== "customer";
  const visibleNavigation = navigation.filter((item) => !item.staff || isStaff);

  return (
    <main className="workspace">
      <aside className="sidebar">
        <div className="brand-lockup">
          <Image src="/resolveflow-logo.png" alt="" width={42} height={42} />
          <div><strong>ResolveFlow</strong><span>Agent Console</span></div>
        </div>
        <nav>
          {visibleNavigation.map((item) => {
            const Icon = item.icon;
            return <button key={item.id} className={view === item.id ? "active" : ""} onClick={() => setView(item.id)}><Icon size={18} /><span>{item.label}</span></button>;
          })}
        </nav>
        <div className="sidebar-user">
          <div className="avatar">{user.full_name.slice(0, 1)}</div>
          <div><strong>{user.full_name}</strong><span>{user.role}</span></div>
          <button className="icon-button" title="退出登录" onClick={onLogout}><LogOut size={17} /></button>
        </div>
      </aside>
      <section className="content">
        {view === "chat" && <ChatView token={token} />}
        {view === "orders" && <OrdersView token={token} />}
        {view === "approvals" && <ApprovalsView token={token} />}
        {view === "knowledge" && <KnowledgeView token={token} />}
        {view === "tickets" && <TicketsView token={token} />}
        {view === "metrics" && <MetricsView token={token} />}
      </section>
    </main>
  );
}

function PageHeader({ eyebrow, title, action }: { eyebrow: string; title: string; action?: React.ReactNode }) {
  return <header className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1></div>{action}</header>;
}

function ChatView({ token }: { token: string }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("就绪");
  const [traces, setTraces] = useState<ToolTrace[]>([]);
  const [citations, setCitations] = useState<Citation[]>([]);

  const fetchConversations = useCallback(
    () => api<Conversation[]>("/conversations", token),
    [token],
  );

  const refreshConversations = useCallback(async () => {
    const items = await fetchConversations();
    setConversations(items);
    setActiveId((current) => current || items[0]?.id || "");
  }, [fetchConversations]);

  useEffect(() => {
    let current = true;
    void fetchConversations().then((items) => {
      if (!current) return;
      setConversations(items);
      setActiveId((active) => active || items[0]?.id || "");
    });
    return () => { current = false; };
  }, [fetchConversations]);
  useEffect(() => {
    if (!activeId) return;
    void api<Message[]>(`/conversations/${activeId}/messages`, token).then(setMessages);
  }, [activeId, token]);

  const createConversation = async () => {
    const created = await api<Conversation>("/conversations", token, { method: "POST", body: JSON.stringify({ title: "新会话" }) });
    setConversations((current) => [created, ...current]);
    setActiveId(created.id);
    setMessages([]);
  };

  const send = async () => {
    if (!input.trim() || loading) return;
    let conversationId = activeId;
    if (!conversationId) {
      const created = await api<Conversation>("/conversations", token, { method: "POST", body: JSON.stringify({ title: input.slice(0, 30) }) });
      conversationId = created.id;
      setActiveId(created.id);
    }
    const optimistic: Message = { id: crypto.randomUUID(), role: "user", content: input, citations_json: "[]", created_at: new Date().toISOString() };
    setMessages((current) => [...current, optimistic]);
    const content = input;
    setInput("");
    setLoading(true);
    setStatus("规划执行路径");
    setTraces([]);
    try {
      const result = await streamAgentMessage(conversationId, content, token, (event, data) => {
        if (event === "tool") {
          setStatus("工具执行中");
          setTraces((current) => [...current, data as ToolTrace]);
        }
      });
      setMessages((current) => [...current, { id: result.message_id ?? crypto.randomUUID(), role: "assistant", content: result.answer, citations_json: JSON.stringify(result.citations), created_at: new Date().toISOString() }]);
      setCitations(result.citations);
      setTraces(result.traces);
      setStatus(result.pending_approval_id ? "等待人工审批" : `完成 · ${result.mode}`);
      await refreshConversations();
    } catch (reason) {
      setStatus(reason instanceof Error ? reason.message : "请求失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-page">
      <PageHeader eyebrow="CUSTOMER OPERATIONS" title="会话工作台" action={<button className="secondary-button" onClick={createConversation}><Plus size={17} />新会话</button>} />
      <div className="chat-layout">
        <aside className="conversation-list">
          <span className="section-label">最近会话</span>
          {conversations.map((conversation) => <button key={conversation.id} className={activeId === conversation.id ? "selected" : ""} onClick={() => setActiveId(conversation.id)}><MessageSquare size={16} /><span>{conversation.title}</span><small>{new Date(conversation.updated_at).toLocaleDateString("zh-CN")}</small></button>)}
          {!conversations.length && <div className="empty-compact">暂无会话</div>}
        </aside>
        <section className="chat-thread">
          <div className="thread-status"><span className={loading ? "status-dot working" : "status-dot"} />{status}</div>
          <div className="messages">
            {!messages.length && <div className="empty-state"><Bot size={28} /><h3>开始一次客服对话</h3><p>可尝试：查询订单 RF20260801001 的物流，或为该订单申请退款。</p></div>}
            {messages.map((message) => <article key={message.id} className={`message ${message.role}`}><div className="message-role">{message.role === "assistant" ? <Bot size={17} /> : <UserRound size={17} />}</div><div><p>{message.content}</p>{message.role === "assistant" && <FeedbackButtons token={token} messageId={message.id} />}</div></article>)}
          </div>
          <div className="composer"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }} placeholder="输入客户问题或订单号…" /><button className="send-button" title="发送" onClick={() => void send()} disabled={loading || !input.trim()}><Send size={19} /></button></div>
        </section>
        <aside className="context-panel">
          <section><span className="section-label">工具轨迹</span>{traces.length ? traces.map((trace, index) => <div className="trace-row" key={`${trace.tool}-${index}`}><Check size={15} /><div><strong>{trace.tool}</strong><span>{trace.duration_ms} ms</span></div></div>) : <div className="empty-compact">等待 Agent 调用工具</div>}</section>
          <section><span className="section-label">RAG 引用</span>{citations.length ? citations.map((citation) => <div className="citation-row" key={citation.source}><FileText size={15} /><div><strong>{citation.title}</strong><span>{citation.source} · {citation.score.toFixed(2)}</span></div></div>) : <div className="empty-compact">暂无检索来源</div>}</section>
        </aside>
      </div>
    </div>
  );
}

function FeedbackButtons({ token, messageId }: { token: string; messageId: string }) {
  const [sent, setSent] = useState(false);
  const submit = async (rating: number) => {
    await api("/conversations/feedback", token, { method: "POST", body: JSON.stringify({ message_id: messageId, rating }) });
    setSent(true);
  };
  if (sent) return <span className="feedback-sent">已记录反馈</span>;
  return <div className="feedback-buttons"><button title="有帮助" onClick={() => void submit(1)}><ThumbsUp size={14} /></button><button title="需改进" onClick={() => void submit(-1)}><ThumbsDown size={14} /></button></div>;
}

function OrdersView({ token }: { token: string }) {
  const [items, setItems] = useState<Order[]>([]);
  useEffect(() => { void api<Order[]>("/orders", token).then(setItems); }, [token]);
  return <><PageHeader eyebrow="CUSTOMER DATA" title="订单上下文" /><div className="table-shell"><table><thead><tr><th>订单号</th><th>商品</th><th>金额</th><th>状态</th><th>物流单号</th><th>退款资格</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td className="mono">{item.id}</td><td>{item.product_name}</td><td>¥{item.amount.toFixed(2)}</td><td><Status value={item.status} /></td><td className="mono">{item.tracking_number ?? "-"}</td><td>{item.refundable ? "可申请" : "已过期"}</td></tr>)}</tbody></table>{!items.length && <div className="empty-state compact"><Archive size={24} /><p>当前账号没有订单</p></div>}</div></>;
}

function ApprovalsView({ token }: { token: string }) {
  const [items, setItems] = useState<Approval[]>([]);
  const [error, setError] = useState("");
  const load = useCallback(() => api<Approval[]>("/approvals", token).then(setItems).catch((reason: Error) => setError(reason.message)), [token]);
  useEffect(() => { void load(); }, [load]);
  const decide = async (id: string, decision: "approve" | "reject") => { await api(`/approvals/${id}/decision`, token, { method: "POST", body: JSON.stringify({ decision, note: decision === "approve" ? "规则核验通过" : "人工拒绝" }) }); await load(); };
  return <><PageHeader eyebrow="HUMAN IN THE LOOP" title="人工审批" /><div className="approval-list">{error && <p className="error-line">{error}</p>}{items.map((item) => <article className="approval-row" key={item.id}><div className="risk-mark"><ShieldCheck size={20} /></div><div className="approval-main"><div><strong>{item.tool_name}</strong><Status value={item.status} /></div><code>{item.tool_args_json}</code><span><Clock3 size={14} />{new Date(item.created_at).toLocaleString("zh-CN")}</span></div>{item.status === "pending" && <div className="approval-actions"><button className="approve" title="批准" onClick={() => void decide(item.id, "approve")}><Check size={17} /></button><button className="reject" title="拒绝" onClick={() => void decide(item.id, "reject")}><X size={17} /></button></div>}</article>)}{!items.length && <div className="empty-state"><ShieldCheck size={28} /><h3>没有待处理审批</h3></div>}</div></>;
}

function KnowledgeView({ token }: { token: string }) {
  const [items, setItems] = useState<KnowledgeDocument[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const load = useCallback(() => api<KnowledgeDocument[]>("/knowledge", token).then(setItems), [token]);
  useEffect(() => { void load(); }, [load]);
  const create = async () => { if (!title || content.length < 20) return; await api("/knowledge", token, { method: "POST", body: JSON.stringify({ title, source: "manual", content }) }); setTitle(""); setContent(""); await load(); };
  return <><PageHeader eyebrow="RETRIEVAL AUGMENTED GENERATION" title="知识库" action={<label className="secondary-button file-button"><Upload size={17} />上传文档<input type="file" accept=".pdf,.docx,.txt,.md" onChange={async (event) => { const file = event.target.files?.[0]; if (!file) return; const form = new FormData(); form.append("file", file); await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/knowledge/upload`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: form }); await load(); }} /></label>} /><div className="knowledge-layout"><section className="document-list"><div className="table-shell"><table><thead><tr><th>文档</th><th>来源</th><th>分块</th><th>状态</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.title}</td><td className="mono">{item.source}</td><td>{item.chunk_count}</td><td><Status value={item.status} /></td></tr>)}</tbody></table></div></section><section className="editor-panel"><span className="section-label">新增文本知识</span><input placeholder="文档标题" value={title} onChange={(event) => setTitle(event.target.value)} /><textarea placeholder="输入客服政策或处理流程…" value={content} onChange={(event) => setContent(event.target.value)} /><button className="primary-button" onClick={() => void create()}><Plus size={17} />加入索引</button></section></div></>;
}

function TicketsView({ token }: { token: string }) {
  const [items, setItems] = useState<Ticket[]>([]);
  useEffect(() => { void api<Ticket[]>("/tickets", token).then(setItems); }, [token]);
  return <><PageHeader eyebrow="CASE MANAGEMENT" title="工单中心" /><div className="table-shell"><table><thead><tr><th>主题</th><th>描述</th><th>优先级</th><th>状态</th><th>创建时间</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.subject}</td><td>{item.description}</td><td><Status value={item.priority} /></td><td><Status value={item.status} /></td><td>{new Date(item.created_at).toLocaleString("zh-CN")}</td></tr>)}</tbody></table>{!items.length && <div className="empty-state"><TicketCheck size={28} /><h3>暂无工单</h3></div>}</div></>;
}

function MetricsView({ token }: { token: string }) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  useEffect(() => { void api<Metrics>("/metrics", token).then(setMetrics); }, [token]);
  const cards = useMemo(() => metrics ? [{ label: "会话数", value: metrics.conversations }, { label: "开放工单", value: metrics.open_tickets }, { label: "待审批", value: metrics.pending_approvals }, { label: "知识文档", value: metrics.knowledge_documents }, { label: "工具成功率", value: `${metrics.tool_success_rate}%` }, { label: "平均工具延迟", value: `${metrics.average_tool_latency_ms} ms` }] : [], [metrics]);
  return <><PageHeader eyebrow="OBSERVABILITY" title="运行指标" /><div className="metric-grid">{cards.map((card) => <div className="metric" key={card.label}><span>{card.label}</span><strong>{card.value}</strong></div>)}</div><section className="activity-feed"><span className="section-label">最近工具执行</span>{metrics?.recent_tools.map((item, index) => <div className="activity-row" key={index}><Check size={15} /><strong>{String(item.tool)}</strong><span>{String(item.duration_ms)} ms</span><time>{new Date(String(item.created_at)).toLocaleString("zh-CN")}</time></div>)}</section></>;
}

function Status({ value }: { value: string }) {
  const safe = value.toLowerCase().replaceAll("_", "-");
  return <span className={`status ${safe}`}>{value}</span>;
}
