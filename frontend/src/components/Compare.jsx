import { ArrowLeft, FileDiff, FileText, LoaderCircle } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from "react-markdown"
import { compareDocuments } from "../services/api"
import { useApp } from "../context/AppContext"

export default function Compare({ onBack }) {
  const { documents } = useApp()
  const [first, setFirst] = useState("")
  const [second, setSecond] = useState("")
  const [comparison, setComparison] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const canCompare = first && second && first !== second

  const runComparison = async () => {
    if (!canCompare || loading) return

    setLoading(true)
    setError("")
    setComparison("")

    try {
      const result = await compareDocuments(Number(first), Number(second))
      setComparison(result.comparison)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="compare-page">
      <button className="back-button" onClick={onBack}>
        <ArrowLeft size={19} />
        Back to chat
      </button>

      <div className="compare-heading">
        <div className="eyebrow">DOCUMENT COMPARISON</div>
        <h1>Compare documents</h1>
        <p>
          Select two indexed PDFs and ask ASTRA to identify similarities,
          differences, and information unique to each document.
        </p>
      </div>

      {documents.length < 2 ? (
        <div className="compare-empty">
          <FileText size={34} />
          <h2>Two documents are required</h2>
          <p>Upload at least two PDFs before starting a comparison.</p>
        </div>
      ) : (
        <>
          <div className="compare-form">
            <div className="compare-field">
              <label>Document A</label>
              <div className="select-large">
                <FileText size={20} />
                <select value={first} onChange={(event) => setFirst(event.target.value)}>
                  <option value="">Select document</option>
                  {documents.map((document) => (
                    <option key={document.id} value={document.id}>
                      {document.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="compare-divider">vs.</div>

            <div className="compare-field">
              <label>Document B</label>
              <div className="select-large">
                <FileText size={20} />
                <select value={second} onChange={(event) => setSecond(event.target.value)}>
                  <option value="">Select document</option>
                  {documents.map((document) => (
                    <option key={document.id} value={document.id}>
                      {document.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <button
            className="primary-compare"
            disabled={!canCompare || loading}
            onClick={runComparison}
          >
            {loading ? (
              <LoaderCircle className="spin" size={20} />
            ) : (
              <FileDiff size={20} />
            )}
            {loading ? "Comparing documents..." : "Compare documents"}
          </button>

          {error && <div className="page-error">{error}</div>}

          {comparison && (
            <section className="comparison-result">
              <div className="result-heading">
                <div className="eyebrow">ANALYSIS RESULT</div>
                <h2>Document comparison</h2>
              </div>
              <div className="result-markdown">
                <ReactMarkdown>{comparison}</ReactMarkdown>
              </div>
            </section>
          )}
        </>
      )}
    </section>
  )
}
