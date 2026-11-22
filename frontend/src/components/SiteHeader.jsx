import { useState } from 'react'
import { Armchair, ClipboardList, Heart, LayoutDashboard, Menu, Search, ShoppingBag, UserRound, X } from 'lucide-react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import useAuth from '../hooks/useAuth'
import useStore from '../hooks/useStore'
import BagDrawer from './BagDrawer'

export default function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()
  const { user } = useAuth()
  const { itemCount, openBag } = useStore()

  function submitSearch(event) {
    event.preventDefault()
    navigate(`/shop${search.trim() ? `?search=${encodeURIComponent(search.trim())}` : ''}`)
    setSearchOpen(false)
    setMenuOpen(false)
  }

  return (
    <>
      <header className="site-header">
        <div className="header-inner">
          <button
            className="icon-button mobile-menu-button"
            type="button"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X size={19} /> : <Menu size={19} />}
          </button>
          <Link className="wordmark" to="/" aria-label="FurniNest home">
            <Armchair size={21} strokeWidth={1.6} />
            <span>FurniNest</span>
          </Link>

          <nav className={`main-nav ${menuOpen ? 'main-nav--open' : ''}`}>
            <NavLink end to="/" onClick={() => setMenuOpen(false)}>Home</NavLink>
            <NavLink to="/shop" onClick={() => setMenuOpen(false)}>Categories</NavLink>
            <NavLink to="/about" onClick={() => setMenuOpen(false)}>About us</NavLink>
            <NavLink to="/journal" onClick={() => setMenuOpen(false)}>Journal</NavLink>
            <NavLink to="/faq" onClick={() => setMenuOpen(false)}>FAQ</NavLink>
            <NavLink to="/contact" onClick={() => setMenuOpen(false)}>Contact</NavLink>
            {user?.is_staff && <NavLink to="/admin" onClick={() => setMenuOpen(false)}><LayoutDashboard size={14} /> Dashboard</NavLink>}
          </nav>

          <div className="header-actions">
            <button
              className="icon-button"
              type="button"
              aria-label={searchOpen ? 'Close search' : 'Search products'}
              onClick={() => setSearchOpen((open) => !open)}
            >
              {searchOpen ? <X size={18} /> : <Search size={18} />}
            </button>
            <button
              className="icon-button bag-trigger"
              type="button"
              aria-label={`Shopping bag, ${itemCount} items`}
              onClick={openBag}
            >
              <ShoppingBag size={18} />
              {itemCount > 0 && <span className="bag-count">{itemCount}</span>}
            </button>
            <Link className="icon-button wishlist-trigger" to="/wishlist" aria-label="Your wishlist" title="Your wishlist">
              <Heart size={18} />
            </Link>
            <Link className="icon-button orders-trigger" to="/orders" aria-label="Your orders" title="Order history">
              <ClipboardList size={18} />
            </Link>
            <Link className="icon-button account-link" to="/account" aria-label="Your account" title="Your account">
              <UserRound size={18} />
            </Link>
          </div>
        </div>
        {searchOpen && (
          <form className="header-search" onSubmit={submitSearch}>
            <Search size={17} />
            <input
              autoFocus
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search furniture..."
              aria-label="Search furniture"
            />
            <button type="submit">Search</button>
          </form>
        )}
      </header>
      <BagDrawer />
    </>
  )
}
