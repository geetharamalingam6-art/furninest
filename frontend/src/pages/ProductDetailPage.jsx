import { useEffect, useState } from 'react'
import { ArrowLeft, ChevronDown, ChevronRight, Minus, Plus, ShoppingBag, Star, X, ZoomIn } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ApiError, ApiLoading, EmptyState } from '../components/ApiState'
import ProductCard from '../components/ProductCard'
import useStore from '../hooks/useStore'
import useApiResource from '../hooks/useApiResource'
import { getProductImage, isDemoProductImage } from '../data/furnitureImagery'

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

function list(data) {
  return Array.isArray(data) ? data : data?.results || []
}

export default function ProductDetailPage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const productResource = useApiResource(`/products/${encodeURIComponent(slug)}/`)
  const product = productResource.data
  const relatedPath = product?.category?.slug
    ? `/products/?category__slug=${encodeURIComponent(product.category.slug)}&page_size=5`
    : '/products/?page_size=5'
  const related = useApiResource(relatedPath)
  const [activeImage, setActiveImage] = useState(0)
  const [imageViewerOpen, setImageViewerOpen] = useState(false)
  const [quantity, setQuantity] = useState(1)
  const [notice, setNotice] = useState('')
  const { addItem, openBag } = useStore()

  useEffect(() => {
    if (!imageViewerOpen) return undefined

    const previousOverflow = document.body.style.overflow
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setImageViewerOpen(false)
    }

    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [imageViewerOpen])

  if (productResource.loading) {
    return <main className="page-section detail-state"><ApiLoading label="Loading this piece..." /></main>
  }
  if (productResource.error) {
    return (
      <main className="page-section detail-state">
        <ApiError message={productResource.error} onRetry={productResource.retry} />
        <Link className="text-link" to="/shop"><ArrowLeft size={16} /> Back to the collection</Link>
      </main>
    )
  }
  if (!product) {
    return <main className="page-section detail-state"><EmptyState title="This piece has moved on."><Link to="/shop">Browse the collection</Link></EmptyState></main>
  }

  const images = (product.images || []).filter((item) => !isDemoProductImage(item.image))
  const fallbackImage = getProductImage(product)
  const image = images[activeImage]?.image || fallbackImage.src
  const imageAlt = images[activeImage]?.alt_text || (images.length ? product.name : fallbackImage.alt)
  const stock = Number(product.stock_quantity)
  const currentPrice = Number(product.current_price ?? product.price)

  async function addToBag(buyNow = false) {
    if (await addItem(product, quantity)) {
      setNotice(`${product.name} added to your bag.`)
      if (buyNow) openBag()
    } else {
      setNotice('Could not add this piece. Check availability and try again.')
    }
  }

  return (
    <main className="page-section detail-page">
      <div className="breadcrumbs"><Link to="/">Home</Link><span>/</span><Link to="/shop">Shop</Link><span>/</span><span>{product.category.name}</span></div>
      <section className="detail-layout">
        <div className="gallery">
          <div className="gallery-main">
            <button
              className="gallery-image-button"
              type="button"
              aria-label={`View larger image of ${product.name}`}
              onClick={() => setImageViewerOpen(true)}
            >
              <img src={image} alt={imageAlt} />
              <span className="gallery-zoom-indicator" aria-hidden="true"><ZoomIn size={18} /></span>
            </button>
            <span className="gallery-label">{product.is_featured ? 'THE EDIT' : 'FURNINEST OBJECTS'}</span>
          </div>
          {images.length > 1 && (
            <div className="gallery-thumbs" aria-label="Product images">
              {images.map((item, index) => (
                <button
                  className={index === activeImage ? 'gallery-thumb gallery-thumb--active' : 'gallery-thumb'}
                  key={item.id}
                  type="button"
                  aria-label={`Show image ${index + 1}`}
                  aria-pressed={index === activeImage}
                  onClick={() => setActiveImage(index)}
                >
                  <img src={item.image} alt="" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="detail-copy">
          <p className="eyebrow">{product.brand?.name || product.category.name}</p>
          <h1>{product.name}</h1>
          <div className="detail-rating">
            {Number(product.review_count) > 0 ? (
              <>
                <span className="rating"><Star size={15} fill="currentColor" /> {Number(product.average_rating).toFixed(1)}</span>
                <a href="#reviews">{product.review_count} reviews</a>
              </>
            ) : <span className="new-product">A new arrival</span>}
          </div>
          <div className="detail-price">{money.format(currentPrice)}
            {product.discount_price && <del>{money.format(Number(product.price))}</del>}
          </div>
          <p className="detail-description">{product.description}</p>

          <div className="detail-attributes">
            {product.material && <div><span>Material</span><strong>{product.material}</strong></div>}
            {product.color && <div><span>Color</span><strong>{product.color}</strong></div>}
            {product.dimensions && <div><span>Dimensions</span><strong>{product.dimensions}</strong></div>}
            {product.weight_kg && <div><span>Weight</span><strong>{product.weight_kg} kg</strong></div>}
          </div>

          <div className="stock-status">
            <span className={stock > 0 ? 'stock-dot' : 'stock-dot stock-dot--out'} />
            {stock > 0 ? (stock < 5 ? `Only ${stock} left in stock` : 'In stock — ready to ship') : 'Currently unavailable'}
          </div>

          <div className="detail-actions">
            <div className="quantity-control quantity-control--large">
              <button type="button" aria-label="Decrease quantity" disabled={quantity <= 1} onClick={() => setQuantity((value) => value - 1)}><Minus size={15} /></button>
              <span>{quantity}</span>
              <button type="button" aria-label="Increase quantity" disabled={quantity >= stock} onClick={() => setQuantity((value) => value + 1)}><Plus size={15} /></button>
            </div>
            <button className="button button--outline add-cart-button" type="button" disabled={stock < 1} onClick={() => addToBag()}>
              Add to bag <ShoppingBag size={16} />
            </button>
            <button className="button button--dark buy-button" type="button" disabled={stock < 1} onClick={() => addToBag(true)}>
              Buy this piece
            </button>
          </div>
          {notice && <p className="form-notice" role="status">{notice}</p>}

          <div className="detail-accordions">
            <details open>
              <summary>Details & specifications <ChevronDown size={16} /></summary>
              <div className="spec-list">
                {Object.entries(product.specifications || {}).length > 0
                  ? Object.entries(product.specifications).map(([key, value]) => <div key={key}><span>{key}</span><strong>{String(value)}</strong></div>)
                  : <p>Designed with enduring materials and thoughtful proportions.</p>}
              </div>
            </details>
            <details><summary>Shipping & delivery <ChevronDown size={16} /></summary><p>Delivery options are confirmed at checkout. Large furniture is delivered with care to your home.</p></details>
            <details><summary>Care & returns <ChevronDown size={16} /></summary><p>Care instructions are supplied with your order. Please contact our team for help with this piece.</p></details>
          </div>
        </div>
      </section>

      {imageViewerOpen && (
        <div
          className="image-viewer-backdrop"
          onClick={(event) => {
            if (event.target === event.currentTarget) setImageViewerOpen(false)
          }}
        >
          <div className="image-viewer" role="dialog" aria-modal="true" aria-label={`${product.name} image preview`}>
            <button className="image-viewer-close" type="button" aria-label="Close image preview" onClick={() => setImageViewerOpen(false)}>
              <X size={20} />
            </button>
            <img src={image} alt={imageAlt} />
          </div>
        </div>
      )}

      <section className="related-section" id="reviews">
        <div className="section-heading">
          <div><p className="eyebrow">CONSIDER THESE, TOO</p><h2>In good company.</h2></div>
          <button className="text-link text-button" onClick={() => navigate('/shop')}>All furniture <ChevronRight size={16} /></button>
        </div>
        {related.loading && <ApiLoading />}
        {related.error && <ApiError message={related.error} onRetry={related.retry} />}
        {!related.loading && !related.error && list(related.data).filter((item) => item.id !== product.id).length > 0 && (
          <div className="product-grid product-grid--four">
            {list(related.data).filter((item) => item.id !== product.id).slice(0, 4).map((item) => <ProductCard key={item.id} product={item} />)}
          </div>
        )}
        {!related.loading && !related.error && list(related.data).filter((item) => item.id !== product.id).length === 0 && (
          <EmptyState title="Nothing similar just yet."><Link to="/shop">Explore the full collection.</Link></EmptyState>
        )}
      </section>
    </main>
  )
}
