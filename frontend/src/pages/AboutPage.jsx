import { ArrowRight, Leaf, HeartHandshake, Ruler, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import usePageMetadata from '../hooks/usePageMetadata'
import { getRoomImages } from '../data/furnitureImagery'

const rooms = getRoomImages()
const livingRoom = rooms.find((room) => room.name === 'Living room')
const bedroom = rooms.find((room) => room.name === 'Bedroom')

const values = [
  { title: 'Thoughtful Design', description: 'Useful forms and considered details make room for everyday life.', Icon: Sparkles },
  { title: 'Quality Materials', description: 'We look for honest materials, lasting finishes, and careful construction.', Icon: Leaf },
  { title: 'Comfort and Functionality', description: 'Furniture should feel good to live with, not just good to look at.', Icon: Ruler },
  { title: 'Customer Care', description: 'Helpful guidance should make choosing and caring for furniture easier.', Icon: HeartHandshake },
]

export default function AboutPage() {
  usePageMetadata('About FurniNest | Furniture for Living Well', 'Discover the FurniNest approach to thoughtful furniture, timeless design, and comfortable living.')

  return (
    <main className="editorial-page">
      <section className="editorial-hero" style={{ backgroundImage: `url("${livingRoom.src}")` }}>
        <div className="editorial-hero-shade" />
        <div className="editorial-hero-copy">
          <p className="eyebrow">OUR POINT OF VIEW</p>
          <h1>A Home Begins with the Things You Love.</h1>
          <p>Thoughtful furniture and considered details for spaces that feel like your own.</p>
        </div>
      </section>

      <div className="page-section editorial-content">
        <nav className="breadcrumbs" aria-label="Breadcrumb">
          <Link to="/">Home</Link><span>/</span><span>About us</span>
        </nav>

        <section className="story-grid">
          <div>
            <p className="eyebrow">OUR STORY</p>
            <h2>Make room for what matters.</h2>
          </div>
          <div className="story-copy">
            <p>FurniNest is built around a simple idea: the things we live with should support the way we want to live. We bring together furniture and home pieces chosen for their comfort, usefulness, and enduring character.</p>
            <p>Our journey is guided by a love of thoughtful spaces—from the first quiet corner to the rooms where friends and family gather. We believe good design is not about having more. It is about choosing well and making a home feel personal.</p>
            <p>We continue to build a collection with care, sharing clear product details and helpful support as we grow.</p>
          </div>
        </section>

        <section className="mission-grid" aria-label="Our mission and vision">
          <article>
            <p className="eyebrow">OUR MISSION</p>
            <h2>Bring thoughtful design home.</h2>
            <p>To bring thoughtfully designed, functional, and beautiful furniture into every home.</p>
          </article>
          <article>
            <p className="eyebrow">OUR VISION</p>
            <h2>Spaces that feel like you.</h2>
            <p>To inspire people to create spaces that reflect their personality and lifestyle.</p>
          </article>
        </section>

        <section className="values-section">
          <div className="centered-heading">
            <p className="eyebrow">THE FURNINEST DIFFERENCE</p>
            <h2>Why choose FurniNest?</h2>
          </div>
          <div className="value-grid">
            {values.map(({ title, description, Icon }) => (
              <article className="value-card" key={title}>
                <Icon size={22} strokeWidth={1.5} />
                <h3>{title}</h3>
                <p>{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="philosophy-grid">
          <div className="philosophy-image">
            <img src={bedroom.src} alt={bedroom.alt} loading="lazy" />
            <span>TIMELESS BY NATURE</span>
          </div>
          <div>
            <p className="eyebrow">OUR DESIGN PHILOSOPHY</p>
            <h2>Simple forms. Thoughtful craft. Room to live.</h2>
            <p>We value pieces that balance simplicity with warmth. Natural textures, useful details, and comfortable proportions help furniture fit into real life and feel at home for years to come.</p>
            <Link className="text-link" to="/shop">Explore the collection <ArrowRight size={16} /></Link>
          </div>
        </section>

        <section className="about-cta">
          <p className="eyebrow">FIND YOUR NEXT FAVORITE</p>
          <h2>Make Yourself at Home.</h2>
          <div>
            <Link className="button button--dark" to="/shop">Explore collections</Link>
            <Link className="button button--outline" to="/contact">Contact us</Link>
          </div>
        </section>
      </div>
    </main>
  )
}
