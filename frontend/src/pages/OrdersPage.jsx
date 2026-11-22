import { useEffect, useState } from 'react'
import { ArrowRight, PackageCheck } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { ApiError, ApiLoading, EmptyState } from '../components/ApiState'
import api from '../services/api'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

function apiMessage(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  return 'Your orders could not be loaded. Please try again.'
}

export default function OrdersPage() {
  const location = useLocation()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    api.get('/orders/').then(
      ({ data }) => {
        if (active) {
          setOrders(data)
          setLoading(false)
        }
      },
      (requestError) => {
        if (active) {
          setError(apiMessage(requestError))
          setLoading(false)
        }
      },
    )
    return () => {
      active = false
    }
  }, [attempt])

  return (
    <main className="page-section orders-page">
      <div className="breadcrumbs"><Link to="/">Home</Link><span>/</span><span>Your orders</span></div>
      <div className="section-heading">
        <div><p className="eyebrow">THE JOURNEY HOME</p><h1>Your orders.</h1></div>
        <PackageCheck size={23} strokeWidth={1.4} />
      </div>
      {location.state?.placedOrder && (
        <p className="form-feedback form-feedback--success" role="status">
          Thank you. Order {location.state.placedOrder} has been placed.
        </p>
      )}
      {loading && <ApiLoading label="Gathering your order history..." />}
      {error && <ApiError message={error} onRetry={() => setAttempt((value) => value + 1)} />}
      {!loading && !error && orders.length === 0 && (
        <EmptyState title="Your next favorite piece is out there.">
          Orders you place will appear here with their delivery status.
        </EmptyState>
      )}
      {!loading && !error && orders.length > 0 && (
        <div className="order-list">
          {orders.map((order) => (
            <article className="order-card" key={order.id}>
              <div className="order-card-heading">
                <div><span className="eyebrow">ORDER {order.order_number}</span><p>{new Date(order.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' })}</p></div>
                <div className="order-status"><span>{order.status_label}</span><small>{order.payment_status_label}</small></div>
              </div>
              <div className="order-card-items">
                {order.items.map((item) => (
                  <div key={item.id}>
                    <span>{item.product_name} <small>× {item.quantity}</small></span>
                    <strong>{money.format(Number(item.line_total))}</strong>
                  </div>
                ))}
              </div>
              <div className="order-card-footer">
                <span>{order.payment_method_label}</span>
                <strong>{money.format(Number(order.total_amount))}</strong>
              </div>
              {order.tracking_number && <p className="order-list-tracking">Tracking number: <strong>{order.tracking_number}</strong></p>}
              <Link className="order-view-details" to={`/orders/${order.id}`}>View details <ArrowRight size={14} /></Link>
              <details className="order-tracking">
                <summary>Delivery and order updates <ArrowRight size={14} /></summary>
                <ol>
                  {order.status_history.map((event, index) => (
                    <li key={`${event.status}-${event.created_at}-${index}`}>
                      <strong>{event.status.replaceAll('_', ' ')}</strong>
                      <span>{event.note || new Date(event.created_at).toLocaleDateString('en-IN')}</span>
                    </li>
                  ))}
                </ol>
                {order.tracking_number && <p>Tracking number: <strong>{order.tracking_number}</strong></p>}
                <address>
                  {order.shipping_full_name}<br />
                  {order.shipping_address_line_1}{order.shipping_address_line_2 ? `, ${order.shipping_address_line_2}` : ''}<br />
                  {order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}
                </address>
              </details>
            </article>
          ))}
        </div>
      )}
    </main>
  )
}
