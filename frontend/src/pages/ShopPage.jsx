import { ArrowDownUp, SlidersHorizontal } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { ApiError, ApiLoading, EmptyState } from '../components/ApiState'
import ProductCard from '../components/ProductCard'
import FurnitureGallery from '../components/FurnitureGallery'
import useApiResource from '../hooks/useApiResource'

function list(data) {
  return Array.isArray(data) ? data : data?.results || []
}

export default function ShopPage() {
  const [params, setParams] = useSearchParams()
  const query = params.toString()
  const productPath = `/products/${query ? `?${query}` : ''}`
  const products = useApiResource(productPath)
  const categories = useApiResource('/categories/?page_size=100')
  const selected = params.get('category__slug') || ''

  function setFilter(key, value) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    if (key !== 'page') next.delete('page')
    setParams(next)
  }

  function clearFilters() {
    setParams({})
  }

  const productList = list(products.data)
  const count = products.data?.count ?? productList.length
  const nextPage = products.data?.next
  const previousPage = products.data?.previous
  const selectedCategory = list(categories.data).find((category) => category.slug === selected)
  const pageTitle = selectedCategory?.name || 'Furniture for living.'
  const pageEyebrow = selectedCategory ? `${selectedCategory.name.toUpperCase()} COLLECTION` : 'A CONSIDERED COLLECTION'
  const pageIntro = selectedCategory
    ? `Thoughtfully chosen pieces for your ${selectedCategory.name.toLowerCase()}.`
    : 'Pieces with a point of view, and a place in your home.'

  return (
    <main className="shop-page page-section">
      <div className="breadcrumbs"><a href="/">Home</a><span>/</span><span>Shop</span></div>
      <div className="shop-title-row">
        <div>
          <p className="eyebrow">{pageEyebrow}</p>
          <h1>{pageTitle}</h1>
          <p className="shop-intro">{pageIntro}</p>
        </div>
        <label className="sort-control">
          <ArrowDownUp size={15} />
          <span className="visually-hidden">Sort products</span>
          <select
            value={params.get('ordering') || ''}
            onChange={(event) => setFilter('ordering', event.target.value)}
          >
            <option value="">Featured</option>
            <option value="price">Price: low to high</option>
            <option value="-price">Price: high to low</option>
            <option value="-created_at">Newest first</option>
            <option value="-average_rating">Best rated</option>
          </select>
        </label>
      </div>

      <div className="shop-layout">
        <aside className="shop-sidebar">
          <div className="filter-heading"><SlidersHorizontal size={16} /><span>Departments</span></div>
          <button className={`category-filter ${!selected ? 'category-filter--active' : ''}`} onClick={() => setFilter('category__slug', '')}>
            All furniture
          </button>
          {categories.loading && <span className="sidebar-muted">Loading categories…</span>}
          {categories.error && <ApiError message={categories.error} onRetry={categories.retry} />}
          {list(categories.data).map((category) => (
            <button
              className={`category-filter ${selected === category.slug ? 'category-filter--active' : ''}`}
              key={category.id}
              onClick={() => setFilter('category__slug', category.slug)}
            >
              <span>{category.name}</span>
              <small>{category.product_count}</small>
            </button>
          ))}
          <div className="sidebar-divider" />
          <label className="filter-label" htmlFor="material-filter">Material</label>
          <select
            id="material-filter"
            className="filter-select"
            value={params.get('material') || ''}
            onChange={(event) => setFilter('material', event.target.value)}
          >
            <option value="">All materials</option>
            <option value="Oak">Oak</option>
            <option value="Walnut">Walnut</option>
            <option value="Linen">Linen</option>
            <option value="Rattan">Rattan</option>
          </select>
          {query && <button className="clear-filters" onClick={clearFilters}>Clear filters</button>}
        </aside>

        <section className="shop-results" aria-live="polite">
          <div className="results-toolbar">
            <span>{count} {count === 1 ? 'piece' : 'pieces'}</span>
            {params.get('search') && <span>Search: “{params.get('search')}”</span>}
          </div>
          {products.loading && <ApiLoading />}
          {products.error && <ApiError message={products.error} onRetry={products.retry} />}
          {!products.loading && !products.error && productList.length > 0 && (
            <>
              <div className="product-grid">
                {productList.map((product) => <ProductCard key={product.id} product={product} />)}
              </div>
              {(nextPage || previousPage) && (
                <div className="pagination">
                  <button disabled={!previousPage} onClick={() => setFilter('page', String(Math.max(1, Number(params.get('page') || 1) - 1)))}>
                    Previous
                  </button>
                  <span>Page {params.get('page') || 1}</span>
                  <button disabled={!nextPage} onClick={() => setFilter('page', String(Number(params.get('page') || 1) + 1))}>
                    Next
                  </button>
                </div>
              )}
            </>
          )}
          {!products.loading && !products.error && productList.length === 0 && (
            <>
              <EmptyState title="No pieces found just yet.">
                Try another category or clear your filters. New furniture will appear here from the catalog.
              </EmptyState>
              {!selected && !params.get('search') && <FurnitureGallery title="Find inspiration by room" />}
            </>
          )}
        </section>
      </div>
    </main>
  )
}
