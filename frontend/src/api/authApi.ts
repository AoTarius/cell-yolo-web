import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 用户信息类型
 */
export interface User {
  id: number
  username: string
  email: string | null
  dark_mode: boolean
  model_base_path: string
  output_base_path: string
}

/**
 * 登录响应类型
 */
export interface LoginResponse {
  status: string
  message: string
  user: User
}

/**
 * 登录错误类型
 */
export interface LoginError {
  error: string
}

/**
 * 认证 API 服务
 */
export const authApi = {
  /**
   * 用户登录
   * POST /api/login/
   * @param username 用户名
   * @param password 密码
   * @returns 用户信息
   */
  async login(username: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/login/', {
      username,
      password,
    })
    return data
  },
}

export default api