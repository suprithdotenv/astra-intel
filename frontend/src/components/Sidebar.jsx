import { Plus } from "lucide-react"
import { useApp } from "../context/AppContext"

export default function Sidebar({ page, setPage, onNewConversation }) {
  const { documents, conversations, conversationId, setConversationId } = useApp()

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <img src="/astra-logo.svg" alt="ASTRA" />
      </div>

      <button className="new-chat-button" onClick={onNewConversation}>
        <Plus size={20} />
        <span>New conversation</span>
      </button>

      <nav className="sidebar-nav">
        <button
          className={`nav-item ${page === "chat" ? "active" : ""}`}
          onClick={() => setPage("chat")}
        >
          Chat
        </button>

        <button
          className={`nav-item ${page === "documents" ? "active" : ""}`}
          onClick={() => setPage("documents")}
        >
          <span>Documents</span>
          <span className="count">{documents.length}</span>
        </button>

        <button
          className={`nav-item ${page === "compare" ? "active" : ""}`}
          onClick={() => setPage("compare")}
        >
          Compare
        </button>
      </nav>

      <div className="recent">
        <div className="sidebar-label">Recent conversations</div>

        {conversations.length === 0 ? (
          <div className="sidebar-empty">No conversations yet</div>
        ) : (
          conversations.slice(0, 12).map((conversation) => (
            <button
              className={`conversation-item ${
                conversation.id === conversationId ? "selected" : ""
              }`}
              key={conversation.id}
              onClick={() => {
                setPage("chat")
                setConversationId(conversation.id)
              }}
            >
              {conversation.title}
            </button>
          ))
        )}
      </div>

      <div className="sidebar-footer">
        <strong>ASTRA INTEL</strong>
        <span>Document intelligence</span>
      </div>
    </aside>
  )
}
