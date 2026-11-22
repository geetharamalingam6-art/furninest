import { useState } from 'react'
import { ArrowUp, Camera, ChevronDown, Mail, Pin, Play, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import useStore from '../hooks/useStore'

const copyrightYear = new Date().getFullYear()

const socialLinks = [
  { label: 'Instagram', Icon: Camera, href: import.meta.env.VITE_INSTAGRAM_URL },
  { label: 'Facebook', Icon: Users, href: import.meta.env.VITE_FACEBOOK_URL },
  { label: 'Pinterest', Icon: Pin, href: import.meta.env.VITE_PINTEREST_URL },
  { label: 'YouTube', Icon: Play, href: import.meta.env.VITE_YOUTUBE_URL },
]

function getErrorMessage(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  const firstError = data && Object.values(data).flat().find((value) => typeof value === 'string')
  return firstError || 'We could not subscribe you right now. Please try again.'
}

function FooterColumn({
  id,
  title,
  expanded,
  onToggle,
  onMouseEnter,
  onMouseLeave,
  onFocus,
  onBlur,
  children,
}) {
  const linksId = `footer-${id}-links`

  return (
    <nav
      className={`footer-column${expanded ? ' footer-column--open' : ''}`}
      aria-label={title}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onFocus={onFocus}
      onBlur={onBlur}
    >
      <h2>
        <button
          className="footer-column-toggle"
          type="button"
          aria-expanded={expanded}
          aria-controls={linksId}
          onClick={onToggle}
        >
          {title}
          <ChevronDown size={14} aria-hidden="true" />
        </button>
      </h2>
      <div className="footer-column-links" id={linksId} aria-hidden={!expanded}>
        {children}
      </div>
    </nav>
  )
}

export default function SiteFooter() {
  const [email, setEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [hoveredFooterColumn, setHoveredFooterColumn] = useState(null)
  const [focusedFooterColumn, setFocusedFooterColumn] = useState(null)
  const [toggledFooterColumn, setToggledFooterColumn] = useState(null)
  const { openBag } = useStore()

  function isFooterColumnOpen(id) {
    return hoveredFooterColumn === id || focusedFooterColumn === id || toggledFooterColumn === id
  }

  function footerColumnProps(id) {
    return {
      id,
      expanded: isFooterColumnOpen(id),
      onMouseEnter: () => {
        if (window.matchMedia('(hover: hover)').matches) {
          setHoveredFooterColumn(id)
        }
      },
      onMouseLeave: () => setHoveredFooterColumn((current) => current === id ? null : current),
      onFocus: () => setFocusedFooterColumn(id),
      onBlur: (event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setFocusedFooterColumn((current) => current === id ? null : current)
        }
      },
      onToggle: () => {
        setToggledFooterColumn((current) => current === id ? null : id)
        setFocusedFooterColumn(null)
      },
    }
  }

  async function subscribe(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setStatus('')
    try {
      await api.post('/newsletter/', { email })
      setStatus('You’re on the list. Thank you for subscribing.')
      setEmail('')
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <footer className="site-footer">
      <div className="site-footer-main page-section">
        <section className="footer-brand">
          <Link className="wordmark" to="/">
            <span>FurniNest</span>
          </Link>
          <p>Thoughtfully designed furniture and timeless pieces to make every space feel like home.</p>
          <div className="footer-socials" role="group" aria-label="Social media">
            {socialLinks.map(({ label, Icon, href }) => (
              href
                ? (
                  <a href={href} key={label} aria-label={label} target="_blank" rel="noreferrer">
                    <Icon size={16} strokeWidth={1.7} aria-hidden="true" />
                  </a>
                )
                : (
                  <span
                    className="footer-social-unconfigured"
                    key={label}
                    role="img"
                    aria-label={`${label} link will be added soon`}
                    title={`${label} link will be added soon`}
                  >
                    <Icon size={16} strokeWidth={1.7} aria-hidden="true" />
                  </span>
                )
            ))}
          </div>
          {socialLinks.every(({ href }) => !href) && (
            <p className="footer-socials-note">Social links will be added soon.</p>
          )}
        </section>

        <FooterColumn
          {...footerColumnProps('explore')}
          title="Explore"
        >
          <Link to="/">Home</Link>
          <Link to="/shop">Shop</Link>
          <Link to="/shop">Categories</Link>
          <Link to="/shop?ordering=-created_at">New arrivals</Link>
          <Link to="/shop?ordering=-average_rating">Best sellers</Link>
          <Link to="/about">About us</Link>
          <Link to="/journal">Journal</Link>
        </FooterColumn>

        <FooterColumn
          {...footerColumnProps('customer-service')}
          title="Customer Service"
        >
          <Link to="/contact">Contact us</Link>
          <Link to="/faq">FAQ</Link>
          <Link to="/faq#shipping">Shipping information</Link>
          <Link to="/faq#returns">Returns and refunds</Link>
          <Link to="/orders">Order tracking</Link>
          <Link to="/faq#policy-notices">Privacy policy</Link>
          <Link to="/faq#policy-notices">Terms and conditions</Link>
        </FooterColumn>

        <FooterColumn
          {...footerColumnProps('my-account')}
          title="My Account"
        >
          <Link to="/account">My account</Link>
          <Link to="/orders">My orders</Link>
          <button type="button" onClick={openBag}>Shopping bag</button>
          <Link to="/wishlist">Wishlist</Link>
          <Link to="/login">Login</Link>
          <Link to="/register">Register</Link>
        </FooterColumn>

        <section className="footer-newsletter">
          <h2>A Little Something for Your Home.</h2>
          <p>Be the first to discover new collections, thoughtful spaces, and exclusive updates.</p>
          <form onSubmit={subscribe}>
            <label className="visually-hidden" htmlFor="footer-newsletter-email">Email address</label>
            <input
              id="footer-newsletter-email"
              type="email"
              required
              maxLength={254}
              placeholder="Your email address"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <button type="submit" disabled={busy} aria-label="Subscribe to the newsletter">
              <Mail size={17} />
            </button>
          </form>
          {status && <p className="footer-form-status" role="status">{status}</p>}
          {error && <p className="footer-form-status footer-form-status--error" role="alert">{error}</p>}
        </section>
      </div>

      <div className="site-footer-bottom">
        <div className="page-section">
          <p>© {copyrightYear} FurniNest. All rights reserved.</p>
          <p>Made for the feeling of home.</p>
          <div>
            <Link to="/faq#policy-notices">Privacy</Link>
            <Link to="/faq#policy-notices">Terms</Link>
            <Link to="/faq#shipping">Shipping</Link>
            <Link to="/faq#returns">Returns</Link>
          </div>
          <button type="button" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
            Back to top <ArrowUp size={14} />
          </button>
        </div>
      </div>
    </footer>
  )
}
