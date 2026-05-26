import { useState, useRef, useEffect, useCallback } from 'react'
import { Send, User, Sparkles, BookOpen, ChevronDown } from 'lucide-react'

const SUGGESTIONS = [
  'Summarize the main topics in this document',
  'What are the key findings or conclusions?',
  'List all important dates or numbers mentioned',
  'What problems does this document describe?',
]

export default function ChatBox({ activeSource, onSourceClick }) {
  const [messages, setMessages] = useState([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const historyRef              = useRef([])
  const bottomRef               = useRef()
  const inputRef                = useRef()
  const abortRef                = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])
  useEffect(() => { inputRef.current?.focus() }, [])

  const sendMessage = useCallback(async (text) => {
    const question = (text || input).trim()
    if (!question || loading) return
    setInput('')
    setLoading(true)

    const userMsg     = { role: 'user', content: question, id: Date.now() }
    const assistantId = Date.now() + 1
    const historySnap = historyRef.current.slice(-6)

    setMessages(prev => [
      ...prev,
      userMsg,
      { role: 'assistant', content: '', sources: [], id: assistantId, streaming: true },
    ])

    try {
      const ctrl = new AbortController()
      abortRef.current = ctrl

      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          source_filter: activeSource || undefined,
          top_k: 5,
          stream: true,
          history: historySnap,
        }),
        signal: ctrl.signal,
      })

      if (!res.ok) throw new Error(`API error ${res.status}`)
      const contentType = res.headers.get('content-type') || ''

      if (contentType.includes('application/json')) {
        const data   = await res.json()
        const answer = data.answer
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: answer, sources: data.sources || [], streaming: false } : m
        ))
        historyRef.current = [...historyRef.current,
          { role: 'user', content: question },
          { role: 'assistant', content: answer },
        ]
        return
      }

      const reader  = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer    = '', fullText = '', sources = []

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') break
          try {
            const msg = JSON.parse(raw)
            if (msg.type === 'sources') {
              sources = msg.sources
              setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, sources } : m))
            } else if (msg.type === 'token') {
              fullText += msg.text
              setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, content: fullText, streaming: true } : m
              ))
              bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
            } else if (msg.type === 'error') {
              throw new Error(msg.text)
            }
          } catch (parseErr) {
            if (parseErr.message?.includes('JSON')) continue
            throw parseErr
          }
        }
      }

      setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, streaming: false } : m))
      if (fullText) {
        historyRef.current = [...historyRef.current,
          { role: 'user', content: question },
          { role: 'assistant', content: fullText },
        ]
      }

    } catch (err) {
      if (err.name === 'AbortError') return
      setMessages(prev => prev.map(m =>
        m.id === assistantId ? { ...m, content: `Error: ${err.message}. Make sure the backend is running.`, streaming: false, error: true } : m
      ))
    } finally {
      setLoading(false)
      abortRef.current = null
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [input, loading, activeSource])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const stopGeneration = () => {
    abortRef.current?.abort()
    setLoading(false)
    setMessages(prev => prev.map((m, i) =>
      i === prev.length - 1 && m.streaming ? { ...m, streaming: false } : m
    ))
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--bg)', overflow: 'hidden' }}>
      <div style={{ padding: '14px 24px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 10, background: 'var(--bg-panel)' }}>
        <Sparkles size={16} color="var(--accent)" />
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 14, color: 'var(--text-1)' }}>
          {activeSource ? `Querying: ${activeSource}` : 'Ask across all documents'}
        </span>
        {activeSource && <span style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>[filtered]</span>}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 0' }}>
        {messages.length === 0
          ? <EmptyState suggestions={SUGGESTIONS} onSuggest={sendMessage} />
          : (
            <div style={{ maxWidth: 780, margin: '0 auto', padding: '0 24px' }}>
              {messages.map(msg => <MessageBubble key={msg.id} msg={msg} onSourceClick={onSourceClick} />)}
              <div ref={bottomRef} />
            </div>
          )
        }
      </div>

      <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border)', background: 'var(--bg-panel)' }}>
        <div style={{ maxWidth: 780, margin: '0 auto', display: 'flex', gap: 10, alignItems: 'flex-end' }}>
          <div style={{ flex: 1, background: 'var(--bg-card)', border: '1.5px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: '12px 16px', transition: 'border-color 0.2s' }}
            onFocus={e => e.currentTarget.style.borderColor = 'var(--accent)'}
            onBlur={e  => e.currentTarget.style.borderColor = 'var(--border)'}
          >
            <textarea ref={inputRef} value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
              placeholder={activeSource ? `Ask about ${activeSource}…` : 'Ask anything about your documents…'}
              rows={1}
              style={{ width: '100%', background: 'none', color: 'var(--text-1)', resize: 'none', fontSize: 14, lineHeight: 1.5, maxHeight: 120, overflow: 'auto', outline: 'none', border: 'none', fontFamily: 'var(--font-body)' }}
              onInput={e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px' }}
            />
          </div>
          {loading ? (
            <button onClick={stopGeneration}
              style={{ width: 44, height: 44, borderRadius: 'var(--radius)', background: 'var(--red)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0, border: 'none', cursor: 'pointer' }}
            >■</button>
          ) : (
            <button onClick={() => sendMessage()} disabled={!input.trim()}
              style={{ width: 44, height: 44, borderRadius: 'var(--radius)', background: !input.trim() ? 'var(--bg-card)' : 'var(--accent)', color: !input.trim() ? 'var(--text-3)' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.18s', flexShrink: 0, border: 'none', cursor: input.trim() ? 'pointer' : 'default' }}
            ><Send size={16} /></button>
          )}
        </div>
        <div style={{ maxWidth: 780, margin: '6px auto 0', fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
          Enter to send · Shift+Enter for newline · Local AI — no data leaves your machine
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ msg, onSourceClick }) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexDirection: isUser ? 'row-reverse' : 'row' }}>
      {isUser ? <AvatarUser /> : <AvatarBot streaming={msg.streaming} />}
      <div style={{ maxWidth: '82%' }}>
        <div style={bubbleStyle(isUser, msg.error)}>
          {msg.content ? <MessageText text={msg.content} streaming={msg.streaming} /> : msg.streaming ? <ThinkingDots /> : null}
        </div>
        {!isUser && msg.sources?.length > 0 && !msg.streaming && (
          <SourcesList sources={msg.sources} onSourceClick={onSourceClick} />
        )}
      </div>
    </div>
  )
}

function MessageText({ text, streaming }) {
  return (
    <p style={{ fontSize: 14, lineHeight: 1.75, color: 'var(--text-1)', whiteSpace: 'pre-wrap', wordBreak: 'break-word', margin: 0 }}>
      {text}
      {streaming && <span style={{ display: 'inline-block', width: 2, height: 16, background: 'var(--accent)', marginLeft: 2, animation: 'blink 1s step-end infinite', verticalAlign: 'middle' }} />}
      <style>{`@keyframes blink{50%{opacity:0}}`}</style>
    </p>
  )
}

function SourcesList({ sources, onSourceClick }) {
  const [open, setOpen] = useState(false)
  return (
    <div style={{ marginTop: 8 }}>
      <button onClick={() => setOpen(o => !o)}
        style={{ background: 'none', color: 'var(--text-3)', fontSize: 11, fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: 4, padding: '2px 4px', borderRadius: 4, cursor: 'pointer', border: 'none', transition: 'color 0.15s' }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--accent-2)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
      >
        <BookOpen size={11} />
        {sources.length} source{sources.length > 1 ? 's' : ''}
        <ChevronDown size={11} style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
      </button>
      {open && (
        <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 4 }}>
          {sources.map((s, i) => (
            <button key={i} onClick={() => onSourceClick(s)}
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '8px 12px', textAlign: 'left', cursor: 'pointer', transition: 'all 0.15s', color: 'var(--text-2)' }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--text-1)' }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{s.source}</span>
                <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--accent-2)', flexShrink: 0 }}>p.{s.page_number} · {Math.round(s.score * 100)}%</span>
              </div>
              {s.section && <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>§ {s.section}</div>}
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4, overflow: 'hidden', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>{s.text}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function EmptyState({ suggestions, onSuggest }) {
  return (
    <div style={{ maxWidth: 600, margin: '60px auto', padding: '0 24px', textAlign: 'center' }}>
      <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'var(--accent-dim)', border: '1px solid var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px', fontSize: 24 }}>◈</div>
      <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 22, color: 'var(--text-1)', marginBottom: 8 }}>Ask your documents anything</h2>
      <p style={{ color: 'var(--text-2)', fontSize: 14, marginBottom: 32 }}>Upload files on the left, then ask questions. UrivDocs finds the answer and shows exactly where it came from.</p>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, textAlign: 'left' }}>
        {suggestions.map((s, i) => (
          <button key={i} onClick={() => onSuggest(s)}
            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '12px 14px', fontSize: 13, color: 'var(--text-2)', cursor: 'pointer', transition: 'all 0.18s', textAlign: 'left', lineHeight: 1.4 }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.color = 'var(--text-1)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-2)' }}
          >{s}</button>
        ))}
      </div>
    </div>
  )
}

function ThinkingDots() {
  return (
    <div style={{ display: 'flex', gap: 5, alignItems: 'center', height: 20 }}>
      {[0,1,2].map(i => (
        <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent)', animation: 'bounce 1.2s ease-in-out infinite', animationDelay: `${i*0.2}s` }} />
      ))}
      <style>{`@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}`}</style>
    </div>
  )
}

const AvatarBot = ({ streaming }) => (
  <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--accent-dim)', border: `1px solid ${streaming ? 'var(--accent-2)' : 'var(--accent)'}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 14, transition: 'border-color 0.3s' }}>◈</div>
)
const AvatarUser = () => (
  <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--bg-card)', border: '1px solid var(--border-hi)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
    <User size={15} color="var(--text-2)" />
  </div>
)
const bubbleStyle = (isUser, isError) => ({
  background: isError ? 'rgba(248,113,113,0.06)' : isUser ? 'var(--accent-dim)' : 'var(--bg-card)',
  border: `1px solid ${isError ? 'var(--red)' : isUser ? 'var(--accent)' : 'var(--border)'}`,
  borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
  padding: '12px 16px',
})
