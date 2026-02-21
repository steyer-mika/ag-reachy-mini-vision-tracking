import numpy as np


class PIDController:
    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        output_limit: float = 1.0,
        integral_limit: float = 0.5,
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit
        self.integral_limit = integral_limit
        self._integral = 0.0
        self._prev_error = 0.0

    def update(self, error: float, dt: float) -> float:
        if dt <= 0:
            dt = 1e-3
        self._integral += error * dt
        self._integral = float(
            np.clip(self._integral, -self.integral_limit, self.integral_limit)
        )
        derivative = (error - self._prev_error) / dt
        self._prev_error = error
        output = self.kp * error + self.ki * self._integral + self.kd * derivative
        return float(np.clip(output, -self.output_limit, self.output_limit))

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = 0.0
