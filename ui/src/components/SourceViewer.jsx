import { X, FileText, Hash, Layers, BarChart2 } from 'lucide-react'

export default function SourceViewer({ chunk, onClose }) {
  if (!chunk) return null
  return (
    <>
      <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100 }} />
      <aside style={{ position: 'fixed', right: 0, top: 0, bottom: 0, width: 420, background: 'var(--bg-panel)', borderLeft: '1px solid var(--border)', zIndex: 101, display: 'flex', flexDirection: 'column', animation: 'slideIn 0.2s ease-out' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10 }}>
          <FileText size={16} color="var(--accent)" />
          <span style={{ flex: 1, fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14, color: 'var(--text-1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {chunk.source}
          </span>
          <button onClick={onClose} style={{ background: 'none', color: 'var(--text-3)', padding: 4, borderRadius: 6, cursor: 'pointer', border: 'none', transition: 'color 0.15s' }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--text-1)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
          ><X size={16} /></button>
        </div>

        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--border)', display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <Badge icon={<Hash size={10} />} label="Page" value={chunk.page_number} />
          <Badge icon={<Layers size={10} />} label="Chunk" value={`#${chunk.chunk_index}`} />
          <Badge icon={<BarChart2 size={10} />} label="Match" value={`${Math.round(chunk.score * 100)}%`} color="var(--green)" />
          {chunk.section && <Badge icon={<FileText size={10} />} label="Section" value={chunk.section} />}
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
          <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-3)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Matched excerpt</div>
          <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '14px 16px', fontFamily: 'var(--font-mono)', fontSize: 13, lineHeight: 1.75, color: 'var(--text-1)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {chunk.text}
          </div>
          <div style={{ marginTop: 20, padding: '12px 16px', background: 'rgba(124,106,247,0.06)', border: '1px solid var(--accent-dim)', borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--text-2)', lineHeight: 1.6 }}>
            <div style={{ fontWeight: 500, color: 'var(--accent-2)', marginBottom: 4, fontSize: 11, fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>ABOUT THIS SOURCE</div>
            From <strong style={{ color: 'var(--text-1)' }}>{chunk.source}</strong>, page {chunk.page_number}.
            Similarity score: {(chunk.score * 100).toFixed(1)}%
          </div>
        </div>

        <style>{`@keyframes slideIn { from { transform: translateX(30px); opacity: 0 } to { transform: none; opacity: 1 } }`}</style>
      </aside>
    </>
  )
}

function Badge({ icon, label, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 20, padding: '3px 10px', fontSize: 11, fontFamily: 'var(--font-mono)', color: color || 'var(--text-2)' }}>
      {icon}
      <span style={{ color: 'var(--text-3)' }}>{label}:</span>
      <span style={{ color: color || 'var(--text-1)' }}>{value}</span>
    </div>
  )
}
