import { Link, Navigate, useLocation } from 'react-router-dom'
import useAuth from '../hooks/useAuth'

export default function ProtectedAdminRoute({ children }) {
  const { isAuthenticated, user } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (!user?.is_staff) {
    return (
      <main className="not-found-page">
        <p className="eyebrow">STAFF ACCESS ONLY</p>
        <h1>This area is for the FurniNest team.</h1>
        <Link className="button button--dark" to="/account">Return to your account</Link>
      </main>
    )
  }
  return children
}
