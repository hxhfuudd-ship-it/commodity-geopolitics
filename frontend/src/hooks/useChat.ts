import { useState, useCallback, useRef } from 'react'
import { aiApi, type ChatMessage } from '../lib/api'

export function useChat() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const initSession = useCallback(async () => {
    const res = await aiApi.newSession()
    setSessionId(res.session_id)
    setMessages([])
    return res.session_id
  }, [])

  const sendMessage = useCallback(async (content: string) => {
    let sid = sessionId
    if (!sid) {
      sid = await initSession()
    }

    const userMsg: ChatMessage = { role: 'user', content, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      abortRef.current = new AbortController()
      const res = await aiApi.chat(sid!, content)
      const reader = res.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let assistantContent = ''
      const assistantMsg: ChatMessage = { role: 'assistant', content: '', timestamp: new Date().toISOString() }
      setMessages(prev => [...prev, assistantMsg])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value, { stream: true })
        const lines = text.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') break
            try { assistantContent += JSON.parse(data) } catch { assistantContent += data }
            setMessages(prev => {
              const updated = [...prev]
              updated[updated.length - 1] = { ...assistantMsg, content: assistantContent }
              return updated
            })
          }
        }
      }
    } catch (e) {
      console.error('Chat error:', e)
    } finally {
      setLoading(false)
    }
  }, [sessionId, initSession])

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
    setLoading(false)
  }, [])

  return { sessionId, messages, loading, sendMessage, initSession, stopGeneration }
}
