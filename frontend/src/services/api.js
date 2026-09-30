const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

async function request(path, options = {}) {
  let response

  try {
    response = await fetch(`${API_BASE}${path}`, options)
  } catch {
    throw new Error(
      `Cannot connect to ASTRA API at ${API_BASE}. Make sure FastAPI is running.`
    )
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok || data.error) {
    throw new Error(data.detail || data.error || "The request could not be completed.")
  }

  return data
}

export async function getDocuments() {
  return request("/documents")
}

export async function uploadDocument(file) {
  const formData = new FormData()
  formData.append("file", file)

  return request("/upload", {
    method: "POST",
    body: formData
  })
}

export async function deleteDocument(id) {
  return request(`/documents/${id}`, {
    method: "DELETE"
  })
}

export async function askQuestion(query, conversationId) {
  return request("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      query,
      limit: 5,
      conversation_id: conversationId || null
    })
  })
}

export async function getConversations() {
  return request("/conversations")
}

export async function getConversation(id) {
  return request(`/conversations/${id}`)
}

export async function getSummary(documentId) {
  return request(`/documents/${documentId}/summary`, {
    method: "POST"
  })
}

export async function compareDocuments(documentId1, documentId2) {
  return request("/documents/compare", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      document_id_1: documentId1,
      document_id_2: documentId2
    })
  })
}
