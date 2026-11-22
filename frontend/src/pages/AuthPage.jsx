import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import api from '../services/api'

function messageFromError(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') {
    if (data.detail.toLowerCase().includes('no active account found')) {
      return 'We could not sign you in. Check your email and password, or use Forgot your password. If your account is unverified, enter your password and use Resend verification email below.'
    }
    if (data.detail.toLowerCase().includes('please verify your email')) {
      return 'Please verify your email before signing in. Use Resend verification email below to request a new link.'
    }
    return data.detail
  }
  if (data && typeof data === 'object') {
    const fieldLabels = {
      email: 'Email',
      full_name: 'Name',
      password: 'Password',
      password_confirm: 'Confirm password',
      phone_number: 'Phone number',
    }
    const messages = Object.entries(data).flatMap(([field, value]) => {
      const fieldMessages = Array.isArray(value) ? value : [value]
      return fieldMessages
        .filter((message) => typeof message === 'string')
        .map((message) => {
          const cleaned = message.replace(/^detail\s*:\s*/i, '')
          if (cleaned.toLowerCase().includes('please verify your email')) {
            return 'Please verify your email before signing in. Use Resend verification email below to request a new link.'
          }
          return ['detail', 'non_field_errors'].includes(field)
            ? cleaned
            : `${fieldLabels[field] || field}: ${cleaned}`
        })
    })
    if (messages.length) return messages.join(' ')
  }
  if (error.response?.status >= 500) {
    return `The backend could not complete this request (HTTP ${error.response.status}). Check the Django terminal for the server error.`
  }
  if (!error.response && error.request) {
    return 'Could not reach the backend. Start Django with backend/runserver.bat and try again.'
  }
  return 'We could not complete that request. Please try again.'
}

export default function AuthPage({ mode }) {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [values, setValues] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    password_confirm: '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [verifying, setVerifying] = useState(mode === 'verify')

  const isRegister = mode === 'register'
  const isForgot = mode === 'forgot'
  const isReset = mode === 'reset'
  const isVerify = mode === 'verify'
  const title = isRegister
    ? 'Make yourself at home.'
    : isForgot
      ? 'A fresh start.'
      : isReset
        ? 'Choose a new password.'
        : 'Welcome back.'

  function updateField(event) {
    setValues((current) => ({ ...current, [event.target.name]: event.target.value }))
    setError('')
  }

  useEffect(() => {
    if (!isVerify) return undefined
    const params = new URLSearchParams(location.search)
    let active = true
    api.post('/email/verify/', {
      uid: params.get('uid') || '',
      token: params.get('token') || '',
    }).then(({ data }) => {
      if (active) setSuccess(data.detail)
    }).catch((requestError) => {
      if (active) setError(messageFromError(requestError))
    }).finally(() => {
      if (active) setVerifying(false)
    })
    return () => { active = false }
  }, [isVerify, location.search])

  async function resendVerification() {
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const { data } = await api.post('/email/resend-verification/', {
        email: values.email,
        password: values.password,
      })
      setSuccess(data.detail)
    } catch (requestError) {
      setError(messageFromError(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function submit(event) {
    event.preventDefault()
    if (isRegister && values.password !== values.password_confirm) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      if (mode === 'login') {
        await login(values.email, values.password)
        navigate(location.state?.from?.pathname || '/account', { replace: true })
      } else if (isRegister) {
        const data = await register(values)
        setSuccess(data.detail)
      } else if (isForgot) {
        const { data } = await api.post('/auth/forgot-password/', { email: values.email })
        setSuccess(data.detail)
      } else {
        const params = new URLSearchParams(location.search)
        const { data } = await api.post('/auth/reset-password/', {
          uid: params.get('uid') || '',
          token: params.get('token') || '',
          new_password: values.password,
          new_password_confirm: values.password_confirm,
        })
        setSuccess(data.detail)
      }
    } catch (requestError) {
      setError(messageFromError(requestError))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-image" aria-label="Warmly furnished living room">
        <div className="auth-image-copy">
          <p className="eyebrow">FURNINEST — A HOME FOR THOUGHTFUL LIVING</p>
          <p>Make room<br />for what matters.</p>
        </div>
      </div>
      <section className="auth-panel">
        <Link className="auth-back" to="/">
          <ArrowLeft size={15} /> Back to the store
        </Link>
        <div className="auth-form-wrap">
          <p className="eyebrow">{isRegister ? 'JOIN OUR COMMUNITY' : 'YOUR FURNINEST ACCOUNT'}</p>
          <h1>{isVerify ? 'Verify your email.' : title}</h1>
          <p className="auth-subtitle">
            {isRegister
              ? 'Save your favorite pieces and keep your orders close.'
              : isForgot
                ? 'Enter your email and we will send a password reset link.'
              : isReset
                  ? 'Use a new password you have not used before.'
                  : isVerify ? 'Confirming your email address.' : 'Sign in to pick up where you left off.'}
          </p>

          {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
          {success && <p className="form-feedback form-feedback--success" role="status">{success}</p>}

          {!(isForgot && success) && !(isReset && success) && !(isRegister && success) && !isVerify && (
            <form className="auth-form" onSubmit={submit}>
              {isRegister && (
                <>
                  <label>
                    Full name
                    <input name="full_name" value={values.full_name} onChange={updateField} autoComplete="name" required />
                  </label>
                  <label>
                    Phone number <span>(optional)</span>
                    <input name="phone_number" type="tel" value={values.phone_number} onChange={updateField} autoComplete="tel" />
                  </label>
                </>
              )}
              {!(isReset) && (
                <label>
                  Email address
                  <input name="email" type="email" value={values.email} onChange={updateField} autoComplete="email" required />
                </label>
              )}
              {!isForgot && (
                <>
                  <label>
                    {isReset ? 'New password' : 'Password'}
                    <input
                      name="password"
                      type="password"
                      value={values.password}
                      onChange={updateField}
                      autoComplete={isRegister || isReset ? 'new-password' : 'current-password'}
                      aria-describedby={isRegister ? 'auth-password-help' : undefined}
                      minLength={8}
                      required
                    />
                  </label>
                  {isRegister && (
                    <p className="auth-password-help" id="auth-password-help">
                      Use at least 8 characters. Avoid common or number-only passwords and details from your name or email.
                    </p>
                  )}
                </>
              )}
              {(isRegister || isReset) && (
                <label>
                  Confirm password
                  <input
                    name="password_confirm"
                    type="password"
                    value={values.password_confirm}
                    onChange={updateField}
                    autoComplete="new-password"
                    minLength={8}
                    required
                  />
                </label>
              )}
              <button className="button button--dark auth-submit" disabled={busy} type="submit">
                {busy ? 'Please wait…' : isRegister ? 'Create account' : isForgot ? 'Send reset link' : isReset ? 'Update password' : 'Sign in'}
                {!busy && <ArrowRight size={16} />}
              </button>
            </form>
          )}

          {mode === 'login' && (
            <div className="auth-links">
              <button className="text-button" type="button" disabled={busy || !values.email || !values.password} onClick={resendVerification}>Resend verification email</button>
              <Link to="/forgot-password">Forgot your password?</Link>
              <p>New to FurniNest? <Link to="/register" state={location.state}>Create an account</Link></p>
            </div>
          )}
          {isVerify && verifying && <p className="account-loading" role="status">Verifying your email…</p>}
          {isVerify && !verifying && <p className="auth-switch"><Link to="/login">Continue to sign in</Link></p>}
          {(isRegister && success) && (
            <div className="auth-switch">
              <p><Link to="/login">Continue to sign in</Link></p>
              <button className="text-button" type="button" disabled={busy} onClick={resendVerification}>Resend verification email</button>
            </div>
          )}
          {isRegister && <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>}
          {isForgot && <p className="auth-switch">Remembered it? <Link to="/login">Back to sign in</Link></p>}
          {isReset && success && <p className="auth-switch"><Link to="/login">Sign in with your new password</Link></p>}
        </div>
        <p className="auth-privacy">Your details are kept private and secure.</p>
      </section>
    </main>
  )
}
