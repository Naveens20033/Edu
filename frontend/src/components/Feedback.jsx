export function LoadingState({ children = 'Loading…' }) {
  return <div className="loading-state" role="status"><span className="loading-spinner" aria-hidden="true" />{children}</div>
}

export function ErrorState({ message, onRetry, retrying = false }) {
  return <div className="notice error-notice" role="alert"><span>{message}</span>{onRetry && <button className="retry-button" disabled={retrying} onClick={onRetry} type="button">{retrying ? 'Retrying…' : 'Try again'}</button>}</div>
}

export function EmptyState({ title, detail }) {
  return <div className="empty-state"><span className="empty-icon" aria-hidden="true">—</span><strong>{title}</strong>{detail && <span>{detail}</span>}</div>
}
