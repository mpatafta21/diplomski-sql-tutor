/**
 * Most openapi-fetch → TanStack Query (Faza 4.2).
 *
 * openapi-fetch vraća {data, error, response} i NE baca — TanStack Query očekuje
 * queryFn koji baca na neuspjeh. `unwrap` to premošćuje NA RUNTIME RAZINI
 * (response.ok / data === undefined), NE kroz tipiziranu error granu: za čiste
 * GET rute bez 4xx u OpenAPI spec-u error je tipiziran kao `never`, a stvarni
 * 401/5xx svejedno stižu (401 usput hvata i auth middleware u client.ts).
 */

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = "ApiError"
    this.status = status
  }
}

interface FetchResult<T> {
  data?: T
  response: Response
}

/** Baci ApiError ako odgovor nije OK ili nema tijela; inače vrati podatke. */
export function unwrap<T>({ data, response }: FetchResult<T>): T {
  if (!response.ok || data === undefined) {
    throw new ApiError(response.status, `HTTP ${response.status}`)
  }
  return data
}
