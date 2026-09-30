import { ArrowLeft, FileText, LoaderCircle, Trash2 } from "lucide-react"
import { useState } from "react"
import {
  compareDocuments,
  deleteDocument,
  getSummary
} from "../services/api"
import { useApp } from "../context/AppContext"
import ReactMarkdown from "react-markdown"

export default function Documents({ onBack }) {
  const {
    documents,
    refreshDocuments
  } = useApp()

  const [summary, setSummary] = useState(null)
  const [comparison, setComparison] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(null)
  const [comparePair, setComparePair] = useState(["", ""])
  const [compareLoading, setCompareLoading] = useState(false)
  const [error, setError] = useState("")

  const summarize = async (id) => {
    setSummaryLoading(id)
    setError("")

    try {
      const result = await getSummary(id)
      setSummary(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setSummaryLoading(null)
    }
  }

  const remove = async (id) => {
    setError("")

    try {
      await deleteDocument(id)
      await refreshDocuments()
      setSummary(null)
      setComparison(null)
    } catch (err) {
      setError(err.message)
    }
  }

  const compare = async () => {
    const [first, second] = comparePair

    if (!first || !second || first === second) return

    setCompareLoading(true)
    setError("")

    try {
      const result = await compareDocuments(Number(first), Number(second))
      setComparison(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setCompareLoading(false)
    }
  }

  return (
    <section className="documents-page">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={18} />
        Back to chat
      </button>

      <div className="documents-heading">
        <div className="eyebrow">DOCUMENT LIBRARY</div>
        <h1>Your documents</h1>
        <p>
          Every indexed PDF is available to ASTRA's retrieval system.
        </p>
      </div>

      {error && <div className="page-error">{error}</div>}

      {documents.length === 0 ? (
        <div className="documents-empty">
          <FileText size={31} />
          <h3>No documents yet</h3>
          <p>Upload PDFs from the chat workspace.</p>
        </div>
      ) : (
        <div className="document-grid">
          {documents.map((document) => (
            <div className="document-card" key={document.id}>
              <div className="document-icon">
                <FileText size={24} />
              </div>

              <div className="document-info">
                <h3>{document.name}</h3>
                <span>Indexed document</span>
              </div>

              <div className="document-actions">
                <button
                  onClick={() => summarize(document.id)}
                  disabled={summaryLoading === document.id}
                >
                  {summaryLoading === document.id ? (
                    <LoaderCircle className="spin" size={16} />
                  ) : (
                    "Summary"
                  )}
                </button>

                <button
                  className="delete-button"
                  onClick={() => remove(document.id)}
                  aria-label={`Delete ${document.name}`}
                >
                  <Trash2 size={17} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {summary && (
        <section className="result-card">
          <div className="result-label">Summary · {summary.document}</div>
          <ReactMarkdown>{summary.summary}</ReactMarkdown>
        </section>
      )}

      {comparison && (
        <section className="result-card">
          <div className="result-label">Comparison</div>
          <ReactMarkdown>{comparison.comparison}</ReactMarkdown>
        </section>
      )}
    </section>
  )
}
