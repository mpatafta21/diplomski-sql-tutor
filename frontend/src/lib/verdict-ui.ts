/**
 * Vizualni meta po verdictu (Faza 4.4a) — ikona + oznaka + tokeni.
 *
 * 🔴 DEKLARATIVNI MIRROR `VERDICT_UI` iz components/task/FeedbackPanel.tsx.
 * Task screen se u 4.4a NE dira (plan §OPSEG), pa se mapa ovdje zrcali umjesto
 * da se FeedbackPanel prežičava. SEMANTIČKA istina (koji verdict, koja poruka)
 * ostaje JEDAN izvor — lib/feedback.ts (deriveVerdict/feedbackText) — pa
 * povijest i task screen govore isto o istom pokušaju (NALAZ #13: boja NIJE
 * jedini kanal → ikona + tekstualna oznaka uvijek idu zajedno).
 */
import {
  CheckCircle2,
  CircleAlert,
  TriangleAlert,
  XCircle,
  type LucideIcon,
} from "lucide-react"
import type { Verdict } from "@/lib/feedback"

export interface VerdictMeta {
  label: string
  icon: LucideIcon
  /** boja teksta/ikone (pojačanje, ne jedini kanal) */
  chip: string
  /** meki background za suptilni accent retka */
  soft: string
  /** border u boji verdicta */
  border: string
}

export const VERDICT_META: Record<Verdict, VerdictMeta> = {
  correct: {
    label: "Točno",
    icon: CheckCircle2,
    chip: "text-correct",
    soft: "bg-correct-soft",
    border: "border-correct/40",
  },
  partial: {
    label: "Djelomično",
    icon: TriangleAlert,
    chip: "text-partial",
    soft: "bg-partial-soft",
    border: "border-partial/40",
  },
  incorrect: {
    label: "Netočno",
    icon: XCircle,
    chip: "text-incorrect",
    soft: "bg-incorrect-soft",
    border: "border-incorrect/40",
  },
  unknown: {
    label: "Bez ocjene",
    icon: CircleAlert,
    chip: "text-muted-foreground",
    soft: "bg-muted",
    border: "border-border",
  },
}
