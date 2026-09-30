import { Check, FileText, LoaderCircle, UploadCloud } from "lucide-react"
import { useRef, useState } from "react"
import { uploadDocument } from "../services/api"
import { useApp } from "../context/AppContext"

export default function UploadPanel() {
  const { refreshDocuments, newConversation } = useApp()
  const inputRef = useRef(null)
  const [items, setItems] = useState([])

  const uploadFiles = async (files) => {
    const pdfs = Array.from(files).filter(
      (file) =>
        file.type === "application/pdf" ||
        file.name.toLowerCase().endsWith(".pdf")
    )

    if (!pdfs.length) return

    setItems(
      pdfs.map((file) => ({
        name: file.name,
        status: "uploading"
      }))
    )

    for (const file of pdfs) {
      try {
        await uploadDocument(file)

        setItems((current) =>
          current.map((item) =>
            item.name === file.name
              ? { ...item, status: "done" }
              : item
          )
        )

        await refreshDocuments()
      } catch (error) {
        setItems((current) =>
          current.map((item) =>
            item.name === file.name
              ? { ...item, status: "error", error: error.message }
              : item
          )
        )
      }
    }
  }

  const chooseFiles = (event) => {
    uploadFiles(event.target.files || [])
    event.target.value = ""
  }

  const dropFiles = (event) => {
    event.preventDefault()
    uploadFiles(event.dataTransfer.files || [])
  }

  const allDone =
    items.length > 0 && items.every((item) => item.status === "done")

  return (
    <section className="upload-panel">
      <div className="upload-copy">
        <div className="eyebrow">ASTRA INTEL</div>
        <h1>Ask your documents.</h1>
        <p>
          Upload one or more PDFs. ASTRA can answer from a specific document
          or synthesize evidence across the entire library.
        </p>
      </div>

      <div
        className="drop-zone"
        onDragOver={(event) => event.preventDefault()}
        onDrop={dropFiles}
        onClick={() => inputRef.current?.click()}
      >
        <div className="upload-icon-large">
          <UploadCloud size={36} strokeWidth={1.7} />
        </div>

        <div className="drop-copy">
          <strong>Upload PDF documents</strong>
          <span>Drop files here or click to browse</span>
        </div>

        <button
          className="browse-button"
          type="button"
          onClick={(event) => {
            event.stopPropagation()
            inputRef.current?.click()
          }}
        >
          Choose files
        </button>

        <input
          ref={inputRef}
          hidden
          type="file"
          accept=".pdf,application/pdf"
          multiple
          onChange={chooseFiles}
        />
      </div>

      {items.length > 0 && (
        <div className="upload-progress">
          <div className="progress-title">
            {allDone ? "Upload complete" : "Uploading documents"}
            {allDone ? (
              <Check size={18} />
            ) : (
              <LoaderCircle className="spin" size={18} />
            )}
          </div>

          {items.map((item) => (
            <div className="progress-item" key={item.name}>
              <div className="progress-file">
                <FileText size={16} />
                <span>{item.name}</span>
              </div>

              {item.status === "uploading" && (
                <span className="waiting-dots">...</span>
              )}

              {item.status === "done" && (
                <span className="ready">
                  <Check size={14} />
                  Ready
                </span>
              )}

              {item.status === "error" && (
                <span className="upload-failed">{item.error}</span>
              )}
            </div>
          ))}

          {allDone && (
            <button
              className="after-upload"
              onClick={newConversation}
            >
              <span>New conversation</span>
            </button>
          )}
        </div>
      )}
    </section>
  )
}
