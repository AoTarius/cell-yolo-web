/**
 * SSE流解析器
 * 解析Server-Sent Events格式的流式响应
 */
export async function streamParser(
  response: Response,
  onChunk: (content: string) => void
): Promise<string> {
  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Response body is not readable')
  }

  const decoder = new TextDecoder()
  let fullContent = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          
          if (data === '[DONE]') {
            return fullContent
          }

          try {
            const parsed = JSON.parse(data)
            const content = parsed.content
            
            if (content) {
              fullContent += content
              onChunk(fullContent)
            }
          } catch (e) {
            // 忽略解析错误，继续处理下一行
            console.warn('Failed to parse SSE data:', data)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }

  return fullContent
}