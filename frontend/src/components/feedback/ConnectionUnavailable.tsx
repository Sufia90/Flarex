interface ConnectionUnavailableProps {
  onRetry?: () => void
}

export function ConnectionUnavailable({ onRetry }: ConnectionUnavailableProps) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center gap-3 py-10 text-center">
      <p className="text-sm font-semibold text-white">Backend unavailable</p>
      <p className="max-w-md text-sm text-white/80">
        The backend could not be reached. Check that it is running and reachable, then try again.
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-md bg-[#28D7F2] px-4 py-2 text-sm font-semibold text-[#07111F] hover:opacity-90"
        >
          Retry
        </button>
      ) : null}
    </div>
  )
}
