import { useState, useRef, useEffect } from 'react'
import { Send, Square, Plus } from 'lucide-react'
import { useChat } from '../hooks/useChat'
import { clsx } from 'clsx'
import ReactMarkdown from 'react-markdown'

export default function AiChat() {
  const { messages, loading, sendMessage, initSession, stopGeneration } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    sendMessage(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)]">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">AI 分析助手</h2>
        <button
          onClick={initSession}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-white border rounded-md text-gray-600 hover:bg-gray-50"
        >
          <Plus className="w-4 h-4" />
          新对话
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-3">
            <p className="text-sm">向 AI 助手提问关于大宗商品和地缘政治的问题</p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              {['黄金近期走势如何？', '分析俄乌冲突对能源价格的影响', '铜铝价格相关性分析'].map(q => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="px-3 py-1.5 text-xs bg-gray-50 border rounded-full text-gray-600 hover:bg-gray-100"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}>
            <div className={clsx(
              'max-w-[75%] rounded-lg px-4 py-2.5 text-sm',
              msg.role === 'user'
                ? 'bg-primary-600 text-white whitespace-pre-wrap'
                : 'bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700'
            )}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-headings:my-2">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : msg.content}
              {loading && i === messages.length - 1 && msg.role === 'assistant' && (
                <span className="inline-block w-1.5 h-4 bg-gray-400 ml-0.5 animate-pulse" />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="mt-3 flex gap-2">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的问题..."
          rows={1}
          className="flex-1 px-4 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-lg resize-none bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
        {loading ? (
          <button
            onClick={stopGeneration}
            className="px-4 py-2.5 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
          >
            <Square className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!input.trim()}
            className="px-4 py-2.5 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
