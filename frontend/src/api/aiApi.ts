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
 * 流式发送聊天消息
 * @param message 用户消息内容
 * @param role AI角色ID
 * @param onChunk 流式回调函数，接收部分内容
 * @returns 完整的AI回复内容
 */
export async function sendChatMessageStream(
  message: string,
  role: string,
  onChunk: (content: string) => void
): Promise<string> {
  const response = await fetch('/api/ai/chat/stream/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message,
      role
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  return streamParser(response, onChunk)
}