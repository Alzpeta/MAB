# Změna: budoucí návštěva bez náhradního termínu

Nabídky bez časového posunu nově znamenají, že zákazník nedostane konkrétní náhradní sezení a musí restauraci navštívit jindy.

- `source/options.py` přidává ke každé nabídce `requires_future_visit`: `1` pro `time_shift = 0`, jinak `0`.
- `source/customers.py` přidává zákaznickou hodnotu `future_visit_frustration`. Vychází z urgence a nízké časové flexibility:
  `0.5 × urgency + 0.5 × (1 − time_flexibility)`.
- `source/reservation.py` tuto frustraci odečítá z utility pouze u nabídek s `requires_future_visit = 1`.
- `source/config.py` obsahuje váhu penalizace `FUTURE_VISIT_FRUSTRATION_WEIGHT`, výchozí hodnota je `1.0`.
- `run_scenarios.py` novou zákaznickou hodnotu ukládá do exportů a zahrnuje ji do grafu atributů.

Díky tomu nejsou čisté slevy a perky bez časového posunu vyhodnoceny stejně jako okamžitě dostupné sezení. Vysoce urgentní a časově málo flexibilní zákazník je přijme s nižší pravděpodobností.
