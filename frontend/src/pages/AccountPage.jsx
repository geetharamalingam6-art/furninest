import { useEffect, useState } from 'react'
import { ArrowRight, LogOut, Pencil, Plus, Trash2, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import api from '../services/api'

const blankAddress = {
  label: 'Home',
  full_name: '',
  phone_number: '',
  address_line_1: '',
  address_line_2: '',
  city: '',
  state: '',
  postal_code: '',
  country: 'India',
  delivery_instructions: '',
  is_default: false,
}

function apiMessage(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  if (data && typeof data === 'object') {
    const value = Object.values(data).flat().find((item) => typeof item === 'string')
    if (value) return value
  }
  return 'The request could not be completed.'
}

export default function AccountPage() {
  const { user, refreshProfile, logout } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [addresses, setAddresses] = useState([])
  const [address, setAddress] = useState(blankAddress)
  const [editingAddressId, setEditingAddressId] = useState(null)
  const [passwords, setPasswords] = useState({ old_password: '', new_password: '', new_password_confirm: '' })
  const [newEmail, setNewEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([api.get('/profile/'), api.get('/addresses/')]).then(
      ([profileResponse, addressResponse]) => {
        if (active) {
          setProfile(profileResponse.data)
          setAddresses(addressResponse.data.results || addressResponse.data)
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

  async function saveProfile(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const { data } = await api.patch('/profile/', {
        full_name: profile.full_name,
        phone_number: profile.phone_number,
      })
      setProfile(data)
      await refreshProfile()
      setNotice('Your profile has been saved.')
    } catch (requestError) {
      setError(apiMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function changeEmail(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/account/change-email/', { email: newEmail })
      setNewEmail('')
      setNotice(data.detail)
    } catch (requestError) {
      setError(apiMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function resendVerification() {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/email/resend-verification/', { email: profile.email })
      setNotice(data.detail)
    } catch (requestError) {
      setError(apiMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function saveAddress(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const { data } = editingAddressId
        ? await api.patch(`/addresses/${editingAddressId}/`, address)
        : await api.post('/addresses/', address)
      setAddresses((current) => editingAddressId
        ? current.map((item) => item.id === data.id ? data : item)
        : [data, ...current])
      setAddress(blankAddress)
      setEditingAddressId(null)
      setNotice(editingAddressId ? 'Your address has been updated.' : 'Your address has been saved.')
    } catch (requestError) {
      setError(apiMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  function editAddress(item) {
    setEditingAddressId(item.id)
    setAddress({
      label: item.label,
      full_name: item.full_name,
      phone_number: item.phone_number,
      address_line_1: item.address_line_1,
      address_line_2: item.address_line_2 || '',
      city: item.city,
      state: item.state,
      postal_code: item.postal_code,
      country: item.country,
      delivery_instructions: item.delivery_instructions || '',
      is_default: item.is_default,
    })
  }

  function cancelAddressEdit() {
    setEditingAddressId(null)
    setAddress(blankAddress)
  }

  async function setDefaultAddress(addressId) {
    try {
      const { data } = await api.patch(`/addresses/${addressId}/`, { is_default: true })
      setAddresses((current) => current.map((item) => item.id === data.id ? data : { ...item, is_default: false }))
      setNotice('Default address updated.')
      setError('')
    } catch (requestError) {
      setError(apiMessage(requestError))
    }
  }

  async function deleteAddress(addressId) {
    try {
      await api.delete(`/addresses/${addressId}/`)
      setAddresses((current) => current.filter((item) => item.id !== addressId))
      setNotice('Address removed.')
      setError('')
    } catch (requestError) {
      setError(apiMessage(requestError))
    }
  }

  async function changePassword(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/auth/change-password/', passwords)
      setPasswords({ old_password: '', new_password: '', new_password_confirm: '' })
      setNotice(data.detail)
    } catch (requestError) {
      setError(apiMessage(requestError))
    } finally {
      setBusy(false)
    }
  }

  async function signOut() {
    try {
      await logout()
      navigate('/', { replace: true })
    } catch (requestError) {
      setError(apiMessage(requestError))
    }
  }

  return (
    <main className="account-page page-section">
      <div className="account-heading">
        <div>
          <p className="eyebrow">YOUR FURNINEST</p>
          <h1>Hello, {profile?.full_name?.split(' ')[0] || user?.full_name || 'there'}.</h1>
        </div>
        <button className="button button--outline" type="button" onClick={signOut}>
          <LogOut size={15} /> Sign out
        </button>
      </div>
      {error && <p className="form-feedback form-feedback--error" role="alert">{error}</p>}
      {notice && <p className="form-feedback form-feedback--success" role="status">{notice}</p>}
      {loading ? (
        <p className="account-loading">Loading your account…</p>
      ) : (
        <div className="account-layout">
          <div className="account-main">
            <section className="account-card">
              <h2>Personal details</h2>
              <form className="account-form" onSubmit={saveProfile}>
                <label>Full name<input value={profile?.full_name || ''} onChange={(event) => setProfile({ ...profile, full_name: event.target.value })} required /></label>
                <label>Email address<input type="email" value={profile?.email || ''} readOnly /></label>
                <label>Phone<input type="tel" value={profile?.phone_number || ''} onChange={(event) => setProfile({ ...profile, phone_number: event.target.value })} /></label>
                <button className="button button--dark" type="submit" disabled={busy}>Save details</button>
              </form>
              <div className="account-email-meta">
                <p>Email status: <strong>{profile?.email_verified ? 'Verified' : 'Not verified'}</strong></p>
                <p>Account created: {profile?.date_joined ? new Date(profile.date_joined).toLocaleDateString() : '—'}</p>
                {!profile?.email_verified && <button className="text-button" type="button" disabled={busy} onClick={resendVerification}>Resend verification email</button>}
              </div>
              <form className="account-form account-email-change" onSubmit={changeEmail}>
                <h3>Change email address</h3>
                <label>New email address<input type="email" value={newEmail} onChange={(event) => setNewEmail(event.target.value)} required /></label>
                <p>Your current address remains active until you verify the new one.</p>
                <button className="button button--outline" type="submit" disabled={busy}>Send verification link</button>
              </form>
            </section>

            <section className="account-card">
              <div className="account-card-title"><h2>Saved addresses</h2><span>{addresses.length}</span></div>
              {addresses.length > 0 && (
                <div className="address-list">
                  {addresses.map((item) => (
                    <article className="address-card" key={item.id}>
                      <div>
                        <div className="address-label">{item.label}{item.is_default && <span>DEFAULT</span>}</div>
                        <strong>{item.full_name}</strong>
                        <p>{item.address_line_1}{item.address_line_2 ? `, ${item.address_line_2}` : ''}<br />{item.city}, {item.state} {item.postal_code}<br />{item.phone_number}</p>
                      </div>
                      <div className="address-actions">
                        <button type="button" onClick={() => editAddress(item)}><Pencil size={13} /> Edit</button>
                        {!item.is_default && <button type="button" onClick={() => setDefaultAddress(item.id)}>Make default</button>}
                        <button className="icon-button" type="button" aria-label={`Delete ${item.label} address`} onClick={() => deleteAddress(item.id)}><Trash2 size={15} /></button>
                      </div>
                    </article>
                  ))}
                </div>
              )}
              <form className="account-form address-form" onSubmit={saveAddress}>
                <h3>{editingAddressId ? <Pencil size={16} /> : <Plus size={16} />} {editingAddressId ? 'Edit address' : 'Add a new address'}</h3>
                <div className="form-row">
                  <label>Address label<input value={address.label} onChange={(event) => setAddress({ ...address, label: event.target.value })} required /></label>
                  <label>Recipient name<input value={address.full_name} onChange={(event) => setAddress({ ...address, full_name: event.target.value })} required /></label>
                </div>
                <div className="form-row">
                  <label>Phone<input type="tel" value={address.phone_number} onChange={(event) => setAddress({ ...address, phone_number: event.target.value })} required /></label>
                  <label>Postal code<input value={address.postal_code} onChange={(event) => setAddress({ ...address, postal_code: event.target.value })} required /></label>
                </div>
                <label>Address line 1<input value={address.address_line_1} onChange={(event) => setAddress({ ...address, address_line_1: event.target.value })} required /></label>
                <label>Address line 2<input value={address.address_line_2} onChange={(event) => setAddress({ ...address, address_line_2: event.target.value })} /></label>
                <div className="form-row form-row--three">
                  <label>City<input value={address.city} onChange={(event) => setAddress({ ...address, city: event.target.value })} required /></label>
                  <label>State<input value={address.state} onChange={(event) => setAddress({ ...address, state: event.target.value })} required /></label>
                  <label>Country<input value={address.country} onChange={(event) => setAddress({ ...address, country: event.target.value })} required /></label>
                </div>
                <label>Delivery instructions<input value={address.delivery_instructions} onChange={(event) => setAddress({ ...address, delivery_instructions: event.target.value })} /></label>
                <div className="account-address-form-actions">
                  <button className="button button--outline" type="submit" disabled={busy}>{editingAddressId ? 'Update address' : 'Save address'}</button>
                  {editingAddressId && <button className="button button--outline" type="button" disabled={busy} onClick={cancelAddressEdit}><X size={14} /> Cancel edit</button>}
                </div>
              </form>
            </section>
          </div>

          <aside className="account-side">
            <section className="account-card">
              <h2>Change password</h2>
              <form className="account-form" onSubmit={changePassword}>
                <label>Current password<input type="password" autoComplete="current-password" value={passwords.old_password} onChange={(event) => setPasswords({ ...passwords, old_password: event.target.value })} required /></label>
                <label>New password<input type="password" autoComplete="new-password" minLength={8} value={passwords.new_password} onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })} required /></label>
                <label>Confirm new password<input type="password" autoComplete="new-password" minLength={8} value={passwords.new_password_confirm} onChange={(event) => setPasswords({ ...passwords, new_password_confirm: event.target.value })} required /></label>
                <button className="button button--dark" type="submit" disabled={busy}>Update password</button>
              </form>
            </section>
            <section className="account-card account-note">
              <p className="eyebrow">GOOD TO KNOW</p>
              <p>Keep an eye on delivery updates and revisit the pieces you have ordered.</p>
              <Link className="account-orders-link" to="/orders">View your orders <ArrowRight size={14} /></Link>
            </section>
          </aside>
        </div>
      )}
    </main>
  )
}
