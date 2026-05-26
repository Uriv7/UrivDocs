/**
 * SEOHead — dynamically updates document title and meta tags per page/state.
 * In a full SSR setup you'd use react-helmet-async; for SPA this updates the DOM directly.
 */
import { useEffect } from 'react'

export default function SEOHead({ title, description }) {
  useEffect(() => {
    if (title) document.title = title
    const metaDesc = document.querySelector('meta[name="description"]')
    if (metaDesc && description) metaDesc.setAttribute('content', description)
    const ogTitle = document.querySelector('meta[property="og:title"]')
    if (ogTitle && title) ogTitle.setAttribute('content', title)
    const ogDesc = document.querySelector('meta[property="og:description"]')
    if (ogDesc && description) ogDesc.setAttribute('content', description)
  }, [title, description])
  return null
}
