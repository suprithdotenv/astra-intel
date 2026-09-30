import { useState } from "react"
import Sidebar from "./components/Sidebar"
import Chat from "./components/Chat"
import UploadPanel from "./components/UploadPanel"
import Documents from "./components/Documents"
import Compare from "./components/Compare"
import { useApp } from "./context/AppContext"

export default function App() {
  const { newConversation } = useApp()
  const [page, setPage] = useState("chat")

  const startNewConversation = () => {
    newConversation()
    setPage("chat")
  }

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} onNewConversation={startNewConversation} />

      <main className="main-area">
        {page === "documents" ? (
          <Documents onBack={() => setPage("chat")} />
        ) : page === "compare" ? (
          <Compare onBack={() => setPage("chat")} />
        ) : (
          <div className="workspace">
            <UploadPanel />
            <Chat />
          </div>
        )}
      </main>
    </div>
  )
}
