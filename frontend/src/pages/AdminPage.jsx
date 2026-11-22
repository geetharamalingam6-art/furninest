import { useEffect, useState } from 'react'
import { ArrowUpRight, Boxes, CircleDollarSign, ClipboardList, PackageSearch, RefreshCw, ShoppingBag } from 'lucide-react'
import api from '../services/api'

const ORDER_STATES = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['processing', 'cancelled'],
  processing: ['shipped', 'cancelled'],
  shipped: ['out_for_delivery'],
  out_for_delivery: ['delivered'],
  delivered: [],
  cancelled: [],
  returned: [],
}

const LABELS = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  processing: 'Processing',
  shipped: 'Shipped',
  out_for_delivery: 'Out for delivery',
  delivered: 'Delivered',
  cancelled: 'Cancelled',
  returned: 'Returned',
}

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

function apiMessage(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  if (data && typeof data === 'object') {
    const message = Object.values(data).flat().find((item) => typeof item === 'string')
    if (message) return message
  }
  return 'The dashboard could not be updated. Please try again.'
}

function adminBaseUrl() {
  return (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/api\/?$/, '')
}

export default function AdminPage() {
  const [overview, setOverview] = useState(null)
  const [orders, setOrders] = useState([])
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyOrder, setBusyOrder] = useState(null)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    Promise.all([
      api.get('/dashboard/overview/'),
      api.get('/dashboard/orders/', { params: { search, status: statusFilter || undefined } }),
    ]).then(
      ([overviewResponse, ordersResponse]) => {
        if (active) {
          setOverview(overviewResponse.data)
          setOrders(ordersResponse.data.results || ordersResponse.data)
          setLoading(false)
          setError('')
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
  }, [search, statusFilter, attempt])

  async function changeOrderStatus(order, nextStatus) {
    setBusyOrder(order.id)
    setError('')
    setNotice('')
    try {
      const { data } = await api.patch(`/dashboard/orders/${order.id}/status/`, { status: nextStatus })
      setOrders((current) => current.map((item) => item.id === data.id ? data : item))
      setNotice(`${data.order_number} is now ${data.status_label.toLowerCase()}.`)
      setAttempt((value) => value + 1)
    } catch (requestError) {
      setError(apiMessage(requestError))
    } finally {
      setBusyOrder(null)
    }
  }

  function applySearch(event) {
    event.preventDefault()
    setSearch(searchInput.trim())
  }

  const adminUrl = adminBaseUrl()

  return (
    <main className="admin-page page-section">
      <div className="admin-heading">
        <div><p className="eyebrow">FURNINEST OPERATIONS</p><h1>Store dashboard.</h1></div>
        <button className="button button--outline" type="button" onClick={() => { setLoading(true); setAttempt((value) => value + 1) }}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>
      {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
      {notice && <p className="form-feedback form-feedback--success" role="status">{notice}</p>}

      {loading && !overview ? (
        <p className="account-loading">Loading store data…</p>
      ) : overview && (
        <>
          <section className="admin-stat-grid" aria-label="Store overview">
            <article className="admin-stat-card"><span><ShoppingBag size={17} /> Orders</span><strong>{overview.total_orders}</strong><small>{overview.to_fulfill} to fulfill</small></article>
            <article className="admin-stat-card"><span><CircleDollarSign size={17} /> Paid revenue</span><strong>{money.format(Number(overview.paid_revenue))}</strong><small>Captured payments</small></article>
            <article className="admin-stat-card"><span><Boxes size={17} /> Active pieces</span><strong>{overview.active_products}</strong><small>{overview.low_stock_count} low in stock</small></article>
            <article className="admin-stat-card"><span><ClipboardList size={17} /> Active coupons</span><strong>{overview.active_coupons}</strong><small>Managed in Django admin</small></article>
          </section>

          <section className="admin-shortcuts" aria-label="Catalog management">
            <a href={`${adminUrl}/admin/products/product/`} target="_blank" rel="noreferrer">Manage products <ArrowUpRight size={14} /></a>
            <a href={`${adminUrl}/admin/products/category/`} target="_blank" rel="noreferrer">Manage categories <ArrowUpRight size={14} /></a>
            <a href={`${adminUrl}/admin/coupons/coupon/`} target="_blank" rel="noreferrer">Manage coupons <ArrowUpRight size={14} /></a>
          </section>

          <div className="admin-content-grid">
            <section className="admin-panel">
              <div className="admin-panel-heading">
                <div><p className="eyebrow">CUSTOMER ORDERS</p><h2>Order management</h2></div>
                <span>{orders.length} shown</span>
              </div>
              <div className="admin-filters">
                <form onSubmit={applySearch}>
                  <input aria-label="Search orders" value={searchInput} onChange={(event) => setSearchInput(event.target.value)} placeholder="Order number, customer…" />
                  <button className="button button--outline" type="submit">Search</button>
                </form>
                <select aria-label="Filter by order status" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="">All statuses</option>
                  {Object.entries(LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </div>
              {orders.length === 0 ? (
                <p className="admin-empty">No orders match the current filters.</p>
              ) : (
                <div className="admin-order-list">
                  {orders.map((order) => {
                    const transitions = ORDER_STATES[order.status] || []
                    return (
                      <article className="admin-order" key={order.id}>
                        <div className="admin-order-main">
                          <div>
                            <strong>{order.order_number}</strong>
                            <span>{order.shipping_full_name} · {order.shipping_city}</span>
                          </div>
                          <div className="admin-order-total">
                            <strong>{money.format(Number(order.total_amount))}</strong>
                            <span>{order.payment_status_label}</span>
                          </div>
                        </div>
                        <div className="admin-order-actions">
                          <span className={`admin-status admin-status--${order.status}`}>{order.status_label}</span>
                          {transitions.length > 0 && (
                            <select
                              aria-label={`Update status for ${order.order_number}`}
                              value=""
                              disabled={busyOrder === order.id}
                              onChange={(event) => changeOrderStatus(order, event.target.value)}
                            >
                              <option value="" disabled>Update status…</option>
                              {transitions.map((value) => <option value={value} key={value}>{LABELS[value]}</option>)}
                            </select>
                          )}
                        </div>
                      </article>
                    )
                  })}
                </div>
              )}
            </section>

            <aside className="admin-panel admin-inventory-panel">
              <div className="admin-panel-heading">
                <div><p className="eyebrow">INVENTORY</p><h2>Running low</h2></div>
                <PackageSearch size={18} />
              </div>
              {overview.low_stock_products.length === 0 ? (
                <p className="admin-empty">Everything active is stocked above the alert level.</p>
              ) : (
                <ul className="low-stock-list">
                  {overview.low_stock_products.map((product) => (
                    <li key={product.id}>
                      <span><strong>{product.name}</strong><small>{product.sku}</small></span>
                      <b>{product.stock_quantity} left</b>
                    </li>
                  ))}
                </ul>
              )}
              <a className="admin-inventory-link" href={`${adminUrl}/admin/products/product/`} target="_blank" rel="noreferrer">
                Update inventory <ArrowUpRight size={14} />
              </a>
            </aside>
          </div>
        </>
      )}
    </main>
  )
}
