# Změna: Fixed-order policy

Byla přidána `FixedOrderPolicy` jako praktická, deterministická baseline pro porovnání s učenými strategiemi.

- `source/agents/fixed_order.py` obsahuje novou politiku.
- Z dostupných nabídek vždy vybere první `min(k, počet_dostupných)` ve stávajícím pořadí.
- Neudržuje žádné hodnoty ani počty a metoda `update()` nic nemění, takže se neučí.
- Konstruktor přijímá `n_arms` jen kvůli společnému rozhraní experimentu; parametr se nepoužívá.
- `source/agents/__init__.py` ji registruje pod názvem `FixedOrder`, proto se automaticky zahrne do experimentů a jejich metrik.
- `tests/test_agents.py` ověřuje pořadí výběru, omezení počtem `k` i neměnnost po aktualizaci.

Tato baseline tedy ukazuje výsledek pevně daného pořadí povolených a dostupných nabídek bez náhody a bez adaptace na předchozí zákazníky.
