import ReactMarkdown from 'react-markdown'
import { useState, useRef, useEffect } from 'react'
import { sendCustomerMessage, sendInternalMessage, confirmEscalation } from '../api.js'

export default function Chat({ session, onLogout }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: session.role === 'internal'
        ? 'Internal support console ready. You have access to all accounts, orders, and tickets.'
        : `Hello! I'm your ParcelPilot support agent. How can I help you today?`,
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [toolTrace, setToolTrace] = useState([])
  const [pendingEscalation, setPendingEscalation] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setLoading(true)
    setToolTrace([])

    const history = newMessages.slice(0, -1).map((m) => ({
      role: m.role,
      content: m.content,
    }))

    try {
      const fn = session.role === 'internal' ? sendInternalMessage : sendCustomerMessage
      const data = await fn(userMessage.content, history, session.access_token)

      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }])
      setToolTrace(data.tool_trace || [])

      if (data.response.includes('ESCALATION_READY_FOR_CONFIRMATION')) {
        const lines = data.response.split('\n')
        const ref_id = lines.find(l => l.startsWith('Reference:'))?.split(': ')[1]?.split(' ')[0]
        const ref_type = lines.find(l => l.startsWith('Reference:'))?.match(/\((\w+)\)/)?.[1]
        const reason = lines.find(l => l.startsWith('Reason:'))?.split(': ')[1]
        if (ref_id && ref_type && reason) {
          setPendingEscalation({ ref_id, ref_type, reason })
        }
      }
    } catch {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: 'Something went wrong. Please try again.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmEscalation = async () => {
    if (!pendingEscalation) return
    try {
      const data = await confirmEscalation(
        pendingEscalation.ref_id,
        pendingEscalation.ref_type,
        pendingEscalation.reason,
        session.access_token
      )
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Escalation created: ${data.escalation.escalation_id} for ${data.escalation.ref_id}. Status: ${data.escalation.status}.`,
      }])
      setPendingEscalation(null)
    } catch {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: 'Failed to create escalation.',
      }])
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div style={styles.layout}>
      <div style={styles.sidebar}>
        <div style={styles.sidebarHeader}>
          <span style={styles.sidebarIcon}>📦</span>
          <div>
            <p style={styles.sidebarTitle}>ParcelPilot</p>
            <p style={styles.sidebarSub}>
              {session.role === 'internal' ? 'Internal Console' : 'Customer Support'}
            </p>
          </div>
        </div>

        <div style={styles.sessionInfo}>
          <p style={styles.sessionLabel}>Logged in as</p>
          <p style={styles.sessionName}>{session.account_name || 'Support Agent'}</p>
          <span style={{
            ...styles.roleBadge,
            background: session.role === 'internal' ? '#7c3aed22' : '#0d947022',
            color: session.role === 'internal' ? '#a78bfa' : '#34d399',
            border: `1px solid ${session.role === 'internal' ? '#7c3aed44' : '#0d947044'}`,
          }}>
            {session.role}
          </span>
        </div>

        <div style={styles.traceSection}>
          <p style={styles.traceLabel}>Tool Trace</p>
          {toolTrace.length === 0 ? (
            <p style={styles.traceEmpty}>No tools called yet</p>
          ) : (
            toolTrace.map((t, i) => (
              <div key={i} style={styles.traceItem}>
                <span style={styles.traceToolName}>{t.tool}</span>
                <p style={styles.traceInput}>
                  {Object.values(t.input || {}).join(' ')}
                </p>
              </div>
            ))
          )}
        </div>

        <button style={styles.logoutBtn} onClick={onLogout}>Sign Out</button>
      </div>

      <div style={styles.chatArea}>
        <div style={styles.messages}>
          {messages.map((m, i) => (
            <div key={i} style={{
              ...styles.messageRow,
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
            }}>
              <div style={{
                ...styles.bubble,
                background: m.role === 'user' ? '#4f46e5' : '#1e2130',
                borderRadius: m.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
              }}>
                {m.role === 'assistant' ? <ReactMarkdown>{m.content}</ReactMarkdown> : m.content}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ ...styles.messageRow, justifyContent: 'flex-start' }}>
              <div style={{ ...styles.bubble, background: '#1e2130', color: '#6b7280' }}>
                Thinking...
              </div>
            </div>
          )}

          {pendingEscalation && (
            <div style={styles.confirmBox}>
              <p style={styles.confirmTitle}>Confirm Escalation</p>
              <p style={styles.confirmText}>
                {pendingEscalation.ref_id} — {pendingEscalation.reason}
              </p>
              <div style={styles.confirmButtons}>
                <button style={styles.confirmYes} onClick={handleConfirmEscalation}>
                  Confirm
                </button>
                <button style={styles.confirmNo} onClick={() => setPendingEscalation(null)}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div style={styles.inputArea}>
          <textarea
            style={styles.textarea}
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
          />
          <button
            style={{ ...styles.sendBtn, opacity: loading || !input.trim() ? 0.5 : 1 }}
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

const styles = {
  layout: {
    display: 'flex',
    height: '100vh',
    background: '#0f1117',
  },
  sidebar: {
    width: '280px',
    background: '#1a1d27',
    borderRight: '1px solid #2a2d3e',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px',
    gap: '20px',
    overflowY: 'auto',
  },
  sidebarHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  sidebarIcon: {
    fontSize: '28px',
  },
  sidebarTitle: {
    fontWeight: '700',
    fontSize: '16px',
    color: '#fff',
  },
  sidebarSub: {
    fontSize: '12px',
    color: '#6b7280',
  },
  sessionInfo: {
    background: '#242736',
    borderRadius: '10px',
    padding: '14px',
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  sessionLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  sessionName: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#e2e8f0',
  },
  roleBadge: {
    fontSize: '11px',
    padding: '3px 10px',
    borderRadius: '20px',
    fontWeight: '600',
    width: 'fit-content',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  traceSection: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  traceLabel: {
    fontSize: '11px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: '4px',
  },
  traceEmpty: {
    fontSize: '12px',
    color: '#3a3f55',
    fontStyle: 'italic',
  },
  traceItem: {
    background: '#242736',
    border: '1px solid #2a2d3e',
    borderRadius: '8px',
    padding: '10px',
  },
  traceToolName: {
    fontSize: '11px',
    fontWeight: '700',
    color: '#818cf8',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  traceInput: {
    fontSize: '11px',
    color: '#6b7280',
    marginTop: '4px',
    wordBreak: 'break-word',
  },
  logoutBtn: {
    background: 'transparent',
    border: '1px solid #2a2d3e',
    borderRadius: '8px',
    color: '#6b7280',
    padding: '10px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  chatArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '24px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  messageRow: {
    display: 'flex',
  },
  bubble: {
    maxWidth: '70%',
    padding: '12px 16px',
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#e2e8f0',
    whiteSpace: 'pre-wrap',
  },
  confirmBox: {
    background: '#1e2130',
    border: '1px solid #4f46e5',
    borderRadius: '12px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    maxWidth: '420px',
  },
  confirmTitle: {
    fontWeight: '700',
    fontSize: '14px',
    color: '#a5b4fc',
  },
  confirmText: {
    fontSize: '13px',
    color: '#9ca3af',
  },
  confirmButtons: {
    display: 'flex',
    gap: '8px',
  },
  confirmYes: {
    background: '#4f46e5',
    border: 'none',
    borderRadius: '6px',
    color: '#fff',
    padding: '8px 16px',
    cursor: 'pointer',
    fontSize: '13px',
    fontWeight: '600',
  },
  confirmNo: {
    background: 'transparent',
    border: '1px solid #2a2d3e',
    borderRadius: '6px',
    color: '#6b7280',
    padding: '8px 16px',
    cursor: 'pointer',
    fontSize: '13px',
  },
  inputArea: {
    padding: '16px 24px',
    borderTop: '1px solid #2a2d3e',
    display: 'flex',
    gap: '12px',
    alignItems: 'flex-end',
  },
  textarea: {
    flex: 1,
    background: '#1e2130',
    border: '1px solid #2a2d3e',
    borderRadius: '10px',
    color: '#e2e8f0',
    padding: '12px 14px',
    fontSize: '14px',
    resize: 'none',
    outline: 'none',
    fontFamily: 'inherit',
    lineHeight: '1.5',
  },
  sendBtn: {
    background: '#4f46e5',
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    padding: '12px 20px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
  },
}