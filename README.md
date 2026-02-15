# AG Reachy Mini Vision & Tracking

## Initial Setup

- Install Python 3.12
- Verify with `python --version`
- Create Virtual Environment `python -m venv .venv`
- Activate VE `.\.venv\Scripts\activate`
- Upgrade PIP `python -m pip install --upgrade pip`
- Install Reachy Mini + Simulation `pip install "reachy-mini[mujoco]"`
- Install Packages `pip install -r requirements.txt`

## Run Program

- `reachy-mini-daemon --sim`
- `python ag_reachy_mini_vision_tracking/main.py`

## References

- MediaPipe `https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python?hl=en`
- Reachy Mini `https://huggingface.co/docs/reachy_mini/platforms/simulation/get_started`
- Examples `https://github.com/pollen-robotics/reachy_mini/tree/main/examples` && `https://github.com/Seeed-Projects/reachy-mini-starter`
- App CLI `https://huggingface.co/blog/pollen-robotics/make-and-publish-your-reachy-mini-apps`

## Metadata

---

title: Ag Reachy Mini Vision Tracking
emoji: 👋
colorFrom: red
colorTo: blue
sdk: static
pinned: false
short_description: Write your description here
tags:

- reachy_mini
- reachy_mini_python_app

---
