# Změna: 95% intervaly spolehlivosti

Výsledky simulace nově obsahují 95% intervaly spolehlivosti. Počítají se přes samostatné simulační běhy, nikoli přes jednotlivé zákazníky v jednom běhu.

## Interval pro mean reward

Pro každou kombinaci scénáře, strategie a `top_k` se ukládá:

- `mean_reward`: průměrná reward přes všechny běhy;
- `ci95`: poloviční šířka 95% intervalu;
- `ci95_lower`: dolní mez intervalu;
- `ci95_upper`: horní mez intervalu.

Interval používá vzorkovou směrodatnou odchylku reward mezi běhy a 95% normální aproximaci:

```text
mean_reward ± 1.96 × standard_deviation / sqrt(number_of_runs)
```

## Párované srovnání strategií

Pro každou strategii se porovnávají reward ze stejného čísla běhu. Díky tomu se rozdíl počítá nad stejnými simulačními podmínkami.

Ukládají se absolutní rozdíly reward vůči:

- Random: `vs_random_mean_difference`, `vs_random_ci95_lower`, `vs_random_ci95_upper`;
- FixedOrder: `vs_fixed_order_mean_difference`, `vs_fixed_order_ci95_lower`, `vs_fixed_order_ci95_upper`.

Pokud interval rozdílu obsahuje nulu, simulace neposkytuje jasný důkaz, že se strategie od dané baseline liší.

## Grafy

Graf výsledků podle `top_k` nyní kolem každé křivky ukazuje poloprůhledný pás mezi `ci95_lower` a `ci95_upper`.
