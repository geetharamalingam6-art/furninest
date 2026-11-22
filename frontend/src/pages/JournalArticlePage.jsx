import { ArrowLeft, ArrowRight } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { journalArticles } from '../data/journalArticles'
import usePageMetadata from '../hooks/usePageMetadata'

export default function JournalArticlePage() {
  const { slug } = useParams()
  const article = journalArticles.find((item) => item.slug === slug)
  const related = journalArticles.filter((item) => item.slug !== slug).slice(0, 3)
  usePageMetadata(
    article ? `${article.title} | FurniNest Journal` : 'Story not found | FurniNest Journal',
    article?.excerpt || 'Browse thoughtful stories and inspiration from FurniNest.',
  )

  if (!article) {
    return (
      <main className="content-page journal-article-page">
        <div className="page-section journal-empty">
          <p className="eyebrow">THE JOURNAL</p>
          <h1>This story is not available.</h1>
          <Link className="text-link" to="/journal"><ArrowLeft size={15} /> Back to Journal</Link>
        </div>
      </main>
    )
  }

  return (
    <main className="content-page journal-article-page">
      <article className="article-content">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link><span>/</span><Link to="/journal">Journal</Link><span>/</span><span>{article.category}</span>
        </nav>
        <header className="article-header">
          <p className="eyebrow">{article.category}</p>
          <h1>{article.title}</h1>
          <p className="article-excerpt">{article.excerpt}</p>
          <time dateTime={article.publishedAt}>{new Date(`${article.publishedAt}T12:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}</time>
        </header>
        <figure className="article-hero-image">
          <img src={article.image} alt={article.imageAlt} />
        </figure>
        <div className="article-body">
          <p className="article-lede">{article.excerpt}</p>
          {article.body.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}
        </div>
        <Link className="text-link article-back-link" to="/journal"><ArrowLeft size={15} /> Back to Journal</Link>
      </article>
      <section className="related-stories page-section">
        <div className="centered-heading">
          <p className="eyebrow">KEEP READING</p>
          <h2>More stories for home.</h2>
        </div>
        <div className="related-story-grid">
          {related.map((item) => (
            <Link className="related-story" key={item.slug} to={`/journal/${item.slug}`}>
              <img src={item.image} alt={item.imageAlt} loading="lazy" />
              <span>{item.category}</span>
              <strong>{item.title}</strong>
              <ArrowRight size={16} />
            </Link>
          ))}
        </div>
      </section>
    </main>
  )
}
