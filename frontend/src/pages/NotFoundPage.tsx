import { NotFoundState } from '../components/feedback/NotFoundState'

export function NotFoundPage() {
  return (
    <NotFoundState
      title="Page not found"
      message="This page does not exist. Use the navigation above to go to one of the six sections."
    />
  )
}
