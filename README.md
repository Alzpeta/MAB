# MAB Reservation Experiment

This project simulates reservation alternative offers using multi-armed bandit agents.

The model generates restaurants, customers, available reservation options, and then lets different agents choose which options to display. The reservation environment simulates whether the customer accepts one of the displayed offers.

## Documentation

- [Configuration](docs/config.md)
- [Customers](docs/customers.md)
- [Restaurants and Options](docs/restaurants_and_options.md)
- [Reservation](docs/reservation.md)
- [Agent Description](docs/agent_description.md)

## Main Files

- `source/config.py`: shared configuration values.
- `source/restaurants.py`: restaurant generation and calendars.
- `source/customers.py`: synthetic customer generation.
- `source/options.py`: available offer catalogue.
- `source/reservation.py`: availability checks, acceptance model, and reservation environment.
- `source/agents/`: bandit agent implementations.
- `source/experiment.py`: experiment runner logic.
- `run_scenarios.py`: scenario runner and output generation.

## Outputs

Experiment outputs are written into `outputs/`.
