# Vystupy a konfigurace experimentu

Interni souhrn aktualniho stavu kodu.

## Spousteci skripty

- `mab.py` spousti zakladni experiment pro vsechny restaurace a vypisuje vysledky do konzole.
- `run_scenarios.py` spousti experiment po scenarich a uklada vystupy do `outputs/mab_run_<timestamp>/`.

## Scenare

Aktualne se vyhodnocuji tyto scenare:

- `all` - vsechny restaurace
- `budget` - pouze budget restaurace
- `midrange` - pouze midrange restaurace
- `premium` - pouze premium restaurace

## Porovnavani agenti

Aktualne registrovani agenti:

- `Random`
- `EpsilonGreedy`
- `DecayEpsilon`
- `UCB1`
- `Thompson`
- `Softmax`

## Vracene metriky vysledku

Pro kazdy scenar, agenta a hodnotu `top_k` se vraci:

- `scenario` - nazev scenare
- `restaurant_tiers` - pouzite typy restauraci
- `agent` - nazev strategie
- `top_k` - pocet zobrazenych alternativ
- `mean_reward` - prumerna odmena / acceptance rate pres behy
- `std_reward` - smerodatna odchylka odmen
- `ci95` - 95% interval spolehlivosti
- `min_reward` - nejhorsi beh
- `max_reward` - nejlepsi beh
- `improvement_vs_random_pct` - zlepseni proti `Random` v procentech
- `rank` - poradi strategie v ramci daneho `top_k`

## Vystupy pro jednotlive scenare

Pro kazdy scenar se uklada adresar:

`outputs/mab_run_<timestamp>/<scenario>/`

Obsah:

- `results.csv` - tabulka vysledku podle agenta a `top_k`
- `results.html` - HTML verze `results.csv`
- `options_detail.csv` - statistiky jednotlivych nabidek podle agenta a `top_k`
- `options_detail.html` - HTML verze detailu nabidek
- `options_by_category.csv` - agregace podle kategorie nabidky
- `options_by_category.html` - HTML verze agregace podle kategorie
- `restaurants.csv` - restaurace pouzite ve scenari
- `customer_sample.csv` - prvnich 200 vygenerovanych zakazniku
- `customer_summary.csv` - statisticky souhrn zakazniku

## Celkove vystupy

V hlavnim adresari behu se uklada:

- `all_results.csv` - spojene vysledky vsech scenaru
- `all_results.html` - HTML verze celkovych vysledku
- `all_options_detail.csv` - spojene detaily nabidek ze vsech scenaru
- `all_options_detail.html` - HTML verze detailu vsech nabidek
- `config_used.json` - konfigurace pouzita pro dany beh

## Statistiky nabidek

U jednotlivych nabidek se sleduje:

- `option_name` - nazev nabidky
- `option_category` - kategorie nabidky
- `shown_count` - kolikrat byla nabidka zobrazena
- `accepted_count` - kolikrat byla nabidka prijata
- `acceptance_rate` - `accepted_count / shown_count`
- `scenario`
- `restaurant_tiers`
- `agent`
- `top_k`

Kategorie nabidek:

- `time_only`
- `discount_only`
- `perk_only`
- `time_discount`
- `time_perk`
- `time_discount_perk`
- `other`

## Generovane grafy pro scenar

Pro kazdy scenar se generuji tyto PNG grafy:

- `<scenario>_strategy_comparison.png` - porovnani strategii podle `mean_reward` pres hodnoty `top_k`
- `<scenario>_mean_reward_heatmap.png` - heatmapa `mean_reward` podle agenta a `top_k`
- `<scenario>_improvement_heatmap.png` - heatmapa zlepseni proti `Random`
- `<scenario>_rank_heatmap.png` - heatmapa poradi strategii
- `<scenario>_customer_sample.png` - rozdeleni hodin, velikosti skupiny, atributu zakazniku a tieru restauraci
- `<scenario>_option_categories.png` - acceptance rate a pocet zobrazeni podle kategorie nabidky
- `<scenario>_top_options.png` - top nabidky podle poctu prijeti a acceptance rate
- `<scenario>_option_category_agent_heatmap.png` - acceptance rate kategorii nabidek podle agenta

## Celkove grafy

V hlavnim adresari behu se generuji:

- `overall_best_results.png` - nejlepsi vysledek pro kazdy scenar a `top_k`
- `overall_best_reward_heatmap.png` - nejlepsi `mean_reward` podle scenare a agenta

## Konfigurovatelne casti

Hlavni konfigurace je v `mab.CONFIG`:

- velikost experimentu: `N_CUSTOMERS`, `N_RUNS`, `SEED`, `N_SHOWN_OPTIONS_LIST`
- restaurace a kalendar: `N_RESTAURANTS`, `N_DAYS`, `OPEN_HOUR`, `CLOSE_HOUR`, `SLOTS_PER_HOUR`
- obsazenost: `EVENING_PEAK_HOURS`, `EVENING_OCCUPANCY_BOOST`, `WEEKEND_DAYS`, `WEEKEND_OCCUPANCY_BOOST`, `TIER_BASE_OCCUPANCY`
- bandit inicializace: `INITIAL_ACCEPTANCE_ESTIMATE`
- distribuce zakazniku: mean/std pro discount affinity, time flexibility, loyalty, perk affinity a urgency
- acceptance model: `BASE_UTILITY`, vahy discount/time/perk/loyalty/urgency, penalty za vecer a velkou skupinu, `NOISE_STD`
- normalizace: `TIME_SHIFT_NORMALIZER`
- orez acceptance probability: `MIN_ACCEPTANCE_PROBABILITY`, `MAX_ACCEPTANCE_PROBABILITY`

Dalsi konfigurovatelne casti:

- `ALL_OPTIONS` - katalog nabidek, jejich casovy posun, sleva a hodnota benefitu
- `RESTAURANT_CONFIGS` - restaurace, tier a povolene nabidky pro kazdou restauraci
- `AGENTS` - seznam strategii, ktere se maji porovnavat
- `SCENARIOS` v `run_scenarios.py` - rozdeleni behu podle tieru restauraci

## Poznamky k modelu

- Agenti jsou aktualne nekontextovi; nevidi latentni preference zakaznika.
- Odmena je binarni: `1` za prijatou nabidku, `0` za neprijatou nebo zadnou dostupnou nabidku.
- Zakaznik prochazi zobrazenymi nabidkami v poradi a prijme prvni, ktera projde pravdepodobnostnim acceptance modelem.
