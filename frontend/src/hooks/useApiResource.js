import { useEffect, useState } from 'react'
import api from '../services/api'

export default function useApiResource(path) {
  const [attempt, setAttempt] = useState(0)
  const [result, setResult] = useState({ path: null, data: null, error: null })

  useEffect(() => {
    let active = true
    api.get(path).then(
      ({ data }) => {
        if (active) setResult({ path, data, error: null })
      },
      (error) => {
        if (active) {
          setResult({
            path,
            data: null,
            error: error.response?.data?.detail || 'We could not load this content.',
          })
        }
      },
    )
    return () => {
      active = false
    }
  }, [path, attempt])

  const isCurrent = result.path === path
  return {
    data: isCurrent ? result.data : null,
    error: isCurrent ? result.error : null,
    loading: !isCurrent,
    retry: () => setAttempt((current) => current + 1),
  }
}
