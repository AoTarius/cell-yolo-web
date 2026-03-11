import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

/**
 * 用户接口
 */
export interface User {
  id: number
  username: string
  email?: string
  dark_mode: boolean
  model_base_path: string
  output_base_path: string
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
   * @returns 登录结果（包含用户信息）
   */
  async login(username: string, password: string): Promise<{
    status: string
    message: string
    user: User
  }> {
    const { data } = await api.post<{
      status: string
      message: string
      user: User
    }>('/login/', {
      username,
      password,
    })
    return data
  },

  /**
   * 更新用户颜色模式
   * POST /api/update-user/
   * @param username 用户名
   * @param darkMode 是否为深色模式
   * @returns 更新结果
   */
  async updateUserDarkMode(username: string, darkMode: boolean): Promise<{ status: string; message: string }> {
    const { data } = await api.post<{ status: string; message: string }>('/update-user/', {
      username,
      dark_mode: darkMode,
    })
    return data
  },
}

export default api