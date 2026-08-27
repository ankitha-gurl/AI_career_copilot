import { useState, useRef, useEffect } from 'react'
import api from '../api/client'

export default function Copilot() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi! I'm your AI Career Copilot. Ask me about your resume, job matches, skill gaps, or interview prep." },
  ])
  const [input, setInput] = useState('')
  const [conversationId, setConversationId] = useState(null)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend(e) {
    e.preventDefault()
    if (!input.trim() || sending) return
    const userMessage = input
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setSending(true)
    setError('')
    try {
      const res = await api.post('/copilot/chat', { message: userMessage, conversation_id: conversationId })
      setConversationId(res.data.conversation_id)
      setMessages((prev) => [...prev, { role: 'assistant', content: res.data.reply }])
    } catch (err) {
      setError(err.response?.data?.detail || 'The Copilot is unavailable right now.')
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="page copilot-page">
      <h1>AI Career Copilot</h1>
      {error && <div className="alert-error">{error}</div>}

      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble chat-${m.role}`}>{m.content}</div>
        ))}
        {sending && <div className="chat-bubble chat-assistant">Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <form className="chat-input-row" onSubmit={handleSend}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your career readiness..."
        />
        <button type="submit" disabled={sending}>Send</button>
      </form>
    </div>
  )
}
