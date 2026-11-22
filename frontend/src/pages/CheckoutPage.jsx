import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, LockKeyhole } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiLoading } from '../components/ApiState'
import api from '../services/api'
import useStore from '../hooks/useStore'
import { getProductImage } from '../data/furnitureImagery'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

function apiMessage(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  if (data && typeof data === 'object') {
    const message = Object.values(data).flat().find((item) => typeof item === 'string')
    if (message) return message
  }
  return 'We could not complete checkout. Please try again.'
}

function loadRazorpay() {
  if (window.Razorpay) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.async = true
    script.onload = resolve
    script.onerror = () => reject(new Error('Razorpay checkout could not be loaded.'))
    document.body.appendChild(script)
  })
}

function razorpayContact(phone, country) {
  const value = String(phone || '').trim()
  const digits = value.replace(/\D/g, '')

  // Razorpay expects an international number. Do not let a short or malformed
  // saved address phone number be interpreted as a country code (for example,
  // a 9-digit Indian number being treated as +98...).
  if (value.startsWith('+')) {
    return digits.length >= 8 && digits.length <= 15 ? `+${digits}` : undefined
  }
  if (String(country || '').trim().toLowerCase() === 'india' && digits.length === 10) {
    return `+91${digits}`
  }
  return undefined
}

export default function CheckoutPage() {
  const navigate = useNavigate()
  const { items, cartLoading, cartError, retryCart } = useStore()
  const [addresses, setAddresses] = useState([])
  const [addressId, setAddressId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('cod')
  const [checkoutKey, setCheckoutKey] = useState(() => window.crypto.randomUUID())
  const [couponInput, setCouponInput] = useState('')
  const [appliedCoupon, setAppliedCoupon] = useState('')
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([api.get('/addresses/'), api.get('/orders/checkout/summary/')]).then(
      ([addressResponse, summaryResponse]) => {
        if (active) {
          const savedAddresses = addressResponse.data.results || addressResponse.data
          setAddresses(savedAddresses)
          setAddressId(String(savedAddresses.find((address) => address.is_default)?.id || savedAddresses[0]?.id || ''))
          setSummary(summaryResponse.data)
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
  }, [])

  async function applyCoupon(event) {
    event.preventDefault()
    setError('')
    try {
      const { data } = await api.get('/orders/checkout/summary/', {
        params: couponInput.trim() ? { coupon_code: couponInput.trim() } : {},
      })
      setSummary(data)
      setAppliedCoupon(data.coupon_code)
      setCheckoutKey(window.crypto.randomUUID())
    } catch (requestError) {
      setError(apiMessage(requestError))
    }
  }

  async function placeOrder(event) {
    event.preventDefault()
    if (!addressId) {
      setError('Add a shipping address before placing your order.')
      return
    }
    if (paymentMethod === 'razorpay') {
      try {
        await loadRazorpay()
      } catch (loadError) {
        setError(loadError.message)
        return
      }
    }
    setBusy(true)
    setError('')
    try {
      const { data } = await api.post('/orders/checkout/', {
        address_id: Number(addressId),
        payment_method: paymentMethod,
        coupon_code: appliedCoupon,
      }, { headers: { 'Idempotency-Key': checkoutKey } })
      if (paymentMethod === 'cod') {
        retryCart()
        navigate('/orders', { state: { placedOrder: data.order_number } })
        return
      }
      const RazorpayCheckout = window.Razorpay
      const contact = razorpayContact(data.order.shipping_phone, data.order.shipping_country)
      const checkout = new RazorpayCheckout({
        key: data.payment.key_id,
        amount: data.payment.amount,
        currency: data.payment.currency,
        name: 'FurniNest',
        description: `Order ${data.order.order_number}`,
        order_id: data.payment.order_id,
        prefill: {
          name: data.order.shipping_full_name,
          ...(contact ? { contact } : {}),
        },
        handler: async (paymentResponse) => {
          try {
            await api.post('/payments/verify/', {
              order_id: data.order.id,
              razorpay_order_id: paymentResponse.razorpay_order_id,
              razorpay_payment_id: paymentResponse.razorpay_payment_id,
              razorpay_signature: paymentResponse.razorpay_signature,
            })
            retryCart()
            navigate('/orders', { state: { placedOrder: data.order.order_number } })
          } catch (verifyError) {
            setError(apiMessage(verifyError))
          } finally {
            setBusy(false)
          }
        },
        modal: {
          ondismiss: () => {
            setError('Payment was cancelled. Your order remains pending and has not been marked as paid.')
            setBusy(false)
          },
        },
        theme: { color: '#70583f' },
      })
      checkout.on('payment.failed', (paymentFailure) => {
        const description = paymentFailure.error?.description
        setError(
          `${description || 'The payment could not be completed.'} Your order remains pending and has not been marked as paid. You can retry payment from this checkout.`,
        )
        setBusy(false)
      })
      checkout.open()
    } catch (requestError) {
      setError(apiMessage(requestError))
      setBusy(false)
    }
  }

  if (loading || cartLoading) return <main className="page-section"><ApiLoading label="Preparing your checkout..." /></main>
  if (cartError) return <main className="page-section"><p className="form-feedback form-feedback--error" role="alert">{cartError}</p><button className="button button--outline" onClick={retryCart}>Try again</button></main>
  if (items.length === 0) {
    return (
      <main className="page-section checkout-page">
        <div className="breadcrumbs"><Link to="/">Home</Link><span>/</span><span>Checkout</span></div>
        <h1>Your bag is empty.</h1>
        <Link className="button button--dark" to="/shop">Explore the collection</Link>
      </main>
    )
  }

  return (
    <main className="page-section checkout-page">
      <div className="breadcrumbs"><Link to="/">Home</Link><span>/</span><span>Checkout</span></div>
      <Link className="checkout-back" to="/shop"><ArrowLeft size={15} /> Continue shopping</Link>
      <div className="section-heading">
        <div><p className="eyebrow">ALMOST HOME</p><h1>Review your order.</h1></div>
      </div>
      {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
      <form className="checkout-layout" onSubmit={placeOrder}>
        <div className="checkout-main">
          <section className="checkout-card">
            <div className="checkout-card-heading"><span>01</span><h2>Delivery address</h2></div>
            {addresses.length === 0 ? (
              <div className="checkout-no-address">
                <p>Add a saved address to continue.</p>
                <Link className="button button--outline" to="/account">Manage addresses</Link>
              </div>
            ) : (
              <div className="checkout-address-list">
                {addresses.map((address) => (
                  <label className={`checkout-address ${String(address.id) === addressId ? 'checkout-address--selected' : ''}`} key={address.id}>
                    <input
                      type="radio"
                      name="address"
                      value={address.id}
                      checked={String(address.id) === addressId}
                      onChange={(event) => {
                        setAddressId(event.target.value)
                        setCheckoutKey(window.crypto.randomUUID())
                      }}
                    />
                    <span>
                      <strong>{address.label}{address.is_default ? ' · Default' : ''}</strong>
                      <span>{address.full_name} · {address.phone_number}</span>
                      <span>{address.address_line_1}{address.address_line_2 ? `, ${address.address_line_2}` : ''}, {address.city}, {address.state} {address.postal_code}</span>
                    </span>
                  </label>
                ))}
                <Link className="checkout-add-address" to="/account">+ Add or edit an address</Link>
              </div>
            )}
          </section>

          <section className="checkout-card">
            <div className="checkout-card-heading"><span>02</span><h2>Payment method</h2></div>
            <div className="checkout-payment-options">
              <label className={paymentMethod === 'cod' ? 'checkout-payment-option checkout-payment-option--selected' : 'checkout-payment-option'}>
                <input type="radio" name="payment" value="cod" checked={paymentMethod === 'cod'} onChange={() => { setPaymentMethod('cod'); setCheckoutKey(window.crypto.randomUUID()) }} />
                <span><strong>Cash on delivery</strong><small>Pay when your furniture arrives.</small></span>
              </label>
              <label className={`${paymentMethod === 'razorpay' ? 'checkout-payment-option checkout-payment-option--selected' : 'checkout-payment-option'}${summary?.razorpay_enabled ? '' : ' checkout-payment-option--disabled'}`}>
                <input type="radio" name="payment" value="razorpay" checked={paymentMethod === 'razorpay'} disabled={!summary?.razorpay_enabled} onChange={() => { setPaymentMethod('razorpay'); setCheckoutKey(window.crypto.randomUUID()) }} />
                <span><strong>Pay online with Razorpay</strong><small>{summary?.razorpay_enabled ? 'Cards, UPI and net banking · secure checkout.' : 'Add Razorpay test credentials to backend/.env, then restart Django.'}</small></span>
              </label>
            </div>
          </section>
        </div>

        <aside className="checkout-summary">
          <h2>Order summary <span>({items.reduce((count, item) => count + item.quantity, 0)} pieces)</span></h2>
          <div className="checkout-summary-items">
            {items.map((item) => (
              <div className="checkout-summary-item" key={item.id}>
                <img src={getProductImage(item.product).src} alt="" loading="lazy" />
                <span>{item.product.name} <small>× {item.quantity}</small></span>
                <strong>{money.format(Number(item.line_total))}</strong>
              </div>
            ))}
          </div>
          <form className="checkout-coupon" onSubmit={applyCoupon}>
            <label htmlFor="checkout-coupon">Promotion code</label>
            <div><input id="checkout-coupon" value={couponInput} onChange={(event) => setCouponInput(event.target.value)} placeholder="Enter code" /><button type="submit">Apply</button></div>
            {appliedCoupon && <small>Applied: {appliedCoupon}</small>}
          </form>
          {summary && (
            <div className="checkout-totals">
              <div><span>Subtotal</span><span>{money.format(Number(summary.subtotal))}</span></div>
              {Number(summary.discount_amount) > 0 && <div><span>Discount</span><span>−{money.format(Number(summary.discount_amount))}</span></div>}
              <div><span>Shipping</span><span>{Number(summary.shipping_amount) ? money.format(Number(summary.shipping_amount)) : 'Complimentary'}</span></div>
              <div><span>Tax</span><span>{money.format(Number(summary.tax_amount))}</span></div>
              <div className="checkout-total"><strong>Total</strong><strong>{money.format(Number(summary.total_amount))}</strong></div>
            </div>
          )}
          <button className="button button--dark checkout-submit" type="submit" disabled={busy || addresses.length === 0 || !summary}>
            {busy ? 'Please wait…' : 'Place order'} {!busy && <ArrowRight size={16} />}
          </button>
          <p className="checkout-secure"><LockKeyhole size={13} /> Your payment details are securely processed.</p>
        </aside>
      </form>
    </main>
  )
}
