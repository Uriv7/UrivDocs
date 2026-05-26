import { CheckCircle, XCircle, Loader } from 'lucide-react'

export default function IngestionStatus({ status }) {
  if (!status) return null
  const icons = {
    processing: <Loader size={13} style={{ animation: 'spin 1s linear infinite', color: 'var(--accent)' }} />,
    done: <CheckCircle size={13} style={{ color: 'var(--green)' }} />,
    error: <XCircle size={13} style={{ color: 'var(--red)' }} />,
  }
  const labels = {
    processing: 'Indexing…',
    done: `Done — ${status.chunks} chunks`,
    error: `Error: ${status.error}`,
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-2)', padding: '4px 8px', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
      {icons[status.status]}
      {labels[status.status]}
    </div>
  )
}
