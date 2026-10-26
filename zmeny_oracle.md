# Změna: Oracle policy

Oracle je teoretická horní baseline. Zná simulační model a pro aktuálního zákazníka seřadí proveditelné nabídky podle pravděpodobnosti odvozené z utility bez noise. Nezná budoucí náhodný výsledek zákaznického rozhodnutí.

## Jak Oracle hodnotí nabídky

Oracle nejdříve spočítá deterministickou utility nabídky ze všech nenáhodných vlivů. Patří sem například sleva, perk, časový posun, urgence, časová flexibilita, velikost skupiny a penalizace budoucí návštěvy.

Z této utility získá skóre:

```text
score = sigmoid(utility bez noise)
```

Noise do skóre nepřidává. Noise má v současném modelu stejné rozdělení pro všechny nabídky, proto jeho vynechání nemění jejich pořadí podle utility. Skutečné vyhodnocení zákazníka provádí až prostředí: tam se noise vygeneruje a teprve potom se rozhodne, zda zákazník nabídku přijme.

## Co Oracle ví

| Oracle ví | Proč |
|---|---|
| Které nabídky jsou právě povolené a proveditelné | Nemůže nabídnout termín mimo otevírací dobu nebo bez kapacity. |
| Parametry každé dostupné nabídky | Časový posun, výši slevy, hodnotu perku a `requires_future_visit`. |
| Charakteristiky aktuálního zákazníka | Citlivost na slevu, časovou flexibilitu, loajalitu, vztah k perkům, urgenci, frustraci z budoucí návštěvy, velikost skupiny a požadovaný čas. |
| Deterministickou část matematického modelu | Všechny váhy pro nenáhodné vlivy, včetně penalizace budoucí návštěvy. |
| Dosavadní odmítnutí původní rezervace | Je zahrnuto v záporné výchozí utility modelu. |

## Co Oracle neví

| Oracle neví | Proč |
|---|---|
| Konkrétní náhodný noise pro zákazníka a nabídku | Noise vzniká až při skutečném vyhodnocení zákaznické reakce. |
| Výsledek losu „přijme / nepřijme“ | Oracle zná pouze pravděpodobnost přijetí, ne skutečný výsledek. |
| Kterou nabídku zákazník opravdu přijme | To se zjistí až při postupném předložení nabídek. |
| Informace z budoucích zákazníků | Nesmí se opírat o budoucí interakce ani o výsledky aktuálního kola. |
| Historii odměn pro učení | Oracle se neučí; její výběr se po `update()` nemění. |

## Kde Oracle končí

1. Zákazník požádá o rezervaci a původní termín nelze splnit.
2. Systém vyfiltruje pouze proveditelné alternativy.
3. Oracle dostane zákazníka a dostupné nabídky.
4. Bez náhody spočítá skóre každé nabídky z utility bez noise.
5. Seřadí nabídky od nejlepší po nejhorší a vrátí prvních `k`.
6. Oracle zde končí.
7. Až poté prostředí vygeneruje noise a simuluje skutečné reakce zákazníka.
