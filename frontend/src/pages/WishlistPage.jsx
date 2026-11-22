import { Heart } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ApiError, ApiLoading, EmptyState } from '../components/ApiState'
import ProductCard from '../components/ProductCard'
import useStore from '../hooks/useStore'

export default function WishlistPage() {
  const { wishlistItems, wishlistError, wishlistLoading } = useStore()

  return (
    <main className="page-section wishlist-page">
      <div className="breadcrumbs"><Link to="/">Home</Link><span>/</span><span>Wishlist</span></div>
      <div className="section-heading">
        <div>
          <p className="eyebrow">KEEP THE GOOD THINGS CLOSE</p>
          <h1>Your saved pieces.</h1>
        </div>
        <Heart size={22} strokeWidth={1.4} />
      </div>
      {wishlistLoading && <ApiLoading label="Loading your saved pieces..." />}
      {wishlistError && <ApiError message={wishlistError} onRetry={() => window.location.reload()} />}
      {!wishlistLoading && !wishlistError && wishlistItems.length > 0 && (
        <div className="product-grid product-grid--four">
          {wishlistItems.map((item) => <ProductCard key={item.id} product={item.product} />)}
        </div>
      )}
      {!wishlistLoading && !wishlistError && wishlistItems.length === 0 && (
        <EmptyState title="A little room for inspiration.">
          Save pieces with the heart icon and they will be waiting here.
        </EmptyState>
      )}
    </main>
  )
}
