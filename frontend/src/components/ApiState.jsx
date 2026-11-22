import { RefreshCw } from 'lucide-react'

export function ApiError({ message, onRetry }) {
  return (
    <div className="api-message api-message--error" role="alert">
      <p>{message}</p>
      <button className="button button--outline" type="button" onClick={onRetry}>
        <RefreshCw size={15} /> Try again
      </button>
    </div>
  )
}

export function ApiLoading({ label = 'Finding the right pieces...' }) {
  return (
    <div className="api-loading" role="status">
      <span className="loading-spinner" />
      {label}
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  )
}
