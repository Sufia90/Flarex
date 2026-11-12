import { EmptyState } from '../components/feedback/EmptyState'

export function ResearchAssistantPage() {
  return (
    <section>
      <h2 className="text-xl font-bold">Research Assistant</h2>
      <EmptyState
        title="Research Assistant is not available yet"
        message="The assistant answers only from retrieved evidence, and no AI provider is configured. The question form and evidence view will be added in Module 09."
      />
    </section>
  )
}
