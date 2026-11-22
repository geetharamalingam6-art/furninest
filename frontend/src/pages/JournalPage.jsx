import { useMemo, useState } from 'react'
import { ArrowRight, Search } from 'lucide-react'
import { Link } from 'react-router-dom'
import { journalArticles, journalCategories } from '../data/journalArticles'
import usePageMetadata from '../hooks/usePageMetadata'

const PAGE_SIZE = 6

export default function JournalPage() {
  const [category, setCategory] = useState('All Stories')
  const [search, setSearch] = useState('')
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)
  usePageMetadata('FurniNest Journal | Stories for Better Living', 'Ideas, inspiration, and thoughtful ways to make your space feel like home.')

  const filteredArticles = useMemo(() => {
    const query = search.trim().toLowerCase()
    return journalArticles.filter((article) => {
      const matchesCategory = category === 'All Stories' || article.category === category
      const matchesSearch = !query || `${article.title} ${article.category} ${article.excerpt}`.toLowerCase().includes(query)
      return matchesCategory && matchesSearch
    })
  }, [category, search])

  function changeCategory(value) {
    setCategory(value)
    setVisibleCount(PAGE_SIZE)
  }

  return (
    <main className="content-page journal-page">
      <div className="page-section">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link><span>/</span><span>Journal</span>
        </nav>
        <header className="page-intro">
          <p className="eyebrow">THE FURNINEST JOURNAL</p>
          <h1>Stories for Better Living.</h1>
          <p>Ideas, inspiration, and thoughtful ways to make your space feel like home.</p>
        </header>

        <div className="journal-tools">
          <div className="journal-filters" role="group" aria-label="Filter journal by category">
            {journalCategories.map((item) => (
              <button
                className={category === item ? 'journal-filter journal-filter--active' : 'journal-filter'}
                key={item}
                type="button"
                aria-pressed={category === item}
                onClick={() => changeCategory(item)}
              >
                {item}
              </button>
            ))}
          </div>
          <label className="journal-search">
            <Search size={16} />
            <span className="visually-hidden">Search stories</span>
            <input
              type="search"
              value={search}
              placeholder="Search stories..."
              onChange={(event) => {
                setSearch(event.target.value)
                setVisibleCount(PAGE_SIZE)
              }}
            />
          </label>
        </div>

        {filteredArticles.length > 0 ? (
          <>
            <div className="journal-grid">
              {filteredArticles.slice(0, visibleCount).map((article) => (
                <article className="journal-card" key={article.slug}>
                  <Link className="journal-card-image" to={`/journal/${article.slug}`}>
                    <img src={article.image} alt={article.imageAlt} loading="lazy" />
                  </Link>
                  <div className="journal-card-copy">
                    <div className="journal-card-meta">
                      <span>{article.category}</span>
                      <time dateTime={article.publishedAt}>{new Date(`${article.publishedAt}T12:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</time>
                    </div>
                    <h2><Link to={`/journal/${article.slug}`}>{article.title}</Link></h2>
                    <p>{article.excerpt}</p>
                    <Link className="text-link" to={`/journal/${article.slug}`}>Read more <ArrowRight size={15} /></Link>
                  </div>
                </article>
              ))}
            </div>
            {visibleCount < filteredArticles.length && (
              <div className="journal-load-more">
                <button className="button button--outline" type="button" onClick={() => setVisibleCount((count) => count + PAGE_SIZE)}>
                  Load more stories
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="journal-empty">
            <h2>No stories found.</h2>
            <p>Try a different search or choose another category.</p>
            <button className="text-link" type="button" onClick={() => { setCategory('All Stories'); setSearch('') }}>Clear filters</button>
          </div>
        )}
      </div>
    </main>
  )
}
