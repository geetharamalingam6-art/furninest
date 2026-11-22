import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import AuthPage from './pages/AuthPage'
import AccountPage from './pages/AccountPage'
import SiteHeader from './components/SiteHeader'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import { StoreProvider } from './context/StoreContext'
import AdminPage from './pages/AdminPage'
import ProtectedAdminRoute from './components/ProtectedAdminRoute'
import HomePage from './pages/HomePage'
import CheckoutPage from './pages/CheckoutPage'
import OrdersPage from './pages/OrdersPage'
import OrderDetailPage from './pages/OrderDetailPage'
import ProductDetailPage from './pages/ProductDetailPage'
import ShopPage from './pages/ShopPage'
import WishlistPage from './pages/WishlistPage'
import AboutPage from './pages/AboutPage'
import JournalPage from './pages/JournalPage'
import JournalArticlePage from './pages/JournalArticlePage'
import FaqPage from './pages/FaqPage'
import ContactPage from './pages/ContactPage'
import SiteFooter from './components/SiteFooter'
import './App.css'
import './EditorialPages.css'

function NotFoundPage() {
  return (
    <main className="not-found-page">
      <p className="eyebrow">A LITTLE OFF THE PATH</p>
      <h1>This page isn't here.</h1>
      <a className="button button--dark" href="/">Return home</a>
    </main>
  )
}

function ScrollToTop() {
  const { pathname, hash } = useLocation()

  useEffect(() => {
    if (hash) {
      requestAnimationFrame(() => document.querySelector(hash)?.scrollIntoView())
    } else {
      window.scrollTo(0, 0)
    }
  }, [pathname, hash])

  return null
}

function Storefront() {
  return (
    <>
      <ScrollToTop />
      <SiteHeader />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/shop" element={<ShopPage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/journal/:slug" element={<JournalArticlePage />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/products/:slug" element={<ProductDetailPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="/forgot-password" element={<AuthPage mode="forgot" />} />
        <Route path="/reset-password" element={<AuthPage mode="reset" />} />
        <Route path="/verify-email" element={<AuthPage mode="verify" />} />
        <Route
          path="/account"
          element={<ProtectedRoute><AccountPage /></ProtectedRoute>}
        />
        <Route
          path="/wishlist"
          element={<ProtectedRoute><WishlistPage /></ProtectedRoute>}
        />
        <Route
          path="/checkout"
          element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>}
        />
        <Route
          path="/orders"
          element={<ProtectedRoute><OrdersPage /></ProtectedRoute>}
        />
        <Route
          path="/orders/:orderId"
          element={<ProtectedRoute><OrderDetailPage /></ProtectedRoute>}
        />
        <Route
          path="/admin"
          element={<ProtectedAdminRoute><AdminPage /></ProtectedAdminRoute>}
        />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <SiteFooter />
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <StoreProvider>
        <Storefront />
      </StoreProvider>
    </AuthProvider>
  )
}
