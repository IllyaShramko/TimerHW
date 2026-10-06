"""Академічний таймер і секундомір 45 / 5 / 45 на базі CustomTkinter."""

import time
from typing import List

import customtkinter as ctk

DEFAULT_PHASES = [
    {"name": "Сесія 1", "seconds": 45 * 60, "color": "#3B8ED0"},
    {"name": "Перерва", "seconds": 5 * 60, "color": "#2FA572"},
    {"name": "Сесія 2", "seconds": 45 * 60, "color": "#3B8ED0"},
]

MODE_COUNTDOWN = "Таймер (зворотний)"
MODE_STOPWATCH = "Секундомір (прямий)"


def format_time(seconds: int) -> str:
    """Форматувати кількість секунд у рядок виду MM:SS або HH:MM:SS."""
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class TimeSettingsDialog(ctk.CTkToplevel):
    """Діалогове вікно для налаштування тривалості кожної фази."""

    def __init__(self, parent: "AcademicTimerApp") -> None:
        super().__init__(parent)
        self.parent_app = parent

        self.title("Налаштування часу")
        self.geometry("380x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self) -> None:
        """Розмістити діалогове вікно по центру батьківського вікна."""
        self.update_idletasks()
        p_x = self.parent_app.winfo_x()
        p_y = self.parent_app.winfo_y()
        p_w = self.parent_app.winfo_width()
        p_h = self.parent_app.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = p_x + max(0, (p_w - w) // 2)
        y = p_y + max(0, (p_h - h) // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Створити форму налаштування тривалості у хвилинах."""
        header_lbl = ctk.CTkLabel(
            self,
            text="Тривалість фаз (у хвилинах):",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header_lbl.pack(pady=(20, 15))

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(padx=30, fill="x")

        self.entries = []
        for idx, phase in enumerate(self.parent_app.phases):
            row = ctk.CTkFrame(form_frame, fg_color="transparent")
            row.pack(fill="x", pady=6)

            lbl = ctk.CTkLabel(
                row,
                text=f"{phase['name']}:",
                width=110,
                anchor="w",
                font=ctk.CTkFont(size=13),
            )
            lbl.pack(side="left")

            entry = ctk.CTkEntry(row, width=90, justify="center")
            entry.insert(0, str(phase["seconds"] // 60))
            entry.pack(side="left", padx=10)

            unit_lbl = ctk.CTkLabel(row, text="хв", text_color="gray")
            unit_lbl.pack(side="left")

            self.entries.append(entry)

        self.error_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#EF4444",
        )
        self.error_label.pack(pady=(8, 4))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=10, fill="x", padx=30)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Зберегти",
            command=self._apply_settings,
            fg_color="#2FA572",
            hover_color="#26865C",
            width=140,
        )
        save_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

        reset_btn = ctk.CTkButton(
            btn_frame,
            text="45 / 5 / 45",
            command=self._reset_defaults,
            fg_color="#4A4D50",
            hover_color="#5D6165",
            width=140,
        )
        reset_btn.pack(side="right", expand=True, fill="x")

    def _reset_defaults(self) -> None:
        """Відновити стандартні значення 45 / 5 / 45."""
        default_minutes = [45, 5, 45]
        for entry, minutes in zip(self.entries, default_minutes):
            entry.delete(0, "end")
            entry.insert(0, str(minutes))
        self.error_label.configure(text="")

    def _apply_settings(self) -> None:
        """Перевірити введені значення та оновити тривалість фаз."""
        new_seconds = []
        for idx, entry in enumerate(self.entries):
            val_str = entry.get().strip()
            if not val_str.isdigit():
                phase_name = self.parent_app.phases[idx]["name"]
                self.error_label.configure(
                    text=f"Введіть ціле число для '{phase_name}'!"
                )
                return
            minutes = int(val_str)
            if minutes < 1 or minutes > 360:
                self.error_label.configure(
                    text="Тривалість має бути від 1 до 360 хв!"
                )
                return
            new_seconds.append(minutes * 60)

        # Оновлення фаз у головному додатку
        for idx, seconds in enumerate(new_seconds):
            self.parent_app.phases[idx]["seconds"] = seconds

        self.parent_app.on_durations_updated()
        self.destroy()


class AcademicTimerApp(ctk.CTk):
    """Головне вікно програми таймера/секундоміра."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Таймер 45 / 5 / 45")
        self.geometry("540x680")
        self.minsize(500, 640)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Список фаз (користувач може змінювати тривалість)
        self.phases: List[dict] = [dict(p) for p in DEFAULT_PHASES]

        # Стан таймера
        self.current_phase_idx: int = 0
        self.is_running: bool = False
        self.elapsed_in_phase: float = 0.0
        self.last_timestamp: float = 0.0
        self.display_mode: str = MODE_COUNTDOWN

        self.auto_advance_var = ctk.BooleanVar(value=True)

        self._build_ui()
        self._update_phase_cards()
        self._update_display()
        self._tick()

    def _build_ui(self) -> None:
        """Створити всі елементи інтерфейсу користувача."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Верхній заголовок та кнопка налаштування часу
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(
            row=0, column=0, padx=20, pady=(15, 5), sticky="ew"
        )
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header_frame,
            text="Академічний таймер",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title_label.pack()

        self.subtitle_label = ctk.CTkLabel(
            header_frame,
            text=self._format_subtitle(),
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.subtitle_label.pack(pady=(2, 6))

        header_settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙ Змінити тривалість фаз (45 / 5 / 45)",
            command=self._open_time_settings,
            fg_color="#374151",
            hover_color="#4B5563",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        header_settings_btn.pack(pady=(2, 0))

        # 2. Картки фаз
        self.cards_frame = ctk.CTkFrame(self)
        self.cards_frame.grid(
            row=1, column=0, padx=20, pady=10, sticky="ew"
        )
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_widgets = []
        for idx, phase in enumerate(self.phases):
            card = ctk.CTkFrame(self.cards_frame, corner_radius=8)
            card.grid(row=0, column=idx, padx=6, pady=8, sticky="nsew")

            title_lbl = ctk.CTkLabel(
                card,
                text=phase["name"],
                font=ctk.CTkFont(size=14, weight="bold"),
            )
            title_lbl.pack(pady=(8, 2))

            dur_lbl = ctk.CTkLabel(
                card,
                text=f"{phase['seconds'] // 60} хв",
                font=ctk.CTkFont(size=12),
                text_color="gray",
            )
            dur_lbl.pack(pady=(0, 4))

            status_lbl = ctk.CTkLabel(
                card,
                text="Очікує",
                font=ctk.CTkFont(size=11),
                text_color="gray",
            )
            status_lbl.pack(pady=(0, 6))

            for w in (card, title_lbl, dur_lbl, status_lbl):
                w.bind(
                    "<Button-1>",
                    lambda _e: self._open_time_settings()
                )
                w.configure(cursor="hand2")

            self.card_widgets.append({
                "frame": card,
                "title": title_lbl,
                "dur": dur_lbl,
                "status": status_lbl,
            })

        # 3. Центральний блок відображення часу
        center_frame = ctk.CTkFrame(self, corner_radius=12)
        center_frame.grid(
            row=2, column=0, padx=20, pady=10, sticky="nsew"
        )
        center_frame.grid_columnconfigure(0, weight=1)

        self.phase_name_label = ctk.CTkLabel(
            center_frame,
            text="",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.phase_name_label.pack(pady=(15, 5))

        self.time_label = ctk.CTkLabel(
            center_frame,
            text="45:00",
            font=ctk.CTkFont(size=64, weight="bold"),
        )
        self.time_label.pack(pady=5)

        self.progress_bar = ctk.CTkProgressBar(
            center_frame, width=360, height=14, corner_radius=7
        )
        self.progress_bar.pack(pady=(10, 8))
        self.progress_bar.set(0.0)

        self.total_info_label = ctk.CTkLabel(
            center_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.total_info_label.pack(pady=(0, 12))

        # Перемикач режиму відображення: Таймер / Секундомір
        self.mode_segmented = ctk.CTkSegmentedButton(
            center_frame,
            values=[MODE_COUNTDOWN, MODE_STOPWATCH],
            command=self._on_mode_change,
        )
        self.mode_segmented.set(MODE_COUNTDOWN)
        self.mode_segmented.pack(pady=(0, 15))

        # 4. Блок кнопок управління
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctrl_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.prev_btn = ctk.CTkButton(
            ctrl_frame,
            text="⏮ Назад",
            width=80,
            command=self._prev_phase,
            fg_color="#4A4D50",
            hover_color="#5D6165",
        )
        self.prev_btn.grid(row=0, column=0, padx=4, pady=5, sticky="ew")

        self.start_pause_btn = ctk.CTkButton(
            ctrl_frame,
            text="▶ Старт",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=42,
            command=self._toggle_start_pause,
            fg_color="#2FA572",
            hover_color="#26865C",
        )
        self.start_pause_btn.grid(
            row=0, column=1, columnspan=2, padx=6, pady=5, sticky="ew"
        )

        self.next_btn = ctk.CTkButton(
            ctrl_frame,
            text="Вперед ⏭",
            width=80,
            command=self._next_phase,
            fg_color="#4A4D50",
            hover_color="#5D6165",
        )
        self.next_btn.grid(row=0, column=3, padx=4, pady=5, sticky="ew")

        self.reset_btn = ctk.CTkButton(
            ctrl_frame,
            text="Скинути поточну фазу",
            command=self._reset_current_phase,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
        )
        self.reset_btn.grid(
            row=1, column=0, columnspan=2, padx=4, pady=(5, 0), sticky="ew"
        )

        self.reset_all_btn = ctk.CTkButton(
            ctrl_frame,
            text="Скинути весь цикл",
            command=self._reset_all,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
        )
        self.reset_all_btn.grid(
            row=1, column=2, columnspan=2, padx=4, pady=(5, 0), sticky="ew"
        )

        # 5. Нижня панель налаштувань
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.grid(
            row=4, column=0, padx=20, pady=(5, 15), sticky="ew"
        )

        auto_cb = ctk.CTkCheckBox(
            bottom_frame,
            text="Автоперехід до наступної фази",
            variable=self.auto_advance_var,
        )
        auto_cb.pack(pady=4)

    def _format_subtitle(self) -> str:
        """Сформувати рядок підзаголовка з поточною тривалістю фаз."""
        return " • ".join(
            f"{p['seconds'] // 60} хв {p['name'].lower()}"
            for p in self.phases
        )

    def _open_time_settings(self) -> None:
        """Відкрити модальне вікно зміни тривалості."""
        TimeSettingsDialog(self)

    def on_durations_updated(self) -> None:
        """Обробити оновлення тривалості користувачем."""
        self.subtitle_label.configure(text=self._format_subtitle())
        for idx, phase in enumerate(self.phases):
            self.card_widgets[idx]["dur"].configure(
                text=f"{phase['seconds'] // 60} хв"
            )

        cur_sec = self.phases[self.current_phase_idx]["seconds"]
        if self.elapsed_in_phase > cur_sec:
            self.elapsed_in_phase = float(cur_sec)

        self._update_display()

    def _on_mode_change(self, selected_mode: str) -> None:
        """Обробити перемикання режиму відображення часу."""
        self.display_mode = selected_mode
        self._update_display()

    def _toggle_start_pause(self) -> None:
        """Запустити або призупинити таймер/секундомір."""
        if self.is_running:
            self.is_running = False
            self.start_pause_btn.configure(
                text="▶ Старт",
                fg_color="#2FA572",
                hover_color="#26865C",
            )
        else:
            self.is_running = True
            self.last_timestamp = time.monotonic()
            self.start_pause_btn.configure(
                text="⏸ Пауза",
                fg_color="#D97706",
                hover_color="#B45309",
            )

    def _prev_phase(self) -> None:
        """Перейти до попередньої фази."""
        if self.current_phase_idx > 0:
            self.current_phase_idx -= 1
            self.elapsed_in_phase = 0.0
            self.last_timestamp = time.monotonic()
            self._update_phase_cards()
            self._update_display()

    def _next_phase(self) -> None:
        """Перейти до наступної фази або завершити сесію."""
        if self.current_phase_idx < len(self.phases) - 1:
            self.current_phase_idx += 1
            self.elapsed_in_phase = 0.0
            self.last_timestamp = time.monotonic()
            self._update_phase_cards()
            self._update_display()
        else:
            self._on_cycle_completed()

    def _reset_current_phase(self) -> None:
        """Скинути час поточної фази на початок."""
        self.elapsed_in_phase = 0.0
        self.last_timestamp = time.monotonic()
        self._update_display()

    def _reset_all(self) -> None:
        """Повністю скинути весь цикл на першу фазу."""
        self.is_running = False
        self.current_phase_idx = 0
        self.elapsed_in_phase = 0.0
        self.start_pause_btn.configure(
            text="▶ Старт",
            fg_color="#2FA572",
            hover_color="#26865C",
        )
        self._update_phase_cards()
        self._update_display()

    def _on_phase_finished(self) -> None:
        """Обробити завершення поточної фази."""
        if self.current_phase_idx < len(self.phases) - 1:
            self.current_phase_idx += 1
            self.elapsed_in_phase = 0.0
            self.last_timestamp = time.monotonic()
            if not self.auto_advance_var.get():
                self.is_running = False
                self.start_pause_btn.configure(
                    text="▶ Старт",
                    fg_color="#2FA572",
                    hover_color="#26865C",
                )
            self._update_phase_cards()
            self._update_display()
        else:
            self._on_cycle_completed()

    def _on_cycle_completed(self) -> None:
        """Обробити завершення всього циклу з трьох фаз."""
        self.is_running = False
        self.start_pause_btn.configure(
            text="▶ Старт",
            fg_color="#2FA572",
            hover_color="#26865C",
        )
        self._update_phase_cards(all_completed=True)
        self.phase_name_label.configure(text="Усі заняття завершено! 🎉")
        self.time_label.configure(text="00:00")
        self.progress_bar.set(1.0)
        total_cycle = sum(p["seconds"] for p in self.phases)
        self.total_info_label.configure(
            text=f"Загальний прогрес: {format_time(total_cycle)} / "
                 f"{format_time(total_cycle)}"
        )

    def _update_phase_cards(self, all_completed: bool = False) -> None:
        """Оновити візуальний стан карток фаз."""
        for idx, card in enumerate(self.card_widgets):
            if all_completed or idx < self.current_phase_idx:
                card["frame"].configure(fg_color=("#E5E7EB", "#1F2937"))
                card["status"].configure(
                    text="✓ Завершено", text_color="#2FA572"
                )
            elif idx == self.current_phase_idx:
                card["frame"].configure(fg_color=("#DBEAFE", "#1E3A8A"))
                card["status"].configure(
                    text="● Активно", text_color="#3B8ED0"
                )
            else:
                card["frame"].configure(fg_color=("#F3F4F6", "#111827"))
                card["status"].configure(text="Очікує", text_color="gray")

    def _update_display(self) -> None:
        """Оновити текстові показники часу та смугу прогресу."""
        if self.current_phase_idx >= len(self.phases):
            return

        cur_phase = self.phases[self.current_phase_idx]
        name = cur_phase["name"]
        duration = cur_phase["seconds"]
        self.phase_name_label.configure(
            text=f"{name} ({duration // 60} хв)"
        )

        # Розрахунок часу відповідно до вибраного режиму
        if self.display_mode == MODE_COUNTDOWN:
            remaining = max(0.0, duration - self.elapsed_in_phase)
            self.time_label.configure(text=format_time(int(remaining)))
        else:
            self.time_label.configure(
                text=format_time(int(self.elapsed_in_phase))
            )

        progress = min(1.0, max(0.0, self.elapsed_in_phase / duration))
        self.progress_bar.set(progress)

        # Загальний сумарний час циклу
        completed_duration = sum(
            self.phases[i]["seconds"]
            for i in range(self.current_phase_idx)
        )
        total_elapsed = completed_duration + self.elapsed_in_phase
        total_cycle = sum(p["seconds"] for p in self.phases)

        self.total_info_label.configure(
            text=f"Загальний прогрес: {format_time(int(total_elapsed))} / "
                 f"{format_time(total_cycle)}"
        )

    def _tick(self) -> None:
        """Періодичний крок таймера."""
        if self.is_running:
            now = time.monotonic()
            dt = now - self.last_timestamp
            self.last_timestamp = now
            self.elapsed_in_phase += dt

            current_duration = self.phases[self.current_phase_idx]["seconds"]
            if self.elapsed_in_phase >= current_duration:
                self.elapsed_in_phase = float(current_duration)
                self._update_display()
                self._on_phase_finished()
            else:
                self._update_display()

        self.after(100, self._tick)


def main() -> None:
    """Точка входу в програму."""
    app = AcademicTimerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
