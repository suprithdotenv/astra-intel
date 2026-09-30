import { FileUp, LoaderCircle, Send } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import ReactMarkdown from "react-markdown"
import {
  askQuestion,
  getSummary,
  uploadDocument
} from "../services/api"
import { useApp } from "../context/AppContext"

export default function Chat() {
  const {
    messages,
    conversationId,
    setConversationId,
    addMessage,
    updateMessage,
    refreshDocuments,
    refreshConversations,
    loadingConversation
  } = useApp()

  const [question, setQuestion] = useState("")
  const [asking, setAsking] = useState(false)
  const [attaching, setAttaching] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)
  const fileRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, asking])

  const submit = async () => {
    const query = question.trim()

    if (!query || asking || attaching) return

    setQuestion("")
    setAsking(true)

    const userId = `user-${Date.now()}`
    const assistantId = `assistant-${Date.now()}`

    addMessage({
      id: userId,
      role: "user",
      content: query
    })

    addMessage({
      id: assistantId,
      role: "assistant",
      loading: true,
      content: ""
    })

    try {
      const result = await askQuestion(query, conversationId)

      if (!conversationId && result.conversation_id) {
        setConversationId(result.conversation_id)
      }

      updateMessage(assistantId, {
        loading: false,
        content: result.answer,
        sources: result.sources || [],
        verification: result.verification
      })

      await refreshConversations()
    } catch (error) {
      updateMessage(assistantId, {
        loading: false,
        error: error.message,
        content: ""
      })
    } finally {
      setAsking(false)
    }
  }

  const attachAndSummarize = async (file) => {
    if (!file || attaching) return

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      return
    }

    setAttaching(true)

    const userId = `file-${Date.now()}`
    const assistantId = `summary-${Date.now()}`

    addMessage({
      id: userId,
      role: "user",
      content: `Summarize ${file.name}`
    })

    addMessage({
      id: assistantId,
      role: "assistant",
      loading: true,
      content: ""
    })

    try {
      const uploaded = await uploadDocument(file)
      await refreshDocuments()

      const summary = await getSummary(uploaded.document_id)

      updateMessage(assistantId, {
        loading: false,
        content: summary.summary,
        sources: [
          {
            document: summary.document,
            page: "document"
          }
        ]
      })

      await refreshConversations()
    } catch (error) {
      updateMessage(assistantId, {
        loading: false,
        error: error.message,
        content: ""
      })
    } finally {
      setAttaching(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <section className="chat-panel">
      <div className="chat-scroll">
        {loadingConversation ? (
          <div className="center-state">
            <LoaderCircle className="spin" size={21} />
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-chat">
            <img src="/astra-logo.svg" alt="" />
            <h2>What can ASTRA find?</h2>
            <p>
              Ask a question about one document, name a document in your
              question, or ask ASTRA to connect evidence across your library.
            </p>
          </div>
        ) : (
          <div className="messages">
            {messages.map((message) => (
              <article className={`message ${message.role}`} key={message.id}>
                {message.role === "user" ? (
                  <div className="user-message">{message.content}</div>
                ) : (
                  <div className="assistant-message">
                    {message.loading ? (
                      <div className="thinking">
                        <span />
                        <span />
                        <span />
                      </div>
                    ) : message.error ? (
                      <div className="assistant-error">{message.error}</div>
                    ) : (
                      <>
                        <div className="markdown">
                          <ReactMarkdown>{message.content}</ReactMarkdown>
                        </div>

                        {message.sources?.length > 0 && (
                          <SourceList sources={message.sources} />
                        )}

                        {message.verification && (
                          <Verification verification={message.verification} />
                        )}
                      </>
                    )}
                  </div>
                )}
              </article>
            ))}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="composer-wrap">
        <div className="composer">
          <button
            className="attach-button"
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={asking || attaching}
            aria-label="Upload PDF for summary"
          >
            {attaching ? (
              <LoaderCircle className="spin" size={20} />
            ) : (
              <FileUp size={20} />
            )}
          </button>

          <textarea
            ref={inputRef}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask ASTRA about your documents..."
            rows={1}
            disabled={asking || attaching}
          />

          <button
            className="send-button"
            type="button"
            onClick={submit}
            disabled={!question.trim() || asking || attaching}
            aria-label="Send"
          >
            {asking ? (
              <LoaderCircle className="spin" size={19} />
            ) : (
              <Send size={18} />
            )}
          </button>

          <input
            ref={fileRef}
            hidden
            type="file"
            accept=".pdf,application/pdf"
            onChange={(event) => {
              attachAndSummarize(event.target.files?.[0])
              event.target.value = ""
            }}
          />
        </div>

        <div className="composer-note">
          Attach a PDF with <strong>+</strong> to upload it and generate its summary.
        </div>
      </div>
    </section>
  )
}

function SourceList({ sources }) {
  const unique = sources.filter(
    (source, index, array) =>
      index ===
      array.findIndex(
        (item) =>
          item.page === source.page &&
          item.document === source.document
      )
  )

  return (
    <div className="sources">
      <div className="sources-title">Sources</div>

      <div className="source-list">
        {unique.map((source, index) => (
          <div className="source" key={`${source.document}-${source.page}-${index}`}>
            <span>{source.document || "Document"}</span>
            {source.page !== "document" && <span>Page {source.page}</span>}
          </div>
        ))}
      </div>
    </div>
  )
}

function Verification({ verification }) {
  if (!verification || verification.grounded === undefined) return null

  const confidence =
    typeof verification.confidence === "number"
      ? Math.round(verification.confidence * 100)
      : null

  return (
    <div className="verification">
      {verification.grounded
        ? "Grounded in document evidence"
        : "Evidence needs review"}
      {confidence !== null && ` · ${confidence}% confidence`}
    </div>
  )
}
