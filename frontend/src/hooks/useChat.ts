import { useState, useCallback, useRef } from 'react'
import { aiApi, type ChatMessage } from '../lib/api'

type ChatMessageWithId = ChatMessage & { id?: string }

export function useChat() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessageWithId[]>([])
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

    // 中止上一个正在进行的请求
    const wasLoading = abortRef.current !== null && loading
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    const userMsg: ChatMessageWithId = { role: 'user', content, timestamp: new Date().toISOString() }
    setMessages(prev => {
      // 如果上一个请求被中断，移除未完成的消息对（旧的用户问题 + 不完整的助手回复）
      if (wasLoading && prev.length >= 2) {
        const last = prev[prev.length - 1]
        const secondLast = prev[prev.length - 2]
        if (last.role === 'assistant' && secondLast.role === 'user') {
          return [...prev.slice(0, -2), userMsg]
        }
      }
      return [...prev, userMsg]
    })
    setLoading(true)

    const msgId = `assistant-${Date.now()}-${Math.random()}`

    try {
      const res = await aiApi.chat(sid!, content, controller.signal)
      const reader = res.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let assistantContent = ''
      const assistantMsg: ChatMessageWithId = { id: msgId, role: 'assistant', content: '', timestamp: new Date().toISOString() }
      setMessages(prev => [...prev, assistantMsg])

      while (true) {
        if (controller.signal.aborted) break
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value, { stream: true })
        const lines = text.split('\n')
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') break
            try { assistantContent += JSON.parse(data) } catch { assistantContent += data }
            setMessages(prev =>
              prev.map(m => m.id === msgId ? { ...m, content: assistantContent } : m)
            )
          }
        }
      }
    } catch (e: any) {
      if (e?.name !== 'AbortError') {
        console.error('Chat error:', e)
      }
    } finally {
      if (abortRef.current === controller) {
        setLoading(false)
      }
    }
  }, [sessionId, initSession, loading])

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
    setLoading(false)
  }, [])

  return { sessionId, messages, loading, sendMessage, initSession, stopGeneration }
}
