import { getRoomImages } from './furnitureImagery'

const roomImages = getRoomImages()
const imageFor = (roomName) => roomImages.find((room) => room.name === roomName)

export const journalCategories = [
  'All Stories',
  'Interior Design',
  'Living Room',
  'Bedroom',
  'Furniture Guide',
  'Home Inspiration',
  'Lifestyle',
]

export const journalArticles = [
  {
    slug: 'warm-welcoming-living-room',
    category: 'Living Room',
    title: 'How to Create a Warm and Welcoming Living Room',
    excerpt: 'A few thoughtful choices can turn a shared room into the heart of your home.',
    publishedAt: '2026-10-12',
    image: imageFor('Living room').src,
    imageAlt: 'Warm living room with sofas and natural materials',
    body: [
      'A welcoming living room is less about filling every corner and more about making the space easy to use. Begin with comfortable seating, a clear path through the room, and a place to set down a book or cup of tea.',
      'Layer natural textures through wood, woven details, soft upholstery, and a rug that brings the arrangement together. A warm lamp and a few personal objects add character without creating clutter.',
      'Leave some breathing room around each piece. When the layout feels balanced, the room becomes ready for quiet evenings as well as time spent together.',
    ],
  },
  {
    slug: 'furniture-for-modern-home',
    category: 'Furniture Guide',
    title: '5 Furniture Pieces Every Modern Home Needs',
    excerpt: 'Build a considered foundation with pieces that earn their place every day.',
    publishedAt: '2026-10-04',
    image: imageFor('Dining room').src,
    imageAlt: 'Dining table and chairs in a bright dining space',
    body: [
      'A useful home starts with the essentials: a comfortable place to sit, a dependable dining surface, a restful bed, practical storage, and a flexible side table. These pieces support daily routines without dictating one particular style.',
      'Look for proportions that suit the room, materials that can be cared for, and details that make each piece pleasant to use. Versatility matters too: a bench can work in a hallway, at a dining table, or at the foot of a bed.',
      'Choose slowly and let the collection grow around the way you live. A few well-considered pieces often make a room feel more complete than a quick assortment.',
    ],
  },
  {
    slug: 'choose-the-perfect-sofa',
    category: 'Living Room',
    title: 'Choosing the Perfect Sofa for Your Space',
    excerpt: 'Measure first, think about how you relax, and choose comfort that fits your room.',
    publishedAt: '2026-09-26',
    image: imageFor('Home decor').src,
    imageAlt: 'Thoughtfully styled living room with layered home decor',
    body: [
      'Start with the room rather than the sofa catalogue. Measure the wall, doorways, and the route into the space, then leave enough room for tables and easy movement around the seating.',
      'Consider who will use the sofa and how. Seat depth, cushion feel, upholstery texture, and the height of the arms all affect comfort. If possible, try the piece in person and review the care guidance for its material.',
      'A sofa should work with the other pieces in the room. Keep the palette flexible, add a throw or cushions for texture, and allow the furniture to feel settled rather than crowded.',
    ],
  },
  {
    slug: 'minimalist-interior-design',
    category: 'Interior Design',
    title: 'Minimalist Interior Design: Less Is More',
    excerpt: 'Create a calm, personal room by making space for the things that matter.',
    publishedAt: '2026-09-18',
    image: imageFor('Hallway').src,
    imageAlt: 'Bright hallway with glass doors and seating',
    body: [
      'Minimalism is not an empty-room rule. It is a way to make everyday spaces easier to understand and use. Begin by noticing what you reach for and what gets in the way.',
      'Keep the pieces that serve a purpose or hold meaning, then give them room. Repeated materials and a restrained palette can make a collection of different objects feel considered.',
      'Comfort belongs in a minimalist home. Soft light, natural surfaces, and a favorite chair can make a simple room feel warm and lived in.',
    ],
  },
  {
    slug: 'style-bedroom-for-comfort',
    category: 'Bedroom',
    title: 'How to Style Your Bedroom for Better Comfort',
    excerpt: 'Thoughtful lighting, soft layers, and practical bedside storage make a difference.',
    publishedAt: '2026-09-10',
    image: imageFor('Bedroom').src,
    imageAlt: 'Calm bedroom with a neatly made bed and warm light',
    body: [
      'A comfortable bedroom supports a gentle start and end to the day. Keep the bed as the visual anchor and make sure there is enough space to walk around it comfortably.',
      'Add layers that feel good to touch, and choose lighting that can be softened in the evening. A bedside surface gives books, glasses, and a lamp a natural home.',
      'Keep the room personal but restful. A small piece of art, a favorite textile, or a plant can bring warmth without taking away from the quiet of the space.',
    ],
  },
  {
    slug: 'small-space-smart-furniture',
    category: 'Home Inspiration',
    title: 'Small Space, Big Ideas: Smart Furniture Solutions',
    excerpt: 'Use flexible pieces and clear pathways to help a compact room do more.',
    publishedAt: '2026-09-02',
    image: imageFor('Home office').src,
    imageAlt: 'Home office with a desk, chair, and bookshelves',
    body: [
      'Small rooms benefit from furniture that is sized to the space and useful in more than one way. A compact desk, a storage ottoman, or a dining table that can double as a work surface can make a room more adaptable.',
      'Use vertical storage where it helps and keep the floor plan open. Furniture with visible legs can make a room feel lighter, while baskets and closed storage help keep everyday items in order.',
      'Before adding another piece, test the walking routes and consider how the room changes through the day. Flexibility is often more valuable than adding more furniture.',
    ],
  },
  {
    slug: 'choosing-home-colors',
    category: 'Interior Design',
    title: 'Choosing the Right Colors for Your Home',
    excerpt: 'Build a palette from the light, materials, and objects already in your space.',
    publishedAt: '2026-08-25',
    image: imageFor('Prayer room').src,
    imageAlt: 'Quiet prayer space with patterned arches and prayer rugs',
    body: [
      'Color feels different from room to room, so start by looking at the natural light and the materials that will stay. Wood tones, flooring, and large furniture pieces are useful anchors for a palette.',
      'Choose a few related shades and repeat them in small ways through textiles, artwork, and accessories. This creates a sense of connection without making every surface match.',
      'Try samples in the room at different times of day. A considered palette should feel comfortable in the morning, in softer evening light, and alongside the objects you already love.',
    ],
  },
  {
    slug: 'natural-materials-timeless-design',
    category: 'Lifestyle',
    title: 'Natural Materials and Timeless Furniture Design',
    excerpt: 'A closer look at texture, craft, and the small details that age gracefully.',
    publishedAt: '2026-08-16',
    image: imageFor('Outdoor').src,
    imageAlt: 'Garden bench beneath a leafy pergola',
    body: [
      'Natural materials bring variation into a room. Grain, weave, and small differences in finish are part of what gives a piece its character.',
      'Timeless design is often practical design: proportions that feel balanced, joinery made to last, and surfaces that can be maintained. Ask about care and construction before choosing a piece.',
      'A home can mix old and new materials comfortably. Let a few textures repeat across the room, then keep the rest simple enough for each object to be appreciated.',
    ],
  },
]
