/**
 * BADGE_ICON (izvučeno u lib 4.3c) — JEDNA mapa lucide ikona bedževa za sve
 * potrošače (dashboard BadgeStrip, task FeedbackPanel, 4.4 galerija).
 * `icon` u katalogu je lucide ime (seed: compass/star/link/ghost/fire);
 * nepoznato ime → Award fallback (nikad emoji — MASTER.md §7).
 */
import {
  Award,
  Compass,
  Flame,
  Ghost,
  Link,
  Star,
  type LucideIcon,
} from "lucide-react"

export const BADGE_ICON: Record<string, LucideIcon> = {
  compass: Compass,
  star: Star,
  link: Link,
  ghost: Ghost,
  fire: Flame,
}

export const BADGE_ICON_FALLBACK: LucideIcon = Award
