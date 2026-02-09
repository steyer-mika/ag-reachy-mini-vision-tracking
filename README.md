# AG Reachy Mini Vision & Tracking

## Initial Setup

- Install Python 3.13.12
- Verify with `python --version`
- Create Virtual Environment `python -m venv virtualenv`
- Activate VE `.\virtualenv\Scripts\activate`
- Upgrade PIP `python -m pip install --upgrade pip`
- Install Reachy Mini + Simulation `pip install "reachy-mini[mujoco]"`

## Start Program

- `reachy-mini-daemon --sim`
- `python hello_world.py`
