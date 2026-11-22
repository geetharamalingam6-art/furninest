import { ArrowUpRight, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ApiError, ApiLoading, EmptyState } from '../components/ApiState'
import ProductCard from '../components/ProductCard'
import FurnitureGallery from '../components/FurnitureGallery'
import { getCategoryImage, getProductImage } from '../data/furnitureImagery'
import useApiResource from '../hooks/useApiResource'

const heroImage =
  'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=2200&q=88'
function collection(data) {
  return Array.isArray(data) ? data : data?.results || []
}

function featuredSelection(products, limit) {
  const selected = []
  const rooms = new Set()

  for (const product of products) {
    const room = product.category?.slug || product.category?.name || product.id
    if (rooms.has(room)) continue
    rooms.add(room)
    selected.push(product)
    if (selected.length === limit) break
  }

  return selected
}

export default function HomePage() {
  const categories = useApiResource('/categories/?page_size=8')
  const featured = useApiResource('/products/featured/')
  const featuredProducts = featuredSelection(collection(featured.data), 8)

  return (
    <main>
      <section className="hero-wrap">
        <div className="hero-scene" style={{ backgroundImage: `url("${heroImage}")` }}>
          <div className="hero-shade" />
          <div className="hero-copy">
            <p className="eyebrow hero-eyebrow">FURNITURE FOR SLOWER DAYS</p>
            <h1>Timeless comfort<br />with <em>naturally crafted</em> forms.</h1>
            <p>Thoughtful furniture, made to bring warmth, balance, and a little more ease to home.</p>
            <Link className="button button--light" to="/shop">
              Shop the collection <ArrowUpRight size={16} />
            </Link>
          </div>
          <div className="hero-caption"><span>01 — 03</span><span>Made for living well</span></div>
        </div>
      </section>

      <section className="page-section category-section" aria-labelledby="category-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">EXPLORE BY ROOM</p>
            <h2 id="category-title">Find your feeling.</h2>
          </div>
          <Link className="text-link" to="/shop">View all categories <ArrowUpRight size={16} /></Link>
        </div>
        {categories.loading ? <ApiLoading label="Loading categories..." /> : null}
        {categories.error ? <ApiError message={categories.error} onRetry={categories.retry} /> : null}
        {!categories.loading && !categories.error && collection(categories.data).length > 0 && (
          <div className="category-grid">
            {collection(categories.data).map((category, index) => {
              const imagery = getCategoryImage(category, index)
              return (
                <Link
                  className="category-tile"
                  key={category.id}
                  to={`/shop?category__slug=${encodeURIComponent(category.slug)}`}
                >
                  <img src={imagery.src} alt={imagery.alt || ''} loading="lazy" />
                  <span className="category-tile-copy">
                    <strong>{category.name}</strong>
                    <small>{imagery.caption || `${category.product_count} pieces`}</small>
                  </span>
                  <ArrowUpRight size={17} className="category-arrow" />
                </Link>
              )
            })}
          </div>
        )}
        {!categories.loading && !categories.error && collection(categories.data).length === 0 && (
          <>
            <EmptyState title="A room for new ideas.">
              Categories will appear here as soon as they are added to the catalog.
            </EmptyState>
            <FurnitureGallery title="Room to imagine" />
          </>
        )}
      </section>

      <section className="featured-section" id="collection">
        <div className="page-section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">THE WELL-LIVED EDIT</p>
              <h2>Pieces to keep close.</h2>
            </div>
            <Link className="text-link" to="/shop">Shop all furniture <ArrowUpRight size={16} /></Link>
          </div>
          {featured.loading ? <ApiLoading /> : null}
          {featured.error ? <ApiError message={featured.error} onRetry={featured.retry} /> : null}
          {!featured.loading && !featured.error && collection(featured.data).length > 0 && (
            <div className="product-grid product-grid--four">
              {featuredProducts.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  imageOverride={getProductImage(product)}
                />
              ))}
            </div>
          )}
          {!featured.loading && !featured.error && collection(featured.data).length === 0 && (
            <EmptyState title="Good things are being made.">
              Featured pieces from the live catalog will be shown here.
            </EmptyState>
          )}
        </div>
      </section>

      <section className="editorial-section page-section" id="about">
        <div className="editorial-image">
          <img
            src="https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=85"
            alt="Warm, natural materials in a quiet living room"
            loading="lazy"
          />
          <span>THE FURNINEST WAY</span>
        </div>
        <div className="editorial-copy">
          <p className="eyebrow">LESS, BUT MORE MEANINGFUL</p>
          <h2>Good design makes room for life.</h2>
          <p>
            Natural materials, enduring shapes, and thoughtful details. We believe
            the things we live with should feel as good as the moments we live in.
          </p>
          <Link className="text-link" to="/shop">Discover our point of view <ArrowRight size={16} /></Link>
        </div>
      </section>

    </main>
  )
}
