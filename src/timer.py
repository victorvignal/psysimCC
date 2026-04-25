import time
from dataclasses import dataclass, field


@dataclass
class SessionTimer:
    duration_minutes: int  # 0 = sem limite

    _accumulated: float = field(default=0.0, init=False)
    _segment_start: float | None = field(default=None, init=False)
    _notified: set[int] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        self._segment_start = time.monotonic()

    @property
    def is_paused(self) -> bool:
        return self._segment_start is None

    @property
    def elapsed_seconds(self) -> float:
        if self._segment_start is None:
            return self._accumulated
        return self._accumulated + (time.monotonic() - self._segment_start)

    @property
    def elapsed_str(self) -> str:
        m, s = divmod(int(self.elapsed_seconds), 60)
        return f"{m:02d}:{s:02d}"

    @property
    def remaining_seconds(self) -> float | None:
        if not self.duration_minutes:
            return None
        return max(0.0, self.duration_minutes * 60 - self.elapsed_seconds)

    @property
    def remaining_str(self) -> str | None:
        rem = self.remaining_seconds
        if rem is None:
            return None
        m, s = divmod(int(rem), 60)
        return f"{m:02d}:{s:02d}"

    @property
    def expired(self) -> bool:
        rem = self.remaining_seconds
        return rem is not None and rem <= 0

    def pause(self) -> None:
        if self._segment_start is not None:
            self._accumulated += time.monotonic() - self._segment_start
            self._segment_start = None

    def resume(self) -> None:
        if self._segment_start is None:
            self._segment_start = time.monotonic()

    def toggle(self) -> bool:
        """Alterna pausa/retomada. Retorna True se ficou pausado."""
        if self.is_paused:
            self.resume()
            return False
        self.pause()
        return True

    def status_line(self) -> str:
        paused = " [PAUSADO]" if self.is_paused else ""
        if self.duration_minutes:
            return f"⏱ {self.elapsed_str} / {self.duration_minutes:02d}:00  (resta {self.remaining_str}){paused}"
        return f"⏱ {self.elapsed_str}{paused}"

    def check_threshold(self, minutes: int) -> bool:
        """True na primeira vez que o tempo restante atinge esse limiar."""
        if self.is_paused:
            return False
        rem = self.remaining_seconds
        if rem is None or minutes in self._notified:
            return False
        if rem <= minutes * 60:
            self._notified.add(minutes)
            return True
        return False
