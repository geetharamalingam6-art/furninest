import livingRoomImage from '../assets/room-living.jpg'
import diningRoomImage from '../assets/room-dining.jpg'
import bedroomImage from '../assets/room-bedroom.jpg'
import prayerRoomImage from '../assets/room-prayer.jpg'
import homeOfficeImage from '../assets/room-office.jpg'
import hallwayImage from '../assets/room-hallway.jpg'
import outdoorImage from '../assets/room-outdoor.jpg'
import homeDecorImage from '../assets/room-decor.jpg'

const roomImages = [
  {
    name: 'Living room',
    caption: 'A quieter place to gather.',
    keywords: ['living room', 'living-room', 'lounge', 'sofa', 'couch'],
    src: livingRoomImage,
    alt: 'Warm living room with sofas and natural materials',
  },
  {
    name: 'Dining room',
    caption: 'Gather around something lasting.',
    keywords: ['dining', 'table', 'dining chair'],
    src: diningRoomImage,
    alt: 'Dining table and chairs in a bright dining space',
  },
  {
    name: 'Bedroom',
    caption: 'Made for a slower morning.',
    keywords: ['bedroom', 'bed', 'nightstand', 'wardrobe'],
    src: bedroomImage,
    alt: 'Calm bedroom with a neatly made bed and warm light',
  },
  {
    name: 'Prayer room',
    caption: 'A serene place for prayer and reflection.',
    keywords: ['prayer', 'meditation', 'worship'],
    src: prayerRoomImage,
    alt: 'Peaceful prayer hall with patterned arches and prayer rugs',
  },
  {
    name: 'Home office',
    caption: 'Settle into your best ideas.',
    keywords: ['home office', 'home-office', 'office', 'desk', 'study', 'work'],
    src: homeOfficeImage,
    alt: 'Home office with a desk, chair, and bookshelves',
  },
  {
    name: 'Hallway',
    caption: 'A warm welcome, from the threshold.',
    keywords: ['hallway', 'hall', 'entryway', 'corridor'],
    src: hallwayImage,
    alt: 'Bright office hallway with glass doors and seating',
  },
  {
    name: 'Outdoor',
    caption: 'Bring comfort into the open air.',
    keywords: ['outdoor', 'garden', 'patio', 'terrace'],
    src: outdoorImage,
    alt: 'Garden bench beneath a leafy pergola',
  },
  {
    name: 'Home decor',
    caption: 'Finish the room with meaning.',
    keywords: ['home decor', 'home-decor', 'decor', 'decoration', 'accessories'],
    src: homeDecorImage,
    alt: 'Thoughtfully styled living room with layered home decor',
  },
]

const roomImagesByCategory = {
  'living-room': roomImages[0],
  'dining-room': roomImages[1],
  bedroom: roomImages[2],
  'prayer-room': roomImages[3],
  'home-office': roomImages[4],
  hallway: roomImages[5],
  outdoor: roomImages[6],
  'home-decor': roomImages[7],
}

const productPhotoAssets = import.meta.glob('../assets/products/*.{jpg,jpeg,png,webp}', {
  eager: true,
  import: 'default',
})
const productPhotosBySlug = Object.fromEntries(
  Object.entries(productPhotoAssets).map(([path, src]) => [
    path.split('/').pop().replace(/\.(jpe?g|png|webp)$/i, ''),
    src,
  ]),
)

function findRoom(search) {
  return roomImages.find(
    (room) => search.includes(room.name.toLowerCase()) || room.keywords.some((keyword) => search.includes(keyword)),
  )
}

function findCategoryRoom(category = {}) {
  const slug = String(category.slug || '').toLowerCase()
  return roomImagesByCategory[slug] || findRoom(String(category.name || '').toLowerCase())
}

export function getFurnitureImage(product = {}) {
  return findCategoryRoom(product.category) || findRoom(String(product.name || '').toLowerCase()) || roomImages[0]
}

export function isDemoProductImage(image = '') {
  return /(?:^|\/)products\/demo\//i.test(image)
}

export function getProductImage(product = {}) {
  const furnitureImage = getFurnitureImage(product)
  const productPhoto = productPhotosBySlug[product.slug]
  const uploadedImage = product.images?.find((image) => image.image && !isDemoProductImage(image.image))
  return {
    src: productPhoto || uploadedImage?.image || furnitureImage.src,
    alt: productPhoto || uploadedImage
      ? `${product.name} in the ${product.category?.name || furnitureImage.name}`
      : furnitureImage.alt,
    caption: furnitureImage.caption,
  }
}

export function getCategoryImage(category = {}, index = 0) {
  const room = findCategoryRoom(category)
  if (!room && category.image) {
    return {
      src: category.image,
      alt: `${category.name} furniture collection`,
    }
  }
  const selectedRoom = room || roomImages[index % roomImages.length]
  return {
    ...selectedRoom,
    alt: selectedRoom.alt || `${category.name} furniture collection`,
  }
}

export function getRoomImages() {
  return roomImages
}
