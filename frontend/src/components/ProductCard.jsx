import { useState } from 'react'
import { Heart, ShoppingBag, Star } from 'lucide-react'
import { Link } from 'react-router-dom'
import useStore from '../hooks/useStore'
import { getProductImage } from '../data/furnitureImagery'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export default function ProductCard({ product, onAdded, imageOverride }) {
  const { addItem, wishlist, toggleWishlist, wishlistError } = useStore()
  const [notice, setNotice] = useState('')
  const productImage = getProductImage(product)
  const image = imageOverride?.src || productImage.src
  const imageAlt = imageOverride?.alt || productImage.alt || product.name
  const isSaved = wishlist.includes(product.id)
  const currentPrice = Number(product.current_price ?? product.price)
  const hasDiscount = product.discount_price && Number(product.discount_price) < Number(product.price)
  const discount = hasDiscount
    ? Math.round((1 - Number(product.discount_price) / Number(product.price)) * 100)
    : 0

  async function addToBag() {
    const added = await addItem(product)
    setNotice(added ? 'Added to your bag.' : 'Could not add this piece. Check availability and try again.')
    onAdded?.(added ? `${product.name} added to your bag.` : `${product.name} is out of stock.`)
  }

  return (
    <article className="product-card">
      <div className="product-card-image">
        <Link to={`/products/${product.slug}`} aria-label={`View ${product.name}`}>
          <img src={image} alt={imageAlt} loading="lazy" />
        </Link>
        {discount > 0 && <span className="product-badge">-{discount}%</span>}
        {!discount && product.is_featured && <span className="product-badge">Featured</span>}
        <button
          className={`favorite-button ${isSaved ? 'favorite-button--active' : ''}`}
          type="button"
          aria-label={isSaved ? `Remove ${product.name} from wishlist` : `Add ${product.name} to wishlist`}
          aria-pressed={isSaved}
          onClick={async () => {
            const updated = await toggleWishlist(product.id)
            setNotice(updated ? (isSaved ? 'Removed from your wishlist.' : 'Saved to your wishlist.') : 'Could not update your wishlist.')
          }}
        >
          <Heart size={17} fill={isSaved ? 'currentColor' : 'none'} />
        </button>
        <button className="quick-add" type="button" disabled={product.stock_quantity < 1} onClick={addToBag}>
          <ShoppingBag size={15} />
          {product.stock_quantity < 1 ? 'Out of stock' : 'Add to bag'}
        </button>
      </div>
      <div className="product-card-copy">
        {notice && <span className="product-action-notice" role="status">{notice}</span>}
        {wishlistError && <span className="product-action-notice product-action-notice--error" role="alert">{wishlistError}</span>}
        <Link className="product-name" to={`/products/${product.slug}`}>{product.name}</Link>
        {(imageOverride?.caption || productImage.caption) && (
          <p className="product-card-caption">{imageOverride?.caption || productImage.caption}</p>
        )}
        <div className="product-price">
          <strong>{money.format(currentPrice)}</strong>
          {hasDiscount && <del>{money.format(Number(product.price))}</del>}
        </div>
        <div className="product-meta">
          {Number(product.review_count) > 0 ? (
            <>
              <span className="rating"><Star size={13} fill="currentColor" /> {Number(product.average_rating).toFixed(1)}</span>
              <span>{product.review_count} reviews</span>
            </>
          ) : (
            <span className="new-product">New arrival</span>
          )}
          <span className={product.stock_quantity > 0 ? 'delivery-note' : 'sold-out'}>
            {product.stock_quantity > 0 ? 'Ready to ship' : 'Currently unavailable'}
          </span>
        </div>
      </div>
    </article>
  )
}
