# AG Reachy Mini Vision & Tracking

## Initial Setup

C:\Users\steyer-mika\.local\bin\uv.exe

- Install Python 3.12
- Verify with `python --version`
- Create Virtual Environment `python -m venv .venv`
- Activate VE `.\.venv\Scripts\activate`
- Upgrade PIP `python -m pip install --upgrade pip`
- Install Reachy Mini + Simulation `pip install "reachy-mini[mujoco]"`

- Install Packages `pip install -r requirements.txt`

## Start Program

- `reachy-mini-daemon --sim`
- `python hello_world.py`

## References

- MediaPipe `https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python?hl=en`
- Reachy Mini `https://huggingface.co/docs/reachy_mini/platforms/simulation/get_started`
- Examples `https://github.com/pollen-robotics/reachy_mini/tree/main/examples`

## Improvements and Features

- [ ] Add Person Tracking
- [ ] Add Robot Controller
- [ ] Add Gesture Controller
- [ ] Add Multi Person Handing
- [ ] Add UI to Control Robot
- [x] Add Logger
- [x] Add fixed fps
- [ ] Improve Memory Management & Performance (Reuse Frame Buffer)
- [ ] Add Renderer to outsource screen drawing
- [ ] Add more Comments to Explain Concepts and Logic
- [ ] Improve Finger Counter
