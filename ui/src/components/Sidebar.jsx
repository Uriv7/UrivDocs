import { useRef, useState, useEffect } from 'react'
import { Upload, FileText, Trash2, Loader, ChevronRight, CheckCircle, AlertCircle } from 'lucide-react'

const S = {
  sidebar: {
    width: 280, minWidth: 280, height: '100vh',
    background: 'var(--bg-panel)', borderRight: '1px solid var(--border)',
    display: 'flex', flexDirection: 'column', fontFamily: 'var(--font-body)',
  },
  header: { padding: '20px 20px 16px', borderBottom: '1px solid var(--border)' },
  logo: {
    fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 20,
    letterSpacing: '-0.5px', color: 'var(--text-1)',
    display: 'flex', alignItems: 'center', gap: 8,
  },
  tagline: { fontSize: 11, color: 'var(--text-3)', marginTop: 2, fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' },
  uploadZone: (dragOver) => ({
    margin: '16px 16px 8px',
    border: `1.5px dashed ${dragOver ? 'var(--accent)' : 'var(--border-hi)'}`,
    borderRadius: 'var(--radius)', padding: '14px 12px',
    display: 'flex', alignItems: 'center', gap: 10,
    cursor: 'pointer', transition: 'all 0.18s',
    color: dragOver ? 'var(--accent-2)' : 'var(--text-2)',
    background: dragOver ? 'var(--accent-glow)' : 'transparent',
    fontSize: 13,
  }),
  sectionLabel: {
    fontSize: 10, letterSpacing: '0.1em', color: 'var(--text-3)',
    fontFamily: 'var(--font-mono)', textTransform: 'uppercase',
    padding: '12px 20px 6px',
  },
  docList: { flex: 1, overflowY: 'auto', padding: '0 8px' },
  docItem: (active) => ({
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '8px 12px', borderRadius: 'var(--radius)', cursor: 'pointer',
    marginBottom: 2, transition: 'all 0.15s',
    background: active ? 'var(--accent-dim)' : 'transparent',
    border: active ? '1px solid var(--accent)' : '1px solid transparent',
    color: active ? 'var(--accent-2)' : 'var(--text-2)',
  }),
  footer: {
    padding: '12px 16px', borderTop: '1px solid var(--border)',
    fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)',
  },
  dot: (ok) => ({
    display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
    background: ok ? 'var(--green)' : 'var(--red)', marginRight: 6,
  }),
}

export default function Sidebar({ documents, onDocsChange, activeSource, onSourceSelect, health }) {
  const fileRef = useRef()
  const [uploads, setUploads] = useState({}) // filename -> {status, chunks, progress}
  const [dragOver, setDragOver] = useState(false)
  const [deleting, setDeleting] = useState(null)

  const pollStatus = (filename) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/upload/status/${encodeURIComponent(filename)}`)
        const data = await res.json()
        setUploads(prev => ({ ...prev, [filename]: data }))
        if (data.status === 'done') {
          clearInterval(interval)
          onDocsChange()
        } else if (data.status === 'error') {
          clearInterval(interval)
        }
      } catch {
        clearInterval(interval)
      }
    }, 1500)
    // Stop polling after 5 minutes max
    setTimeout(() => clearInterval(interval), 300000)
  }

  const uploadFile = async (file) => {
    if (!file) return
    const filename = file.name
    setUploads(prev => ({ ...prev, [filename]: { status: 'uploading' } }))

    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
        setUploads(prev => ({ ...prev, [filename]: { status: 'error', error: err.detail || 'Upload failed' } }))
        return
      }
      setUploads(prev => ({ ...prev, [filename]: { status: 'processing', chunks: 0 } }))
      pollStatus(filename)
    } catch (e) {
      setUploads(prev => ({ ...prev, [filename]: { status: 'error', error: e.message } }))
    }
  }

  const handleDrop = (e) => {
    e.preventDefault(); setDragOver(false)
    Array.from(e.dataTransfer.files).forEach(uploadFile)
  }

  const deleteDoc = async (e, filename) => {
    e.stopPropagation()
    setDeleting(filename)
    try {
      await fetch(`/api/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' })
      if (activeSource === filename) onSourceSelect(null)
      onDocsChange()
    } finally {
      setDeleting(null)
    }
  }

  // Active uploads not yet in documents list
  const activeUploads = Object.entries(uploads).filter(
    ([name, s]) => s.status !== 'done' || !documents.find(d => d.filename === name)
  )

  return (
    <aside style={S.sidebar}>
      <div style={S.header}>
        <div style={S.logo}>
          <span style={{ color: 'var(--accent)', fontSize: 22 }}>◈</span>
          <span>Uriv<span style={{ color: 'var(--accent-2)' }}>Docs</span></span>
        </div>
        <div style={S.tagline}>local ai · document intelligence</div>
      </div>

      {/* Upload zone */}
      <div
        style={S.uploadZone(dragOver)}
        onClick={() => fileRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <Upload size={15} />
        <span>Drop file or click to upload</span>
        <input
          ref={fileRef}
          type="file"
          multiple
          style={{ display: 'none' }}
          accept=".pdf,.txt,.md,.docx,.csv,.xlsx,.pptx,.png,.jpg,.jpeg,.mp3,.wav,.mp4,.html"
          onChange={e => Array.from(e.target.files || []).forEach(uploadFile)}
        />
      </div>

      {/* Active uploads */}
      {activeUploads.map(([name, status]) => (
        <div key={name} style={{ margin: '0 16px 4px', padding: '8px 12px', background: 'var(--bg-card)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {status.status === 'uploading' || status.status === 'processing'
              ? <Loader size={12} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent)', flexShrink: 0 }} />
              : status.status === 'done'
              ? <CheckCircle size={12} style={{ color: 'var(--green)', flexShrink: 0 }} />
              : <AlertCircle size={12} style={{ color: 'var(--red)', flexShrink: 0 }} />
            }
            <span style={{ fontSize: 11, color: 'var(--text-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1 }} title={name}>{name}</span>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
            {status.status === 'uploading' ? 'Uploading...'
              : status.status === 'processing' ? 'Indexing document...'
              : status.status === 'done' ? `✓ ${status.chunks} chunks indexed`
              : `Error: ${status.error}`}
          </div>
        </div>
      ))}

      <div style={S.sectionLabel}>Documents ({documents.length})</div>

      <div style={S.docList}>
        {/* All docs option */}
        <div style={{ ...S.docItem(activeSource === null), marginBottom: 6 }} onClick={() => onSourceSelect(null)}>
          <FileText size={13} />
          <span style={{ flex: 1, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>All documents</span>
          {activeSource === null && <ChevronRight size={12} />}
        </div>

        {documents.map(doc => (
          <div key={doc.filename} style={S.docItem(activeSource === doc.filename)} onClick={() => onSourceSelect(doc.filename)}>
            <FileText size={13} style={{ flexShrink: 0 }} />
            <span style={{ flex: 1, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={doc.filename}>
              {doc.filename}
            </span>
            {deleting === doc.filename
              ? <Loader size={11} style={{ animation: 'spin 1s linear infinite' }} />
              : (
                <button
                  style={{ background: 'none', color: 'var(--text-3)', padding: '2px 4px', borderRadius: 4, cursor: 'pointer', lineHeight: 1, border: 'none', transition: 'color 0.15s' }}
                  onClick={e => deleteDoc(e, doc.filename)}
                  onMouseEnter={e => e.currentTarget.style.color = 'var(--red)'}
                  onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
                ><Trash2 size={11} /></button>
              )
            }
          </div>
        ))}

        {documents.length === 0 && activeUploads.length === 0 && (
          <div style={{ padding: '20px 12px', fontSize: 12, color: 'var(--text-3)', textAlign: 'center', lineHeight: 1.8 }}>
            No documents yet.<br />Upload a file to get started.
          </div>
        )}
      </div>

      <div style={S.footer}>
        <div><span style={S.dot(health?.llm_available)} />LLM {health?.llm_available ? 'ready' : 'offline'}</div>
        <div style={{ marginTop: 3 }}><span style={S.dot(health?.status === 'ok')} />{health?.vector_store || 'chroma'} · {health?.indexed_documents ?? '—'} docs</div>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </aside>
  )
}
