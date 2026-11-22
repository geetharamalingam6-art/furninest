import { useEffect, useState } from 'react'
import { ArrowLeft, PackageCheck } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, ApiLoading } from '../components/ApiState'
import api from '../services/api'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

const stages = [
  ['confirmed', 'Order placed'],
  ['processing', 'Processing'],
  ['shipped', 'Shipped'],
  ['out_for_delivery', 'Out for delivery'],
  ['delivered', 'Delivered'],
]

export default function OrderDetailPage() {
  const { orderId } = useParams()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setOrder(null)
    setError('')
    api.get(`/orders/${orderId}/`).then(({ data }) => {
      if (active) setOrder(data)
    }).catch((requestError) => {
      if (active) {
        const detail = requestError.response?.data?.detail
        setError(typeof detail === 'string' ? detail : 'Order details could not be loaded.')
      }
    })
    return () => { active = false }
  }, [orderId, attempt])

  if (error) return <main className="page-section order-detail-page"><ApiError message={error} onRetry={() => setAttempt((value) => value + 1)} /></main>
  if (!order) return <main className="page-section order-detail-page"><ApiLoading label="Loading order details..." /></main>

  const specialStatus = ['cancelled', 'returned'].includes(order.status)
  const currentStage = order.status === 'pending' ? 0 : stages.findIndex(([status]) => status === order.status)
  const paymentFailed = order.payment_status === 'failed'

  return (
    <main className="page-section order-detail-page">
      <div className="breadcrumbs"><Link to="/">Home</Link><span>/</span><Link to="/orders">Your orders</Link><span>/</span><span>{order.order_number}</span></div>
      <Link className="checkout-back" to="/orders"><ArrowLeft size={15} /> Back to your orders</Link>
      <div className="section-heading order-detail-heading">
        <div><p className="eyebrow">ORDER {order.order_number}</p><h1>Order details.</h1><p>Placed {new Date(order.created_at).toLocaleDateString('en-IN', { dateStyle: 'long' })}</p></div>
        <div className="order-status"><span>{order.status_label}</span><small>{order.payment_status_label}</small></div>
      </div>

      {paymentFailed && <p className="form-feedback form-feedback--error" role="status">Payment was not completed. This order has not been marked as paid.</p>}

      <section className="order-detail-card">
        <h2><PackageCheck size={18} /> Delivery tracking</h2>
        {specialStatus ? (
          <p className="order-special-status">Order {order.status_label.toLowerCase()}{paymentFailed ? ' and payment failed' : ''}.</p>
        ) : (
          <ol className="order-stage-timeline">
            {stages.map(([status, label], index) => {
              const statusEvent = order.status_history.find((event) => event.status === status)
                || (status === 'confirmed' && order.status === 'pending'
                  ? order.status_history.find((event) => event.status === 'pending')
                  : null)
              const active = currentStage >= index
              return (
                <li className={active ? 'order-stage order-stage--complete' : 'order-stage'} key={status}>
                  <span className="order-stage-marker" aria-hidden="true" />
                  <strong>{label}</strong>
                  <small>{statusEvent ? new Date(statusEvent.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' }) : active ? 'In progress' : 'Awaiting update'}</small>
                </li>
              )
            })}
          </ol>
        )}
        {order.tracking_number && <p>Tracking number: <strong>{order.tracking_number}</strong></p>}
        <h3>Order updates</h3>
        <ol className="order-update-list">
          {order.status_history.map((event, index) => (
            <li key={`${event.status}-${event.created_at}-${index}`}>
              <strong>{event.status.replaceAll('_', ' ')}</strong>
              <span>{event.note || new Date(event.created_at).toLocaleDateString('en-IN', { dateStyle: 'medium' })}</span>
              <time>{new Date(event.created_at).toLocaleString('en-IN')}</time>
            </li>
          ))}
        </ol>
      </section>

      <div className="order-detail-grid">
        <section className="order-detail-card">
          <h2>Items in this order</h2>
          <div className="order-detail-items">
            {order.items.map((item) => (
              <div className="order-detail-item" key={item.id}>
                <span><strong>{item.product_name}</strong><small>Qty {item.quantity} · {money.format(Number(item.unit_price))} each</small></span>
                <strong>{money.format(Number(item.line_total))}</strong>
              </div>
            ))}
          </div>
          <div className="order-detail-totals">
            <div><span>Subtotal</span><span>{money.format(Number(order.subtotal))}</span></div>
            {Number(order.discount_amount) > 0 && <div><span>Discount</span><span>-{money.format(Number(order.discount_amount))}</span></div>}
            <div><span>Shipping</span><span>{money.format(Number(order.shipping_amount))}</span></div>
            <div><span>Tax</span><span>{money.format(Number(order.tax_amount))}</span></div>
            <div className="order-detail-grand-total"><strong>Total</strong><strong>{money.format(Number(order.total_amount))}</strong></div>
          </div>
        </section>

        <div className="order-detail-aside">
          <section className="order-detail-card">
            <h2>Payment</h2>
            <p>{order.payment_method_label}</p>
            <p>Status: <strong>{order.payment_status_label}</strong></p>
            <p>Order status: <strong>{order.status_label}</strong></p>
          </section>
          <section className="order-detail-card">
            <h2>Shipping address</h2>
            <address>
              {order.shipping_full_name}<br />
              {order.shipping_phone}<br />
              {order.shipping_address_line_1}{order.shipping_address_line_2 ? `, ${order.shipping_address_line_2}` : ''}<br />
              {order.shipping_city}, {order.shipping_state} {order.shipping_postal_code}<br />
              {order.shipping_country}
            </address>
            {order.delivery_instructions && <p>Delivery instructions: {order.delivery_instructions}</p>}
          </section>
        </div>
      </div>
    </main>
  )
}
