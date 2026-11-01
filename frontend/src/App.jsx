import React, { useEffect, useRef, useState } from "react";
import { BookOpen, Plus, MessageSquare, Files, Upload, Send, ThumbsUp, ThumbsDown, RefreshCw, Paperclip } from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const STORAGE = "techdocs-chat-history";
const id = () => Math.random().toString(36).slice(2);

export default function App() {
  const [chats, setChats] = useState(() => {
    try { return JSON.parse(localStorage.getItem(STORAGE)) || []; } catch { return []; }
  });
  const [activeId, setActiveId] = useState(null);
  const [page, setPage] = useState("chat");
  const [question, setQuestion] = useState("");
  const [documents, setDocuments] = useState([]);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
  const fileRef = useRef(null);
  const endRef = useRef(null);

  useEffect(() => localStorage.setItem(STORAGE, JSON.stringify(chats)), [chats]);
  useEffect(() => { if (!activeId && chats.length) setActiveId(chats[0].id); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [chats, busy]);
  useEffect(() => { loadDocuments(); }, []);

  const active = chats.find(c => c.id === activeId);

  async function loadDocuments() {
    try {
      const response = await fetch(`${API}/documents`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || response.statusText);
      setDocuments(data.documents || []);
    } catch (error) { setNotice(`Could not load documents: ${error.message}`); }
  }

  function newChat() { setActiveId(null); setPage("chat"); setQuestion(""); setNotice(""); }

  async function ask(event) {
    event?.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    const chatId = activeId || id();
    if (!activeId) {
      setChats(old => [{ id: chatId, title: q.slice(0, 45), messages: [] }, ...old]);
      setActiveId(chatId);
    }
    setChats(old => old.map(c => c.id === chatId ? { ...c, messages: [...c.messages, { role: "user", text: q }] } : c));
    setQuestion("");
    setBusy(true);
    setNotice("");
    try {
      const response = await fetch(`${API}/query`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail || data));
      const message = { role: "assistant", text: data.answer || "", question: q, sources: data.sources || [], retries: data.retries, queryType: data.query_type };
      setChats(old => old.map(c => c.id === chatId ? { ...c, messages: [...c.messages, message] } : c));
    } catch (error) {
      setChats(old => old.map(c => c.id === chatId ? { ...c, messages: [...c.messages, { role: "error", text: error.message }] } : c));
    } finally { setBusy(false); }
  }

  async function upload(files) {
    if (!files?.length) return;
    setUploading(true); setNotice("");
    const form = new FormData();
    Array.from(files).forEach(file => form.append("files", file));
    try {
      const response = await fetch(`${API}/ingest`, { method: "POST", body: form });
      const data = await response.json();
      if (!response.ok) throw new Error(JSON.stringify(data.detail || data));
      setNotice(`Uploaded ${data.documents_received ?? 0} document(s). ${data.chunks_indexed ?? 0} chunks indexed.`);
      await loadDocuments();
    } catch (error) { setNotice(`Upload failed: ${error.message}`); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function feedback(message, rating) {
    try {
      const response = await fetch(`${API}/feedback`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: message.question, answer: message.text, rating, comment: "Feedback from TechDocs" })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setNotice("Feedback saved.");
    } catch (error) { setNotice(`Feedback failed: ${error.message}`); }
  }

  return <div className="app">
    <aside className="sidebar">
      <div className="brand"><BookOpen size={19}/><span>TechDocs</span></div>
      <button className="new-chat" onClick={newChat}><Plus size={16}/> New chat</button>
      <div className="side-label">MENU</div>
      <button className={page === "chat" ? "nav active" : "nav"} onClick={() => setPage("chat")}><MessageSquare size={16}/> Ask questions</button>
      <button className={page === "documents" ? "nav active" : "nav"} onClick={() => { setPage("documents"); loadDocuments(); }}><Files size={16}/> Documents <span className="count">{documents.length}</span></button>
      <div className="side-label recent-label">RECENT</div>
      <div className="history">{chats.map(chat => <button key={chat.id} className={activeId === chat.id && page === "chat" ? "history-item selected" : "history-item"} onClick={() => { setActiveId(chat.id); setPage("chat"); }}><MessageSquare size={14}/><span>{chat.title}</span></button>)}</div>
      <div className="side-bottom"><span className="status-dot"/> API connected</div>
    </aside>

    <main className="main">
      <header className="header"><span>{page === "chat" ? "Ask questions" : "Documents"}</span><span className="header-note">Technical documentation assistant</span></header>
      {notice && <div className="notice">{notice}<button onClick={() => setNotice("")}>×</button></div>}

      {page === "documents" ? <section className="page">
        <div className="page-title"><div><h1>Documents</h1><p>Files available for searching.</p></div><button className="primary" onClick={() => fileRef.current?.click()} disabled={uploading}><Upload size={15}/>{uploading ? "Uploading..." : "Upload files"}</button></div>
        <div className="upload-box" onClick={() => fileRef.current?.click()}><Upload size={20}/><strong>Choose files to upload</strong><span>PDF, TXT, Markdown or HTML</span></div>
        <div className="list-title"><h2>Uploaded files</h2><button className="text-button" onClick={loadDocuments}><RefreshCw size={14}/> Refresh</button></div>
        <div className="documents">{documents.length ? documents.map((doc, i) => <div className="document" key={i}><Files size={17}/><div><strong>{doc.source || "Document"}</strong><small>{doc.source_type || "File"} · {doc.chunks ?? 0} chunks</small></div></div>) : <p className="empty">No documents uploaded yet.</p>}</div>
      </section> : <>
        <section className="chat">
          {!active || !active.messages.length ? <div className="welcome">
            <BookOpen size={27}/>
            <h1>Technical Documentation Assistant</h1>
            <p>Ask questions about the documents you have uploaded.</p>
            <div className="examples">
              <button onClick={() => setQuestion("How does FastAPI validate incoming request data?")}>How does FastAPI validate incoming request data?</button>
              <button onClick={() => setQuestion("Explain how FastAPI dependencies work.")}>Explain how FastAPI dependencies work.</button>
              <button onClick={() => setQuestion("What testing frameworks does Python support?")}>What testing frameworks does Python support?</button>
            </div>
            <small>{documents.length} documents indexed</small>
          </div> : <div className="messages">
            {active.messages.map((m, i) => <div className={`message ${m.role}`} key={i}>
              <div className="message-role">{m.role === "user" ? "You" : m.role === "assistant" ? "Assistant" : "Error"}</div>
              <div className="message-text">{m.text}</div>
              {m.role === "assistant" && <>
                {m.sources?.length > 0 && <div className="sources"><strong>Sources</strong>{m.sources.map((s, j) => <span key={j}>{s.source || s.title || `Source ${j + 1}`}</span>)}</div>}
                <div className="feedback"><button title="Helpful" onClick={() => feedback(m, "up")}><ThumbsUp size={14}/></button><button title="Not helpful" onClick={() => feedback(m, "down")}><ThumbsDown size={14}/></button></div>
              </>}
            </div>)}
            {busy && <div className="message assistant"><div className="message-role">Assistant</div><div className="message-text muted">Searching documents...</div></div>}
            <div ref={endRef}/>
          </div>}
        </section>
        <form className="composer" onSubmit={ask}>
          <textarea value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }} placeholder="Ask a question..." rows={2}/>
          <div className="composer-actions"><button type="button" className="text-button" onClick={() => fileRef.current?.click()}><Paperclip size={14}/> Upload a document</button><button className="primary send" disabled={!question.trim() || busy}>Send <Send size={14}/></button></div>
        </form>
      </>}
      <input ref={fileRef} type="file" multiple accept=".pdf,.txt,.md,.html,.htm" hidden onChange={e => upload(e.target.files)}/>
    </main>
  </div>;
}