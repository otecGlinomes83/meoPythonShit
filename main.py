from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from password_generator import (
    DEFAULT_DB_FILE,
    MAX_LENGTH,
    MIN_LENGTH,
    add_history_entry,
    filter_history,
    generate_password,
    history_to_table_rows,
    load_data,
    save_data,
)


class PasswordGeneratorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Random Password Generator")
        self.geometry("980x640")
        self.minsize(900, 580)

        self.data = load_data()
        self.filtered_history = list(self.data.get("history", []))

        self.length_var = tk.IntVar(value=12)
        self.digits_var = tk.BooleanVar(value=True)
        self.letters_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=False)
        self.password_var = tk.StringVar(value="")
        self.filter_var = tk.StringVar(value="")

        self._build_ui()
        self.refresh_history_table()

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        controls = ttk.LabelFrame(main, text="Параметры генерации", padding=12)
        controls.pack(fill="x")

        length_row = ttk.Frame(controls)
        length_row.pack(fill="x", pady=(0, 8))

        ttk.Label(length_row, text="Длина пароля:").pack(side="left")
        self.length_value_label = ttk.Label(length_row, text=str(self.length_var.get()))
        self.length_value_label.pack(side="right")

        self.length_scale = ttk.Scale(
            controls,
            from_=MIN_LENGTH,
            to=MAX_LENGTH,
            orient="horizontal",
            command=self._on_length_changed,
        )
        self.length_scale.set(self.length_var.get())
        self.length_scale.pack(fill="x")

        options = ttk.Frame(controls)
        options.pack(fill="x", pady=10)

        ttk.Checkbutton(options, text="Цифры", variable=self.digits_var).grid(row=0, column=0, padx=(0, 18), sticky="w")
        ttk.Checkbutton(options, text="Буквы", variable=self.letters_var).grid(row=0, column=1, padx=(0, 18), sticky="w")
        ttk.Checkbutton(options, text="Спецсимволы", variable=self.symbols_var).grid(row=0, column=2, sticky="w")

        action_row = ttk.Frame(controls)
        action_row.pack(fill="x", pady=(6, 0))

        ttk.Button(action_row, text="Сгенерировать", command=self.on_generate).pack(side="left")
        ttk.Button(action_row, text="Копировать", command=self.copy_password).pack(side="left", padx=8)
        ttk.Button(action_row, text="Сохранить историю", command=self.save_history).pack(side="left")

        result_frame = ttk.LabelFrame(main, text="Результат", padding=12)
        result_frame.pack(fill="x", pady=(12, 0))

        result_entry = ttk.Entry(result_frame, textvariable=self.password_var, font=("Segoe UI", 12))
        result_entry.pack(fill="x")
        result_entry.configure(state="readonly")

        history_frame = ttk.LabelFrame(main, text="История", padding=12)
        history_frame.pack(fill="both", expand=True, pady=(12, 0))

        filter_row = ttk.Frame(history_frame)
        filter_row.pack(fill="x", pady=(0, 10))

        ttk.Label(filter_row, text="Фильтр:").pack(side="left")
        ttk.Entry(filter_row, textvariable=self.filter_var).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(filter_row, text="Применить", command=self.apply_filter).pack(side="left")
        ttk.Button(filter_row, text="Сбросить", command=self.reset_filter).pack(side="left", padx=8)
        ttk.Button(filter_row, text="Удалить выбранное", command=self.delete_selected).pack(side="left")

        columns = ("id", "password", "length", "digits", "letters", "symbols", "createdAt")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=14)

        headings = {
            "id": "ID",
            "password": "Пароль",
            "length": "Длина",
            "digits": "Цифры",
            "letters": "Буквы",
            "symbols": "Спецсимволы",
            "createdAt": "Дата",
        }

        widths = {
            "id": 50,
            "password": 280,
            "length": 70,
            "digits": 90,
            "letters": 90,
            "symbols": 110,
            "createdAt": 200,
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        status = ttk.Label(
            main,
            text=f"Файл данных: {DEFAULT_DB_FILE}",
            anchor="w",
        )
        status.pack(fill="x", pady=(10, 0))

    def _on_length_changed(self, value: str) -> None:
        rounded = int(float(value))
        self.length_var.set(rounded)
        self.length_value_label.config(text=str(rounded))

    def on_generate(self) -> None:
        length = int(self.length_var.get())
        use_digits = bool(self.digits_var.get())
        use_letters = bool(self.letters_var.get())
        use_symbols = bool(self.symbols_var.get())

        if not (MIN_LENGTH <= length <= MAX_LENGTH):
            messagebox.showerror("Ошибка", f"Длина должна быть от {MIN_LENGTH} до {MAX_LENGTH}.")
            return

        if not (use_digits or use_letters or use_symbols):
            messagebox.showerror("Ошибка", "Выбери хотя бы один тип символов.")
            return

        try:
            password = generate_password(length, use_digits, use_letters, use_symbols)
        except ValueError as exc:
            messagebox.showerror("Ошибка", str(exc))
            return

        self.password_var.set(password)
        history = self.data.setdefault("history", [])
        add_history_entry(history, password, length, use_digits, use_letters, use_symbols)
        self.refresh_history_table()
        self.save_history()

    def copy_password(self) -> None:
        password = self.password_var.get().strip()
        if not password:
            messagebox.showinfo("Информация", "Сначала сгенерируй пароль.")
            return
        self.clipboard_clear()
        self.clipboard_append(password)
        self.update()
        messagebox.showinfo("Готово", "Пароль скопирован в буфер обмена.")

    def save_history(self) -> None:
        save_data(self.data)
        self.refresh_history_table()

    def refresh_history_table(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.filtered_history = filter_history(self.data.get("history", []), self.filter_var.get())
        for row in history_to_table_rows(self.filtered_history):
            self.tree.insert("", "end", values=row)

    def apply_filter(self) -> None:
        self.refresh_history_table()

    def reset_filter(self) -> None:
        self.filter_var.set("")
        self.refresh_history_table()

    def delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Информация", "Выбери запись для удаления.")
            return

        item = self.tree.item(selected[0], "values")
        if not item:
            return

        entry_id = int(item[0])
        history = self.data.get("history", [])
        self.data["history"] = [row for row in history if int(row.get("id", 0)) != entry_id]
        save_data(self.data)
        self.refresh_history_table()


if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()
