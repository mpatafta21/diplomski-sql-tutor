/**
 * ErrorBoundary (Faza 4.1c) — hvata RENDER greške (ne mrežne; te idu kroz
 * TanStack Query error → <ErrorState>). Fallback je oporavljiv (reset + retry).
 *
 * Class komponenta bez TS parameter-properties (TS6 erasableSyntaxOnly — invarijanta #2):
 * sva polja eksplicitno deklarirana.
 */
import { Component, type ErrorInfo, type ReactNode } from "react"
import { ErrorState } from "@/components/state/ErrorState"

interface ErrorBoundaryProps {
  children: ReactNode
  /** Opcionalni custom fallback; default je <ErrorState> s resetom. */
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  error: Error | null
}

export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Dev dijagnostika; produkcijski telemetry nije u scopeu teze.
    console.error("ErrorBoundary uhvatio render grešku:", error, info)
  }

  handleReset = (): void => {
    this.setState({ error: null })
  }

  render(): ReactNode {
    if (this.state.error !== null) {
      if (this.props.fallback !== undefined) {
        return this.props.fallback
      }
      return (
        <div className="flex min-h-svh items-center justify-center p-8">
          <ErrorState
            title="Greška u prikazu"
            message="Dio sučelja se srušio. Resetiraj prikaz ili osvježi stranicu."
            onRetry={this.handleReset}
            className="max-w-md"
          />
        </div>
      )
    }
    return this.props.children
  }
}
