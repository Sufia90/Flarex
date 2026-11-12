interface NotFoundStateProps {
  title?: string
  message?: string
}

export function NotFoundState({ title = 'Not found', message }: NotFoundStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
      <p className="text-sm font-semibold text-white">{title}</p>
      {message ? <p className="max-w-md text-sm text-white/80">{message}</p> : null}
    </div>
  )
}
