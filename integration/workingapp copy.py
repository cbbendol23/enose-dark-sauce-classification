import sys
import tkinter as tk
from tkinter import ttk
import threading
import time, csv, os
import pandas as pd
import joblib
import numpy as np
from PIL import Image, ImageTk
import serial

LABELFONT = ("Segoe UI", 16, "bold")
TEXTFONT = ("Segoe UI", 20, "bold")
BUTTONFONT = ("Segoe UI", 22, "bold")
EBUTTONFONT = ("Segoe UI", 16, "bold")
RESULTFONT = ("Segoe UI", 30, "bold")
SENSORFONT = ("Segoe UI", 13, "bold")

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

        app.after(800, lambda: _do_restart())
    else:
        python = sys.executable
        os.execv(python, [python] + sys.argv)

# ---------------- MAIN APP ---------------- #
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Delayed fullscreen activation for touchscreen reliability
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
        self.bg_image = Image.open("integration/background.png").resize((800,480), Image.LANCZOS)
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
                   ).place(x=300, y=280)
        ttk.Button(canvas, text="Exit", style="Exit.TButton", command=controller.quit).place(x=700, y=430)

# ---------------- CLASSIFICATION PAGE ---------------- #
class ClassificationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bg_image = Image.open("integration/background.png").resize((800,480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0,0,image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose",
                 font=LABELFONT, bg="white").pack(expand=True, fill="both")

        canvas.create_text(400, 200, text="Please place the Sample Inside the Chamber",
                           font=TEXTFONT, fill="white")

        start_btn = ttk.Button(canvas, text="Start Classifying", style="TButton",
                   command=lambda: [controller.show_frame(ClassificationReadingPage),
                                    controller.frames[ClassificationReadingPage].start_timer(controller)])
        start_btn.place(x=300, y=280)

        restart_btn = ttk.Button(canvas, text="Restart App", style="Restart.TButton")
        restart_btn.config(command=lambda: restart_program(app=controller.master, button=restart_btn))
        restart_btn.place(x=100, y=430)

        exit_btn = ttk.Button(canvas, text="Exit", style="Exit.TButton", command=controller.quit)
        exit_btn.place(x=700, y=430)

# ---------------- CLASSIFICATION READING PAGE ---------------- #
class ClassificationReadingPage(tk.Frame):
    def stop_serial(self):
        self.sensor_display_running = False
        self.gathering = False
        if hasattr(self, 'ser') and self.ser:
            close_serial(self.ser)
            self.ser = None

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.ser = None
        self.gathering = False
        self.gather_thread = None
        self.sensor_display_running = False
        self.latest_values = ["--.--"] * 4
        self.remaining_time = 600

        # Background
        self.bg_image = Image.open("integration/background.png").resize((800,480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0,0,image=self.bg_photo, anchor="nw")

        # Title
        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose",
                 font=LABELFONT, bg="white").pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="PROCESS: Gathering Data....", font=TEXTFONT, fill="white")
        self.sensor_text_id_1 = self.canvas.create_text(400, 290, text="MQ2: --.--  MQ3: --.--  MQ135: --.--  MQ136: --.--", font=SENSORFONT, fill="yellow")
        self.timer_text_id = self.canvas.create_text(400, 250, text="10:00", font=TEXTFONT, fill="white")

        ttk.Button(self.canvas, text="Exit", style="Exit.TButton",
                   command=lambda: [self.stop_serial(), controller.quit()]).place(x=700, y=430)
        ttk.Button(self.canvas, text="Skip", style="Restart.TButton", command=self.skip_and_save).place(x=550, y=430)

    # ---------------- SERIAL HANDLING ---------------- #
    def start_timer(self, controller):
        self.remaining_time = 600
        self.gathering = True
        self.sensor_display_running = True
        self.latest_values = ["--.--"] * 4
        self.gather_thread = threading.Thread(target=self.gather_data, daemon=True)
        self.gather_thread.start()
        self.update_sensor_display()
        self.update_timer(controller)

    def gather_data(self, filename="integration/gathered_data.csv", port="/dev/ttyACM0", baud=9600):
        sensor_cols = ["MQ2","MQ3","MQ135","MQ136"]
        header = ["Label"] + sensor_cols
        try:
            self.ser = open_serial(port, baud)
            if not self.ser:
                print("Could not open COM port, skipping gathering")
                return

            # write header fresh
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)

            start_time = time.time()
            while self.gathering and (time.time() - start_time < self.remaining_time):
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    values = line.split(",")
                    if len(values) >= 4:
                        row = ["Unknown"] + values[:4]
                        with open(filename, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(row)
                        self.latest_values = values[:4]
                        # Save mean instantly after each new row
                        try:
                            df = pd.read_csv(filename).reindex(columns=["Label"] + sensor_cols)
                            means = df[sensor_cols].astype(float).mean()
                            mean_filename = "integration/gathered_data_mean.csv"
                            with open(mean_filename, "w", newline="") as mf:
                                mwriter = csv.writer(mf)
                                mwriter.writerow(header)
                                mwriter.writerow(["Unknown"] + list(means))
                                mf.flush()
                                os.fsync(mf.fileno())
                        except Exception as e:
                            print(f"Error writing mean to new file: {e}")
        except Exception as e:
            print(f"Error during data gathering: {e}")
        finally:
            self.stop_serial()

    def update_sensor_display(self):
        first_line = f"MQ2: {self.latest_values[0]}  MQ3: {self.latest_values[1]}  MQ135: {self.latest_values[2]}  MQ136: {self.latest_values[3]}"
        self.canvas.itemconfig(self.sensor_text_id_1, text=first_line)
        if self.sensor_display_running:
            self.after(1000, self.update_sensor_display)

    def update_timer(self, controller):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.canvas.itemconfig(self.timer_text_id, text=f"{minutes}:{seconds:02d}")
        if self.remaining_time > 0 and self.gathering:
            self.remaining_time -= 1
            self._timer_after_id = self.after(1000, self.update_timer, controller)
        else:
            self.gathering = False
            self.sensor_display_running = False
            self.stop_serial()
            # Show processing page for 1 second before result
            controller.show_frame(ProcessingPage)
            self.after(1000, lambda: [controller.frames[ResultPage].update_results(), controller.show_frame(ResultPage)])

    def skip_and_save(self):
        if getattr(self, "_timer_after_id", None):
            try:
                self.after_cancel(self._timer_after_id)
            except:
                pass
            self._timer_after_id = None
        self.gathering = False
        if self.gather_thread and self.gather_thread.is_alive():
            self.gather_thread.join(timeout=2)
        # save mean to a new file
        try:
            sensor_cols = ["MQ2","MQ3","MQ135","MQ136"]
            header = ["Label"] + sensor_cols
            if os.path.exists("integration/gathered_data.csv"):
                df = pd.read_csv("integration/gathered_data.csv")
                if not df.empty:
                    df = df.reindex(columns=["Label"] + sensor_cols)
                    means = df[sensor_cols].astype(float).mean()
                    mean_filename = "integration/gathered_data_mean.csv"
                    with open(mean_filename, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(header)
                        writer.writerow(["Unknown"] + list(means))
                        f.flush()
                        os.fsync(f.fileno())
        except Exception as e:
            print(f"Error saving mean data on skip: {e}")
        self.canvas.itemconfig(self.timer_text_id, text="Stopped")
        self.stop_serial()
        # Show processing page for 1 second before result
        self.controller.show_frame(ProcessingPage)
        self.after(1000, lambda: [self.controller.frames[ResultPage].update_results(), self.controller.show_frame(ResultPage)])

# ---------------- PROCESSING PAGE ---------------- #
class ProcessingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bg_image = Image.open("integration/background.png").resize((800,480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0, y=0, relwidth=1, relheight=1)
        canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose", font=LABELFONT, bg="white").pack(expand=True, fill="both")
        canvas.create_text(400, 240, text="Processing...", font=TEXTFONT, fill="orange")

    def stop_serial(self):
        self.sensor_display_running = False
        self.gathering = False
        if hasattr(self, 'ser') and self.ser:
            close_serial(self.ser)
            self.ser = None

# ---------------- RESULT PAGE ---------------- #
class ResultPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bg_image = Image.open("integration/background.png").resize((800,480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0,y=0,relwidth=1,relheight=1)
        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0,0,image=self.bg_photo,anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5,y=70,anchor="n",width=550,height=45)
        tk.Label(title_frame, text="SVM Dark Condiment Classification using E-Nose",
                 font=LABELFONT, bg="white").pack(expand=True, fill="both")

        # placeholders
        self.result_text_id = self.canvas.create_text(400,200,text="",font=RESULTFONT, fill="orange")
        self.sensor_text_id_1 = self.canvas.create_text(400,260,text="", font=SENSORFONT, fill="yellow")

        ttk.Button(self.canvas, text="Restart", style="Restart.TButton",
                   command=lambda: [controller.show_frame(ExhaustPage),
                                    controller.frames[ExhaustPage].start_timer(controller)]).place(x=550, y=430)
        ttk.Button(self.canvas, text="Exit", style="Exit.TButton", command=controller.quit).place(x=700, y=430)

        self.update_results()

    def update_results(self):
        try:
            sensor_cols = ["MQ2","MQ3","MQ135","MQ136"]
            df = pd.read_csv("integration/gathered_data_mean.csv").reindex(columns=["Label"] + sensor_cols)
            data = df.loc[0, sensor_cols].values.astype(float)
            sensor_text = "  ".join([f"{col}:{val:.2f}" for col,val in zip(sensor_cols,data)])
            model = joblib.load("svm_best_model.joblib")
            result = model.predict(np.array(data).reshape(1,-1))[0]
        except Exception as e:
            sensor_text = ""
            result = f"Error: {e}"

        color_map = {"Soy Sauce":"#F79503","Fish Sauce":"#F79503","Oyster Sauce":"#F79503","Worcestershire Sauce":"#F79503"}

        self.canvas.itemconfig(self.result_text_id, text=f"RESULT: {result}", fill=color_map.get(str(result),"orange"))
        if sensor_text:
            self.canvas.itemconfig(self.sensor_text_id_1, text=sensor_text)

# ---------------- EXHAUST PAGE (MQ137/MQ138 removed) ---------------- #
class ExhaustPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.ser = None
        self.gathering = False
        self.sensor_display_running = False
        self.latest_values = ["--.--"] * 4
        self.remaining_time = 900  # 15 minutes exhaust

        self.bg_image = Image.open("integration/background.png").resize((800,480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        tk.Label(self, image=self.bg_photo).place(x=0,y=0,relwidth=1,relheight=1)
        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0,y=0,relwidth=1,relheight=1)
        self.canvas.create_image(0,0,image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5,y=70,anchor="n",width=550,height=45)
        tk.Label(title_frame, text="Exhaust Process", font=LABELFONT, bg="white").pack(expand=True, fill="both")

        self.canvas.create_text(400,200,text="PROCESS: Exhausting Sensor....", font=TEXTFONT, fill="white")
        self.sensor_text_id_1 = self.canvas.create_text(400, 290, text="MQ2: --.--  MQ3: --.--  MQ135: --.--  MQ136: --.--", font=SENSORFONT, fill="yellow")
        self.timer_text_id = self.canvas.create_text(400,250,text="15:00", font=TEXTFONT, fill="white")

        ttk.Button(self.canvas, text="Exit", style="Exit.TButton",
                   command=lambda: [self.stop_serial(), controller.quit()]).place(x=700, y=430)

        ttk.Button(self.canvas, text="Skip", style="Restart.TButton",
            command=lambda: [self.stop_serial(), controller.show_frame(ClassificationPage)]).place(x=550, y=430)

    def start_timer(self, controller):
        self.remaining_time = 900
        self.gathering = True
        self.sensor_display_running = True
        self.latest_values = ["--.--"] * 4
        self.gather_thread = threading.Thread(target=self.gather_data, daemon=True)
        self.gather_thread.start()
        self.update_sensor_display()
        self.update_timer(controller)

    def gather_data(self, port="/dev/ttyACM0", baud=9600):
        try:
            self.ser = open_serial(port, baud)
            if not self.ser:
                print("Could not open COM port for exhaust")
                return
            while self.gathering and self.remaining_time > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    values = line.split(",")
                    if len(values) >= 4:
                        self.latest_values = values[:4]
        except Exception as e:
            print(f"Error during exhaust: {e}")
        finally:
            self.stop_serial()

    def update_sensor_display(self):
        first_line = f"MQ2: {self.latest_values[0]}  MQ3: {self.latest_values[1]}  MQ135: {self.latest_values[2]}  MQ136: {self.latest_values[3]}"
        self.canvas.itemconfig(self.sensor_text_id_1, text=first_line)
        if self.sensor_display_running:
            self.after(1000, self.update_sensor_display)

    def update_timer(self, controller):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        self.canvas.itemconfig(self.timer_text_id, text=f"{minutes:02d}:{seconds:02d}")
        if self.remaining_time > 0 and self.gathering:
            self.remaining_time -= 1
            self._timer_after_id = self.after(1000, self.update_timer, controller)
        else:
            self.gathering = False
            self.sensor_display_running = False
            self.stop_serial()
            controller.show_frame(ClassificationPage)

    def stop_serial(self):
        self.sensor_display_running = False
        self.gathering = False
        if self.ser:
            close_serial(self.ser)
            self.ser = None

# ---------------- RUN APP ---------------- #
if __name__ == "__main__":
    app = App()
    app.mainloop()
