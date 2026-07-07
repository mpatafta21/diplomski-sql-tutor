/**
 * Zgodni aliasi za auth tipove — SVI IZVEDENI iz generiranog schema.d.ts (contract-safe).
 * NE definirati ručne interface-e za ove oblike (contract-mismatch rizik koji gasimo).
 */
import type { components } from "./schema"

export type MeResponse = components["schemas"]["MeResponse"]
export type TokenResponse = components["schemas"]["TokenResponse"]
export type RegisterRequest = components["schemas"]["RegisterRequest"]
export type LoginBody = components["schemas"]["Body_post_login_login_post"]
