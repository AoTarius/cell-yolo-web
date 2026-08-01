import { streamParser } from '@/lib/streamParser'

export interface AIConfigStatus {
  configured: boolean
  message: string
}

/**
 * 检查 AI API 配置是否有效
 * @returns 配置状态
 */
export async function checkAIConfig(): Promise<AIConfigStatus> {
  const response = await fetch('/api/ai/check-config/', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return await response.json()
}

/**
 * 流式发送聊天消息（支持上下文感知）
 *
 * 将当前会话的完整对话历史一并发送给后端，
 * 后端转发给 DeepSeek API，AI 可基于完整上下文回答。
 * 对话历史仅存于前端内存，刷新页面后自动清空。
 *
 * @param messages 完整的对话消息列表 [{role, content}, ...]
 * @param role AI角色ID
 * @param onChunk 流式回调函数，接收累积的完整内容
 * @returns 完整的AI回复内容
 */
export async function sendChatMessageStream(
  messages: Array<{ role: string; content: string }>,
  role: string,
  onChunk: (content: string) => void
): Promise<string> {
  const response = await fetch('/api/ai/chat/stream/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      messages,
      role
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return streamParser(response, onChunk)
}