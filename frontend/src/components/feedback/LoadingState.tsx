interface LoadingStateProps {
  message?: string
}

export function LoadingState({ message = 'Loading...' }: LoadingStateProps) {
  return (
    <div role="status" className="flex flex-col items-center justify-center gap-3 py-10 text-center">
      <span
        className="h-8 w-8 animate-spin rounded-full border-2 border-[#28D7F2] border-t-transparent"
        aria-hidden="true"
      />
      <p className="text-sm text-white/80">{message}</p>
    </div>
  )
}
