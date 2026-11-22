import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Clock3, Mail, MapPin, Phone } from 'lucide-react'
import api from '../services/api'
import usePageMetadata from '../hooks/usePageMetadata'
import { getRoomImages } from '../data/furnitureImagery'

const contactImage = getRoomImages().find((room) => room.name === 'Living room')

const contactItems = [
  { title: 'Email Support', value: import.meta.env.VITE_CONTACT_EMAIL, fallback: 'Email contact is being configured.', Icon: Mail },
  { title: 'Phone Support', value: import.meta.env.VITE_CONTACT_PHONE, fallback: 'Business phone details are being configured.', Icon: Phone },
  { title: 'Our Location', value: import.meta.env.VITE_CONTACT_ADDRESS, fallback: 'Business address is being configured.', Icon: MapPin },
  { title: 'Working Hours', value: import.meta.env.VITE_CONTACT_HOURS, fallback: 'Business hours are being confirmed.', Icon: Clock3 },
]

function getErrorMessage(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  const firstError = data && Object.values(data).flat().find((value) => typeof value === 'string')
  return firstError || 'We could not send your message. Please try again.'
}

export default function ContactPage() {
  const [form, setForm] = useState({ name: '', email: '', phone: '', subject: '', message: '' })
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  usePageMetadata('Contact Us | FurniNest', 'Contact the FurniNest team with a product or order question.')

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function submitContact(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    setStatus('')
    try {
      await api.post('/contact/', form)
      setStatus('Thank you. Your message has been received by our team.')
      setForm({ name: '', email: '', phone: '', subject: '', message: '' })
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="content-page contact-page">
      <div className="page-section">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link><span>/</span><span>Contact</span>
        </nav>
        <header className="page-intro">
          <p className="eyebrow">WE’RE HERE TO HELP</p>
          <h1>We’d Love to Hear From You.</h1>
          <p>Have a question, need assistance, or want to share an idea? Get in touch with us.</p>
        </header>

        <div className="contact-info-grid">
          {contactItems.map(({ title, value, fallback, Icon }) => (
            <article className="contact-info-card" key={title}>
              <Icon size={20} strokeWidth={1.6} />
              <h2>{title}</h2>
              {title === 'Email Support' && value
                ? <a href={`mailto:${value}`}>{value}</a>
                : <p>{value || fallback}</p>}
            </article>
          ))}
        </div>

        <section className="contact-layout">
          <div className="contact-form-panel">
            <p className="eyebrow">SEND A MESSAGE</p>
            <h2>How can we help?</h2>
            <form className="contact-form" onSubmit={submitContact}>
              <div className="contact-form-row">
                <label>Full name<input name="name" autoComplete="name" required maxLength={160} value={form.name} onChange={updateField} /></label>
                <label>Email address<input name="email" type="email" autoComplete="email" required maxLength={254} value={form.email} onChange={updateField} /></label>
              </div>
              <div className="contact-form-row">
                <label>Phone number<input name="phone" type="tel" autoComplete="tel" required pattern="\+?[0-9\s()-]{7,20}" title="Enter a valid phone number." value={form.phone} onChange={updateField} /></label>
                <label>Subject<input name="subject" required maxLength={200} value={form.subject} onChange={updateField} /></label>
              </div>
              <label>Message<textarea name="message" rows="6" required maxLength={5000} value={form.message} onChange={updateField} /></label>
              {status && <p className="form-notice" role="status">{status}</p>}
              {error && <p className="form-notice form-notice--error" role="alert">{error}</p>}
              <button className="button button--dark" type="submit" disabled={submitting}>
                {submitting ? 'Sending...' : 'Send message'}
              </button>
            </form>
          </div>
          <aside className="contact-aside">
            <p className="eyebrow">A THOUGHTFUL NEXT STEP</p>
            <h2>Need a quick answer?</h2>
            <p>Browse common questions or explore the collection while our contact details are being finalized.</p>
            <Link className="text-link" to="/faq">Visit the FAQ <span aria-hidden="true">→</span></Link>
            <Link className="text-link" to="/shop">Explore the store <span aria-hidden="true">→</span></Link>
            <div className="contact-aside-image">
              <img src={contactImage.src} alt={contactImage.alt} loading="lazy" />
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}
