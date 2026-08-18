# Změna: abandonment efekt a poziční metriky

Model nově simuluje odchod zákazníka po odmítnutí nabídky. Výchozí hodnota `ABANDONMENT_PROBABILITY` je `0.20`.

## Průběh rozhodování

1. Zákazník uvidí nabídku a může ji přijmout nebo odmítnout.
2. Po odmítnutí — pokud existuje další nabídka — s pravděpodobností `q` odejde.
3. Pokud neodejde, uvidí následující nabídku.
4. Nabídky za okamžikem odchodu zákazník nevidí a neovlivňují učení agentů ani statistiky.

`ReservationEnvironment` vrací také:

- `evaluated_arms`: nabídky, které zákazník skutečně viděl;
- `abandoned`: zda zákazník odešel před vyčerpáním vybraných nabídek.

## Poziční metriky

Pro každou strategii, hodnotu `k` a pozici nabídky se ukládají:

| Metrika | Význam |
|---|---|
| `position_shown_count` | Kolikrát zákazník skutečně viděl nabídku na dané pozici. |
| `position_acceptance_rate` | Podíl přijetí ze skutečně zobrazených nabídek na dané pozici. |
| `abandoned_after_position_count` | Kolikrát zákazník po odmítnutí nabídky na dané pozici odešel. |

Navíc se ukládá `position_accepted_count`, protože je potřeba pro správný výpočet a agregaci acceptance rate.

## Výstupy

Každý scénář obsahuje soubor `position_metrics.csv` a jeho HTML verzi `position_metrics.html`. V kořeni celého běhu jsou stejné agregované údaje v souborech `all_position_metrics.csv` a `all_position_metrics.html`.
