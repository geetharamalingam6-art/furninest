import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const accessToken = window.localStorage.getItem('furninest-access')
  const cartToken = window.localStorage.getItem('furninest-cart-token')
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`
  if (cartToken) config.headers['X-Cart-Token'] = cartToken
  return config
})

api.interceptors.response.use(
  (response) => {
    if (response.data?.guest_token) {
      window.localStorage.setItem('furninest-cart-token', response.data.guest_token)
    } else if (
      response.data?.guest_token === null
      && String(response.config.url).startsWith('/cart')
      && window.localStorage.getItem('furninest-access')
    ) {
      window.localStorage.removeItem('furninest-cart-token')
    }
    return response
  },
  async (error) => {
    const request = error.config
    const refreshToken = window.localStorage.getItem('furninest-refresh')
    const requestUrl = String(request?.url || '')
    const canRefresh = error.response?.status === 401
      && !request?._retry
      && refreshToken
      && !requestUrl.includes('/auth/login/')
      && !requestUrl.includes('/auth/register/')
      && !requestUrl.includes('/auth/token/refresh/')
      && !requestUrl.includes('/auth/logout/')

    if (!canRefresh) return Promise.reject(error)

    request._retry = true
    try {
      const { data } = await axios.post(
        `${api.defaults.baseURL}/auth/token/refresh/`,
        { refresh: refreshToken },
        { timeout: api.defaults.timeout },
      )
      window.localStorage.setItem('furninest-access', data.access)
      if (data.refresh) window.localStorage.setItem('furninest-refresh', data.refresh)
      request.headers.Authorization = `Bearer ${data.access}`
      return api(request)
    } catch (refreshError) {
      window.localStorage.removeItem('furninest-access')
      window.localStorage.removeItem('furninest-refresh')
      window.dispatchEvent(new Event('furninest:session-expired'))
      return Promise.reject(refreshError)
    }
  },
)

export default api
