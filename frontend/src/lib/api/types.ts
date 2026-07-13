/**
 * Zgodni aliasi za auth tipove — SVI IZVEDENI iz generiranog schema.d.ts (contract-safe).
 * NE definirati ručne interface-e za ove oblike (contract-mismatch rizik koji gasimo).
 */
import type { components } from "./schema"

export type MeResponse = components["schemas"]["MeResponse"]
export type TokenResponse = components["schemas"]["TokenResponse"]
export type RegisterRequest = components["schemas"]["RegisterRequest"]
export type LoginBody = components["schemas"]["Body_post_login_login_post"]

// Data hookovi (Faza 4.2) — read površina za Dashboard/Module overview.
export type ProfileResponse = components["schemas"]["ProfileResponse"]
export type MasteryItem = components["schemas"]["MasteryItem"]
export type ModuleNode = components["schemas"]["ModuleNode"]
export type ConceptNode = components["schemas"]["ConceptNode"]
export type NextTaskResponse = components["schemas"]["NextTaskResponse"]
export type TaskDetailResponse = components["schemas"]["TaskDetailResponse"]
export type BadgeCatalogItem = components["schemas"]["BadgeCatalogItem"]
export type RunResponse = components["schemas"]["RunResponse"]
export type AttemptResponse = components["schemas"]["AttemptResponse"]
