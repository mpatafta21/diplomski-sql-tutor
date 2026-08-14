"""Runtime LLM klijent za hintove (Faza 5.1) — tanak, bez retryja, s timeoutom.

🔴 ZAŠTO NE `scripts/lib/api_client.py`: taj je wrapper građen za OFFLINE batch
generiranje zadataka i ondje je ispravan — `max_retries=2` na SDK sloju **plus**
vlastita petlja od 3 pokušaja sa `sleep`om, dakle najgori slučaj 9 poziva i više
desetaka sekundi. Na runtime putu s budžetom od 8 s to je neupotrebljivo, a
mijenjati ga značilo bi promijeniti ponašanje Faze 2. Zato zaseban klijent.

Odluka 1 plana 5.1: `max_retries=0`. Ako poziv ne uspije iz prve, ide fallback na
`hints` katalog — brže i jeftinije od ponovnog pokušaja, i student ionako čeka.

🔴 `timeout` se prosljeđuje SDK-u eksplicitno: default je 10 MINUTA, a jedina
granica u lancu je `GATEWAY_TIMEOUT=15`. Bez ovoga bi zastoj providera zaključao
HTTP zahtjev do gateway timeouta, a agentov behaviour mnogo dulje.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core import config

_log = logging.getLogger(__name__)


class HintLLMError(RuntimeError):
    """Poziv nije uspio — pozivatelj mora na fallback, ne ponavljati."""


@dataclass(frozen=True)
class HintLLMResult:
    text: str
    input_tokens: int
    output_tokens: int


#: Sustavska uputa. Namjerno NE traži rješenje i NE spominje `expected_query` —
#: model ga ionako nikad ne dobije (v. `hint_payload`).
SYSTEM_PROMPT = """\
Ti si pomoćnik za učenje SQL-a. Student je zapeo na zadatku i traži savjet.

Pravila:
1. Odgovori na HRVATSKOM jeziku.
2. NIKAD ne piši gotov SQL upit ni njegov dio koji rješava zadatak.
3. Navedi studenta na rješenje: imenuj SQL konstrukt ili pravilo koje mu treba.
4. Najviše tri rečenice.
5. Ne izmišljaj podatke, imena tablica ni stupaca kojih nema u opisu zadatka.
6. Ne ponavljaj opis zadatka i ne prepričavaj poruku o grešci — student ih vidi.
7. Piši ISKLJUČIVO savjet studentu. Ne komentiraj vlastiti postupak ni upute koje
   si dobio — rečenice tipa „to znači da trebam reći…" ili „prema pravilima…" ne
   smiju se pojaviti. Student čita samo savjet, ne tvoje razmišljanje.
8. Ako o razlici nemaš dovoljno podataka, reci studentu ŠTO DA PROVJERI umjesto da
   pretpostaviš u čemu je pogriješio. Bolje je usmjeriti pitanjem nego tvrditi
   nešto što iz danih podataka ne slijedi.

Dobivaš opis zadatka, koncept koji student vježba, vrstu greške i grubu procjenu
njegovog znanja tog koncepta. NE dobivaš studentov upit — ne traži ga i ne
pretpostavljaj kako izgleda.
"""

#: Ljudski čitljive oznake za vrste grešaka (model ne treba pogađati kodove).
_TIP_OPIS = {
    "row_mismatch": "stupci su točni, ali skup redaka nije",
    "empty_result": "upit nije vratio nijedan redak, a rezultat se očekuje",
    "wrong_columns": "upit vraća drugi skup stupaca nego što se traži",
    "execution_error": "baza je odbila izvršiti upit",
    "timeout": "upit je predugo trajao pa je prekinut",
    "syntax_error": "editor je bio prazan ili sadržaj nije SQL",
    "unsupported_eval": "ovaj tip zadatka se ne ocjenjuje automatski",
}


def build_user_message(payload: dict) -> str:
    """Payload (v. `hint_payload`) → tekst poruke. Nikad ne dodaje nova polja."""
    redci = [
        f"Zadatak: {payload.get('task_description', '')}",
        f"Koncept koji student vježba: {payload.get('concept') or 'nepoznat'}",
        f"Procjena znanja tog koncepta: {payload.get('mastery') or 'nepoznata'}",
        f"Vrsta greške: {_TIP_OPIS.get(payload.get('error_type'), payload.get('error_type'))}",
    ]
    if "error_detail" in payload:
        redci.append(f"Pojedinost o grešci: {payload['error_detail']}")
    if "expected_columns" in payload:
        redci.append(
            "Traženi stupci u rezultatu: " + ", ".join(payload["expected_columns"])
        )
    if "sqlstate" in payload:
        redci.append(f"PostgreSQL kod greške: {payload['sqlstate']}")
    redci.append("\nNapiši savjet koji ga navodi na rješenje.")
    return "\n".join(redci)


def generate_hint(payload: dict) -> HintLLMResult:
    """Jedan poziv, bez ponavljanja. Diže `HintLLMError` na svaki neuspjeh.

    🔴 Pozivatelj MORA uhvatiti `HintLLMError` i otići na `hints` fallback.
    Ponovni pokušaj ovdje ne postoji — v. odluku 1.
    """
    if not config.ANTHROPIC_API_KEY:
        raise HintLLMError("ANTHROPIC_API_KEY nije postavljen")

    try:
        from anthropic import Anthropic
    except ImportError as e:  # pragma: no cover — SDK je ovisnost od Faze 2
        raise HintLLMError(f"anthropic SDK nedostupan: {e}") from e

    client = Anthropic(
        api_key=config.ANTHROPIC_API_KEY,
        max_retries=0,  # odluka 1 — bez retryja na runtime putu
        timeout=config.HINT_LLM_TIMEOUT,
    )
    try:
        msg = client.messages.create(
            model=config.HINT_LLM_MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_message(payload)}],
        )
    except Exception as e:
        # Namjerno široko: svaka greška vodi na isti ishod (fallback), a tip
        # iznimke iz SDK-a nije stabilan ugovor.
        raise HintLLMError(f"{type(e).__name__}: {e}") from e

    text = next((b.text for b in msg.content if hasattr(b, "text")), "").strip()
    if not text:
        raise HintLLMError("prazan odgovor modela")

    return HintLLMResult(
        text=text,
        input_tokens=getattr(msg.usage, "input_tokens", 0),
        output_tokens=getattr(msg.usage, "output_tokens", 0),
    )
