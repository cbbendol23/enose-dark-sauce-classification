import sys
import tkinter as tk
from tkinter import ttk
import threading
import time, csv, os
from matplotlib import lines
import pandas as pd
import joblib
from PIL import Image, ImageTk
import serial

LABELFONT = ("Segoe UI", 16, "bold")
TEXTFONT = ("Segoe UI", 20, "bold")
BUTTONFONT = ("Segoe UI", 22, "bold")
EBUTTONFONT = ("Segoe UI", 16, "bold")
RESULTFONT = ("Segoe UI", 30, "bold")
SENSORFONT = ("Segoe UI", 13, "bold")

# ---------------- SENSOR CONFIG ---------------- #
SENSOR_COLS = ["MQ2", "MQ3", "MQ135", "MQ136", "MQ137", "MQ138"]
SENSOR_COUNT = len(SENSOR_COLS)

# ---------------- BASE DIRECTORY (ALL FILES HERE) ---------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RAW_CSV      = os.path.join(BASE_DIR, "gathered_data.csv")
MEAN_CSV     = os.path.join(BASE_DIR, "gathered_data_mean.csv")
MEAN_LOG_CSV = os.path.join(BASE_DIR, "gathered_data_mean_log.csv")
MODEL_PATH   = os.path.join(BASE_DIR, "svm_best_model.joblib")
BG_IMAGE     = os.path.join(BASE_DIR, "background.png")

# ---------------- CSV LOG APPENDER---------------- #
def append_mean_log(means):
    """
    Append one row per test to gathered_data_mean_log.csv
    Format: Label + 6 sensor means
    """
    header = ["Label"] + SENSOR_COLS
    file_exists = os.path.exists(MEAN_LOG_CSV)

    with open(MEAN_LOG_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(["Unknown"] + list(means))
        f.flush()
        os.fsync(f.fileno())

# ---------------- SERIAL PORT MANAGER ---------------- #
def open_serial(port="/dev/ttyACM0", baud=9600):
    for attempt in range(5):
        try:
            ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
            return ser
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(0.5)
    print(f"Failed to open {port}")
    return None

def close_serial(ser):
    if ser:
        try:
            ser.close()
            time.sleep(0.5)
        except Exception:
            pass

# ---------------- RESTART ---------------- #
def restart_program(app=None, button=None):
    """Restart the current program, replacing the current process."""
    if button:
        button.config(state='disabled')
    if app:
        # Attempt to close all resources
        for frame in getattr(app, 'frames', {}).values():
            if hasattr(frame, 'stop_serial'):
                try:
                    frame.stop_serial()
                except Exception:
                    pass

        # Show restarting message
        top = tk.Toplevel(app)
        top.geometry("400x200+300+200")
        top.overrideredirect(True)
        tk.Label(top, text="Restarting...", font=TEXTFONT, bg="white").pack(expand=True, fill="both")
        app.update()

        def _do_restart():
            python = sys.executable
            os.execv(python, [python] + sys.argv)

        app.after(800, _do_restart)
    else:
        python = sys.executable
        os.execv(python, [python] + sys.argv)

# ---------------- MAIN APP ---------------- #
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.after(100, self._activate_fullscreen)
        self.bind('<Escape>', lambda e: self.attributes('-fullscreen', False))

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.configure("TButton", font=BUTTONFONT, padding=10)
        style.configure("Exit.TButton", font=EBUTTONFONT, padding=4)
        style.configure("Restart.TButton", font=EBUTTONFONT, padding=4)

        self.frames = {}
        for F in (StartPage, ClassificationPage, ClassificationReadingPage, ProcessingPage, ResultPage, ExhaustPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def _activate_fullscreen(self):
        self.attributes('-fullscreen', True)
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(500, lambda: self.attributes('-topmost', False))

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

# ---------------- START PAGE ---------------- #
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.bg_image = Image.open(BG_IMAGE).resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose",
                 font=LABELFONT, bg="white").pack(expand=True, fill="both")

        canvas.create_text(400, 200, text="Press Start to Begin!", font=TEXTFONT, fill="white")
        ttk.Button(canvas, text="Start", style="TButton",
                   command=lambda: [controller.show_frame(ClassificationReadingPage),
                                    controller.frames[ClassificationReadingPage].start_timer(controller)]
                   ).place(x=295, y=265)

        ttk.Button(canvas, text="Exit", style="Exit.TButton", command=controller.quit).place(x=640, y=430)

# ---------------- CLASSIFICATION PAGE ---------------- #
class ClassificationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.bg_image = Image.open(BG_IMAGE).resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose",
                 font=LABELFONT, bg="white").pack(expand=True, fill="both")

        canvas.create_text(400, 200, text="Please place the Sample Inside the Chamber",
                           font=TEXTFONT, fill="white")

        ttk.Button(canvas, text="Start Classifying", style="TButton",
                   command=lambda: [controller.show_frame(ClassificationReadingPage),
                                    controller.frames[ClassificationReadingPage].start_timer(controller)]
                   ).place(x=285, y=265)

        restart_btn = ttk.Button(canvas, text="Restart App", style="Restart.TButton")
        restart_btn.config(command=lambda: restart_program(app=controller, button=restart_btn))
        restart_btn.place(x=10, y=430)

        ttk.Button(canvas, text="Exit", style="Exit.TButton", command=controller.quit).place(x=640, y=430)

# ---------------- CLASSIFICATION READING PAGE ---------------- #
class ClassificationReadingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.ser = None
        self.gathering = False
        self.gather_thread = None
        self.remaining_time = 600
        self._timer_after_id = None

        # Background
        self.bg_image = Image.open(BG_IMAGE).resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # Title
        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(
            title_frame,
            text="SVM Dark Condiment Classification using E-Nose",
            font=LABELFONT,
            bg="white"
        ).pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="PROCESS: Gathering Data....",
                                font=TEXTFONT, fill="white")
        self.timer_text_id = self.canvas.create_text(400, 250, text="10:00",
                                                     font=TEXTFONT, fill="white")

        # Live sensor display
        self.sensor_display_running = False
        self.latest_values = ["--.--"] * SENSOR_COUNT

        self.sensor_text_id = self.canvas.create_text(
            400, 300,
            text=self.format_sensor_text(),
            font=SENSORFONT,
            fill="yellow",
            justify="center"
        )

        ttk.Button(
            self.canvas, text="Exit", style="Exit.TButton",
            command=lambda: [self.stop_serial(), controller.quit()]
        ).place(x=640, y=430)

        ttk.Button(
            self.canvas, text="Skip", style="Restart.TButton",
            command=self.skip_and_save
        ).place(x=490, y=430)

    def start_timer(self, controller):
        self.remaining_time = 600
        self.gathering = True

        self.latest_values = ["--.--"] * SENSOR_COUNT
        self.sensor_display_running = True
        self.update_sensor_display()

        self.gather_thread = threading.Thread(target=self.gather_data, daemon=True)
        self.gather_thread.start()

        self.update_timer(controller)

    def gather_data(self, filename=RAW_CSV, port="/dev/ttyACM0", baud=9600):
        header = ["Label"] + SENSOR_COLS
        try:
            self.ser = open_serial(port, baud)
            if not self.ser:
                print("Could not open COM port, skipping gathering")
                return

            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)

            while self.gathering:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                values = [v.strip() for v in line.split(",") if v.strip()]
                if len(values) < SENSOR_COUNT:
                    continue

                self.latest_values = values[:SENSOR_COUNT]
                row = ["Unknown"] + self.latest_values

                with open(filename, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(row)

        except Exception as e:
            print(f"Error during data gathering: {e}")
        finally:
            self.stop_serial()

    def format_sensor_text(self):
        pairs = [f"{name}: {val}" for name, val in zip(SENSOR_COLS, self.latest_values)]
        per_line = 3
        lines = ["  ".join(pairs[i:i + per_line]) for i in range(0, len(pairs), per_line)]
        return "\n".join(lines)

    def update_sensor_display(self):
        self.canvas.itemconfig(self.sensor_text_id, text=self.format_sensor_text())
        if self.sensor_display_running:
            self.after(500, self.update_sensor_display)

    def update_timer(self, controller):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.canvas.itemconfig(self.timer_text_id, text=f"{minutes}:{seconds:02d}")

        if self.remaining_time > 0 and self.gathering:
            self.remaining_time -= 1
            self._timer_after_id = self.after(1000, self.update_timer, controller)
        else:
            self.gathering = False
            self.stop_serial()

            try:
                self.save_mean_only()
            except Exception as e:
                print(f"Error saving mean at timer end: {e}")

            controller.show_frame(ProcessingPage)
            self.after(1000, lambda: [
                controller.frames[ResultPage].update_results(),
                controller.show_frame(ResultPage)
            ])

    def skip_and_save(self):
        if self._timer_after_id:
            try:
                self.after_cancel(self._timer_after_id)
            except Exception:
                pass
            self._timer_after_id = None

        self.gathering = False
        self.stop_serial()

        if self.gather_thread and self.gather_thread.is_alive():
            self.gather_thread.join(timeout=2)

        try:
            self.save_mean_only()
        except Exception as e:
            print(f"Error saving mean on skip: {e}")

        self.canvas.itemconfig(self.timer_text_id, text="Stopped")

        self.controller.show_frame(ProcessingPage)
        self.after(1000, lambda: [
            self.controller.frames[ResultPage].update_results(),
            self.controller.show_frame(ResultPage)
        ])

    def compute_means_from_raw(self):
        if not os.path.exists(RAW_CSV):
            raise FileNotFoundError("gathered_data.csv not found")

        df = pd.read_csv(RAW_CSV)
        if df.empty:
            raise ValueError("gathered_data.csv is empty")

        df.rename(columns=lambda c: c.strip(), inplace=True)
        df = df.reindex(columns=["Label"] + SENSOR_COLS)
        return df[SENSOR_COLS].astype(float).mean()

    def save_mean_only(self):
        header = ["Label"] + SENSOR_COLS
        means = self.compute_means_from_raw()

        with open(MEAN_CSV, "w", newline="") as mf:
            writer = csv.writer(mf)
            writer.writerow(header)
            writer.writerow(["Unknown"] + list(means))
            mf.flush()
            os.fsync(mf.fileno())

    def stop_serial(self):
        self.gathering = False
        self.sensor_display_running = False
        if hasattr(self, "ser") and self.ser:
            close_serial(self.ser)
            self.ser = None

# ---------------- PROCESSING PAGE ---------------- #
class ProcessingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.bg_image = Image.open(BG_IMAGE).resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose",
                 font=LABELFONT, bg="white").pack(expand=True, fill="both")

        canvas.create_text(400, 240, text="Processing...", font=TEXTFONT, fill="orange")

# ---------------- RESULT PAGE ---------------- #
class ResultPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.bg_image = Image.open(BG_IMAGE).resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(
            title_frame,
            text="SVM Dark Condiment Classification using E-Nose",
            font=LABELFONT,
            bg="white"
        ).pack(expand=True, fill="both")

        self.result_text_id = self.canvas.create_text(
            400, 200,
            text="",
            font=RESULTFONT,
            fill="orange"
        )

        self.mean_text_id = self.canvas.create_text(
            400, 300,
            text="",
            font=SENSORFONT,
            fill="yellow",
            justify="center"
        )

        ttk.Button(
            self.canvas,
            text="Restart",
            style="Restart.TButton",
            command=lambda: [
                controller.show_frame(ExhaustPage),
                controller.frames[ExhaustPage].start_timer(controller)
            ]
        ).place(x=490, y=430)

        ttk.Button(
            self.canvas,
            text="Exit",
            style="Exit.TButton",
            command=controller.quit
        ).place(x=640, y=430)

        self.update_results()

    def format_mean_text(self, mean_vals):
        pairs = [f"{n}: {v}" for n, v in zip(SENSOR_COLS, mean_vals)]
        per_line = 3
        lines = ["  ".join(pairs[i:i+per_line]) for i in range(0, len(pairs), per_line)]
        return "\n" + "\n".join(lines)

    def update_results(self):
        try:
            # Load model
            model = joblib.load(MODEL_PATH)
            expected_cols = list(getattr(model, "feature_names_in_", SENSOR_COLS))

            # Read mean CSV written by ClassificationReadingPage
            df = pd.read_csv(MEAN_CSV)
            df.rename(columns=lambda c: c.strip(), inplace=True)

            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                raise ValueError(f"Missing columns in gathered_data_mean.csv: {missing}")

            row = df.loc[0, expected_cols].astype(float).tolist()
            X_infer = pd.DataFrame([row], columns=expected_cols)

            # Predict
            result = model.predict(X_infer)[0]

            missing_means = [c for c in SENSOR_COLS if c not in df.columns]
            if missing_means:
                raise ValueError(f"Missing mean columns in gathered_data_mean.csv: {missing_means}")

            mean_vals = df.loc[0, SENSOR_COLS].astype(float).tolist()
            mean_vals_display = [f"{v:.2f}" for v in mean_vals]

        except Exception as e:
            result = f"Error: {e}"
            mean_vals_display = ["--.--"] * SENSOR_COUNT

        color_map = {
            "Soy Sauce": "#F79503",
            "Fish Sauce": "#F79503",
            "Oyster Sauce": "#F79503",
            "Worcestershire Sauce": "#F79503"
        }

        self.canvas.itemconfig(
            self.result_text_id,
            text=f"RESULT: {result}",
            fill=color_map.get(str(result), "orange")
        )

        self.canvas.itemconfig(
            self.mean_text_id,
            text=self.format_mean_text(mean_vals_display)
        )

# ---------------- EXHAUST PAGE ---------------- #
class ExhaustPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.ser = None
        self.gathering = False
        self.remaining_time = 900  # 15 minutes exhaust
        self._timer_after_id = None
        self.gather_thread = None

        self.bg_image = Image.open(BG_IMAGE).resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(
            title_frame,
            text="Exhaust Process",
            font=LABELFONT,
            bg="white"
        ).pack(expand=True, fill="both")

        self.canvas.create_text(
            400, 200,
            text="PROCESS: Exhausting Sensor....",
            font=TEXTFONT,
            fill="white"
        )

        self.timer_text_id = self.canvas.create_text(
            400, 250,
            text="15:00",
            font=TEXTFONT,
            fill="white"
        )


        self.latest_values = ["--.--"] * SENSOR_COUNT
        self.sensor_display_running = False

        self.sensor_text_id = self.canvas.create_text(
            400, 320,
            text=self.format_sensor_text(),
            font=SENSORFONT,
            fill="yellow",
            justify="center"
        )

        ttk.Button(
            self.canvas,
            text="Exit",
            style="Exit.TButton",
            command=lambda: [self.stop_serial(), controller.quit()]
        ).place(x=640, y=430)

        ttk.Button(
            self.canvas,
            text="Skip",
            style="Restart.TButton",
            command=lambda: [
                self.stop_serial(),
                controller.show_frame(ClassificationPage)
            ]
        ).place(x=490, y=430)

    def start_timer(self, controller):
        self.remaining_time = 900
        self.gathering = True

        self.latest_values = ["--.--"] * SENSOR_COUNT
        self.sensor_display_running = True
        self.update_sensor_display()

        self.gather_thread = threading.Thread(
            target=self.gather_data,
            daemon=True
        )
        self.gather_thread.start()

        self.update_timer(controller)

    def gather_data(self, port="/dev/ttyACM0", baud=9600):
        try:
            self.ser = open_serial(port, baud)
            if not self.ser:
                print("Could not open COM port for exhaust")
                return

            while self.gathering and self.remaining_time > 0:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                values = [v.strip() for v in line.split(",") if v.strip()]
                if len(values) < SENSOR_COUNT:
                    continue

                self.latest_values = values[:SENSOR_COUNT]

        except Exception as e:
            print(f"Error during exhaust: {e}")
        finally:
            self.stop_serial()

    def format_sensor_text(self):
        pairs = [f"{name}: {val}" for name, val in zip(SENSOR_COLS, self.latest_values)]
        per_line = 3
        lines = ["  ".join(pairs[i:i + per_line]) for i in range(0, len(pairs), per_line)]
        return "\n".join(lines)

    def update_sensor_display(self):
        self.canvas.itemconfig(
            self.sensor_text_id,
            text=self.format_sensor_text()
        )
        if self.sensor_display_running:
            self.after(500, self.update_sensor_display)

    def update_timer(self, controller):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.canvas.itemconfig(
            self.timer_text_id,
            text=f"{minutes:02d}:{seconds:02d}"
        )

        if self.remaining_time > 0 and self.gathering:
            self.remaining_time -= 1
            self._timer_after_id = self.after(
                1000,
                self.update_timer,
                controller
            )
        else:
            self.gathering = False
            self.stop_serial()
            controller.show_frame(ClassificationPage)

    def stop_serial(self):
        self.gathering = False
        self.sensor_display_running = False
        if self.ser:
            close_serial(self.ser)
            self.ser = None


if __name__ == "__main__":
    app = App()
    app.mainloop()
