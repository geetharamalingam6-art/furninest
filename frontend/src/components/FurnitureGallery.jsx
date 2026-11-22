import { getRoomImages } from '../data/furnitureImagery'

export default function FurnitureGallery({ title = 'A little room inspiration' }) {
  return (
    <section className="furniture-gallery" aria-label={title}>
      <div className="furniture-gallery-heading">
        <p className="eyebrow">{title}</p>
        <p>Thoughtful spaces, made for everyday living.</p>
      </div>
      <div className="furniture-gallery-grid">
        {getRoomImages().map((room) => (
          <figure className="furniture-gallery-card" key={room.name}>
            <img src={room.src} alt={room.alt} loading="lazy" />
            <figcaption>
              <span>{room.name}</span>
              <strong>{room.caption}</strong>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}
