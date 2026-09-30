import { createContext, useContext, useEffect, useMemo, useState } from "react"
import {
  getConversations,
  getConversation,
  getDocuments
} from "../services/api"

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [documents, setDocuments] = useState([])
  const [messages, setMessages] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [conversations, setConversations] = useState([])
  const [loadingConversation, setLoadingConversation] = useState(false)

  const refreshDocuments = async () => {
    try {
      const data = await getDocuments()
      setDocuments(Array.isArray(data) ? data : [])
    } catch {
      setDocuments([])
    }
  }

  const refreshConversations = async () => {
    try {
      const data = await getConversations()
      setConversations(Array.isArray(data) ? data : [])
    } catch {
      setConversations([])
    }
  }

  useEffect(() => {
    refreshDocuments()
    refreshConversations()
  }, [])

  useEffect(() => {
    if (!conversationId) {
      setMessages([])
      return
    }

    const load = async () => {
      setLoadingConversation(true)

      try {
        const data = await getConversation(conversationId)

        setMessages(
          data.flatMap((item) => [
            {
              id: `user-${item.id}`,
              role: "user",
              content: item.question
            },
            {
              id: `assistant-${item.id}`,
              role: "assistant",
              content: item.answer
            }
          ])
        )
      } catch {
        setMessages([])
      } finally {
        setLoadingConversation(false)
      }
    }

    load()
  }, [conversationId])

  const addMessage = (message) => {
    setMessages((current) => [...current, message])
  }

  const updateMessage = (id, patch) => {
    setMessages((current) =>
      current.map((message) =>
        message.id === id ? { ...message, ...patch } : message
      )
    )
  }

  const newConversation = () => {
    setConversationId(null)
    setMessages([])
  }

  const value = useMemo(
    () => ({
      documents,
      messages,
      conversationId,
      conversations,
      loadingConversation,
      setConversationId,
      addMessage,
      updateMessage,
      newConversation,
      refreshDocuments,
      refreshConversations
    }),
    [
      documents,
      messages,
      conversationId,
      conversations,
      loadingConversation
    ]
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  return useContext(AppContext)
}
