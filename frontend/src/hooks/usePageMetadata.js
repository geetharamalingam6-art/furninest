import { useEffect } from 'react'

export default function usePageMetadata(title, description) {
  useEffect(() => {
    const previousTitle = document.title
    let descriptionTag = document.querySelector('meta[name="description"]')
    const createdDescriptionTag = !descriptionTag

    if (!descriptionTag) {
      descriptionTag = document.createElement('meta')
      descriptionTag.name = 'description'
      document.head.append(descriptionTag)
    }

    const previousDescription = descriptionTag.content
    document.title = title
    descriptionTag.content = description

    return () => {
      document.title = previousTitle
      if (createdDescriptionTag) descriptionTag.remove()
      else descriptionTag.content = previousDescription
    }
  }, [title, description])
}
