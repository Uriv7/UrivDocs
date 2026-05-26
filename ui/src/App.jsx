import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar.jsx'
import ChatBox from './components/ChatBox.jsx'
import SourceViewer from './components/SourceViewer.jsx'
import SEOHead from './components/SEOHead.jsx'

export default function App() {
  const [documents, setDocuments]         = useState([])
  const [activeSource, setActiveSource]   = useState(null)
  const [selectedChunk, setSelectedChunk] = useState(null)
  const [sourceViewerOpen, setSourceViewerOpen] = useState(false)
  const [health, setHealth]               = useState(null)
  const [chatKey, setChatKey]             = useState(0)   // increment to reset chat

  const fetchDocuments = async () => {
    try {
      const res  = await fetch('/api/documents')
      const data = await res.json()
      setDocuments(data.documents || [])
    } catch {}
  }

  const fetchHealth = async () => {
    try {
      const res  = await fetch('/health')
      const data = await res.json()
      setHealth(data)
    } catch {
      setHealth({ status: 'error', llm_available: false })
    }
  }

  useEffect(() => {
    fetchDocuments()
    fetchHealth()
    const iv = setInterval(fetchHealth, 30000)
    return () => clearInterval(iv)
  }, [])

  // When user switches document, reset the chat completely
  const handleSourceSelect = useCallback((source) => {
    setActiveSource(source)
    setChatKey(k => k + 1)          // new key = ChatBox remounts = fresh chat
    setSourceViewerOpen(false)
  }, [])

  const handleSourceClick = (chunk) => {
    setSelectedChunk(chunk)
    setSourceViewerOpen(true)
  }

  const pageTitle = activeSource
    ? `${activeSource} — UrivDocs`
    : 'UrivDocs — Local AI Document Intelligence'

  const pageDesc = activeSource
    ? `Asking AI questions about ${activeSource}.`
    : 'Upload any file and ask questions. Get cited answers — 100% local AI.'

  return (
    <>
      <SEOHead title={pageTitle} description={pageDesc} />
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        <Sidebar
          documents={documents}
          onDocsChange={fetchDocuments}
          activeSource={activeSource}
          onSourceSelect={handleSourceSelect}
          health={health}
        />
        <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* key prop forces full remount = fresh empty chat on every switch */}
          <ChatBox
            key={`chat-${activeSource ?? 'all'}-${chatKey}`}
            activeSource={activeSource}
            onSourceClick={handleSourceClick}
          />
        </main>
        {sourceViewerOpen && (
          <SourceViewer
            chunk={selectedChunk}
            onClose={() => setSourceViewerOpen(false)}
          />
        )}
      </div>
    </>
  )
}
