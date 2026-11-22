import { useCallback, useEffect, useMemo, useState } from 'react'
import useAuth from '../hooks/useAuth'
import api from '../services/api'
import StoreContext from './storeContextValue'

function readStoredList(key) {
  try {
    const value = JSON.parse(window.localStorage.getItem(key) || '[]')
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

function getErrorMessage(error) {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  const firstFieldError = data && Object.values(data).flat().find((value) => typeof value === 'string')
  return firstFieldError || 'We could not update your shopping bag. Please try again.'
}

const EMPTY_ITEMS = []

export function StoreProvider({ children }) {
  const { user } = useAuth()
  const [cart, setCart] = useState(null)
  const [cartError, setCartError] = useState('')
  const [cartAttempt, setCartAttempt] = useState(0)
  const [guestWishlist, setGuestWishlist] = useState(() => readStoredList('furninest-wishlist'))
  const [serverWishlist, setServerWishlist] = useState([])
  const [wishlistItems, setWishlistItems] = useState([])
  const [wishlistError, setWishlistError] = useState('')
  const [wishlistLoadedUserId, setWishlistLoadedUserId] = useState(null)
  const [bagOpen, setBagOpen] = useState(false)

  useEffect(() => {
    let active = true
    api.get('/cart/').then(
      ({ data }) => {
        if (active) {
          setCart(data)
          setCartError('')
        }
      },
      (error) => {
        if (active) setCartError(getErrorMessage(error))
      },
    )
    return () => {
      active = false
    }
  }, [user?.id, cartAttempt])

  useEffect(() => {
    let active = true
    async function loadWishlist() {
      if (!user?.id) return
      try {
        const guestProducts = readStoredList('furninest-wishlist')
        for (const productId of guestProducts) {
          await api.post('/wishlist/add/', { product_id: productId })
        }
        const { data } = await api.get('/wishlist/')
        if (active) {
          setWishlistItems(data)
          setServerWishlist(data.map((item) => item.product.id))
          setGuestWishlist([])
          setWishlistError('')
          setWishlistLoadedUserId(user.id)
        }
      } catch (error) {
        if (active) setWishlistError(getErrorMessage(error))
      }
    }
    loadWishlist()
    return () => {
      active = false
    }
  }, [user?.id])

  useEffect(() => {
    window.localStorage.setItem('furninest-wishlist', JSON.stringify(guestWishlist))
  }, [guestWishlist])

  const addItem = useCallback(async (product, quantity = 1) => {
    if (!product || product.stock_quantity < 1) return false
    try {
      const { data } = await api.post('/cart/add/', {
        product_id: product.id,
        quantity,
      })
      setCart(data)
      setCartError('')
      return true
    } catch (error) {
      setCartError(getErrorMessage(error))
      return false
    }
  }, [])

  const updateQuantity = useCallback(async (itemId, quantity) => {
    try {
      const { data } = await api.patch(`/cart/items/${itemId}/`, { quantity })
      setCart(data)
      setCartError('')
    } catch (error) {
      setCartError(getErrorMessage(error))
    }
  }, [])

  const removeItem = useCallback(async (itemId) => {
    try {
      const { data } = await api.delete(`/cart/items/${itemId}/`)
      setCart(data)
      setCartError('')
    } catch (error) {
      setCartError(getErrorMessage(error))
    }
  }, [])

  const clearBag = useCallback(async () => {
    try {
      const { data } = await api.delete('/cart/clear/')
      setCart(data)
      setCartError('')
    } catch (error) {
      setCartError(getErrorMessage(error))
    }
  }, [])

  const toggleWishlist = useCallback(async (productId) => {
    setWishlistError('')
    if (!user?.id) {
      setGuestWishlist((current) =>
        current.includes(productId)
          ? current.filter((id) => id !== productId)
          : [...current, productId],
      )
      return true
    }

    const savedItem = wishlistItems.find((item) => item.product.id === productId)
    try {
      const { data } = savedItem
        ? await api.delete(`/wishlist/items/${savedItem.id}/`)
        : await api.post('/wishlist/add/', { product_id: productId })
      setWishlistItems(data)
      setServerWishlist(data.map((item) => item.product.id))
      return true
    } catch (error) {
      setWishlistError(getErrorMessage(error))
      return false
    }
  }, [user?.id, wishlistItems])

  const items = cart?.items || EMPTY_ITEMS
  const wishlist = user?.id ? serverWishlist : guestWishlist
  const value = useMemo(
    () => ({
      items,
      cart,
      cartError,
      cartLoading: cart === null && !cartError,
      wishlist,
      wishlistItems,
      wishlistError,
      wishlistLoading: Boolean(user?.id && !wishlistError && wishlistLoadedUserId !== user.id),
      bagOpen,
      itemCount: cart?.item_count || 0,
      subtotal: Number(cart?.subtotal || 0),
      addItem,
      updateQuantity,
      removeItem,
      clearBag,
      toggleWishlist,
      retryCart: () => setCartAttempt((current) => current + 1),
      openBag: () => setBagOpen(true),
      closeBag: () => setBagOpen(false),
    }),
    [
      items,
      cart,
      cartError,
      wishlist,
      wishlistError,
      wishlistItems,
      wishlistLoadedUserId,
      user?.id,
      bagOpen,
      addItem,
      updateQuantity,
      removeItem,
      clearBag,
      toggleWishlist,
    ],
  )

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}
