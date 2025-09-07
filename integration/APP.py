import tkinter as tk
from tkinter import ttk
import random
import serial, time, csv
import pandas as pd
import joblib
import os
import numpy as np
from PIL import Image, ImageTk

LABELFONT = ("Segoe UI", 16, "bold")
TEXTFONT = ("Segoe UI", 20, "bold")
BUTTONFONT = ("Segoe UI", 22, "bold")
EBUTTONFONT = ("Segoe UI", 16, "bold")
RESULTFONT = ("Segoe UI", 30, "bold")
CONDIMENTS = ["Soy Sauce", "Fish Sauce", "Oyster Sauce", "Worcestershire Sauce"]

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.attributes('-fullscreen', True)
        self.bind('<Escape>', lambda e: self.attributes('-fullscreen', False))
        container = tk.Frame(self)
        container.pack(fill ="both", expand =True)
        container.grid_rowconfigure(0, weight =1)
        container.grid_columnconfigure(0, weight =1)
        style = ttk.Style()
        style.configure("TButton", font=BUTTONFONT, padding=10)
        style.configure("Exit.TButton", font=EBUTTONFONT, padding=4)
        
        self.frames={}
        for F in (StartPage, ClassificationPage, ClassificationReadingPage, ResultPage, ExhaustPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row = 0 , column = 0, sticky ="nsew")
        
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.bg_image = Image.open("integration/background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="Press Start to Begin!",
                                font=TEXTFONT, fill="white")

        button1 = ttk.Button(self.canvas, text="Start", style="TButton",
                             command=lambda: [controller.show_frame(ClassificationPage),
                                              controller.frames[ClassificationPage].start_timer(controller)])
        self.canvas.create_window(400, 280, window=button1)

        exit_button = ttk.Button(self.canvas, text="Exit", style="Exit.TButton", command=controller.quit)
        self.canvas.create_window(700, 430, window=exit_button)

class ClassificationPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.bg_image = Image.open("integration/background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="Please place the Sample Inside the Chamber",
                                font=TEXTFONT, fill="white")

        button1 = ttk.Button(self.canvas, text="Start Classifying", style="TButton",
                             command=lambda: [controller.show_frame(ClassificationReadingPage),
                                              controller.frames[ClassificationReadingPage].start_timer(controller)])
        self.canvas.create_window(400, 280, window=button1)

        exit_button = ttk.Button(self.canvas, text="Exit", style="Exit.TButton", command=controller.quit)
        self.canvas.create_window(700, 430, window=exit_button)



class ClassificationReadingPage(tk.Frame):
    #def gather_data(self, filename="gathered_data.csv", port="/dev/ttyACM0", baud=9600): ## Change port kung ano compatible
    def gather_data(self, filename="gathered_data.csv", port="COM3", baud=9600):
        self.gathering = True
        header = ["MQ2", "MQ3", "MQ135", "MQ136", "MQ137", "MQ138"]
        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                self.gather_start_time = time.time()
                while self.gathering and (time.time() - self.gather_start_time < 600):
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        values = line.split(",")
                        if len(values) == 6:
                            writer.writerow(values)
            # After gathering, calculate mean for each sensor and overwrite the file
            df = pd.read_csv(filename)
            means = df[header].astype(float).mean()
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerow(list(means))
        except Exception as e:
            print(f"Error during data gathering: {e}")
        finally:
            if self.ser:
                try: self.ser.close()
                except: pass

    def skip_and_save(self):
    # 1) Cancel the timer tick if scheduled
        if getattr(self, "_timer_after_id", None) is not None:
            try:
                self.after_cancel(self._timer_after_id)
            except Exception:
                pass
            self._timer_after_id = None

        # 2) Stop and join the gather thread so the file is closed
        self.gathering = False
        if self.gather_thread and self.gather_thread.is_alive():
            self.gather_thread.join(timeout=2)

        # 3) Save the mean to gathered_data.csv
        try:
            header = ["MQ2", "MQ3", "MQ135", "MQ136", "MQ137", "MQ138"]
            if os.path.exists("gathered_data.csv"):
                df = pd.read_csv("gathered_data.csv")
                if not df.empty:
                    means = df[header].astype(float).mean()
                    with open("gathered_data.csv", "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(header)
                        writer.writerow(list(means))
                else:
                    print("Skip pressed: gathered_data.csv is empty—nothing to average.")
            else:
                print("Skip pressed: gathered_data.csv does not exist yet.")
        except Exception as e:
            print(f"Error saving data on skip: {e}")

        # 4) Reflect stopped state and go to results
        self.canvas.itemconfig(self.timer_text_id, text="Stopped")
        self.controller.show_frame(ResultPage)



    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.gathering = False
        self.gather_thread = None
        self.bg_image = Image.open("integration/background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="PROCESS: Gathering Data....",
                                font=TEXTFONT, fill="white")

        exit_button = ttk.Button(self.canvas, text="Exit", style="Exit.TButton", command=controller.quit)
        self.canvas.create_window(700, 430, window=exit_button)

        next_button = ttk.Button(self.canvas, text="skip", style="TButton", command=self.skip_and_save)
        self.canvas.create_window(400, 320, window=next_button) ## Para pang check lang ng panels will be removed later on

        self.timer_text_id = self.canvas.create_text(400, 250, text="10:00",
                                 font=TEXTFONT, fill="WHITE")
        self.remaining_time = 600

    


    def start_timer(self, controller):
        self.remaining_time = 600
        import threading
        self.gathering = True
        self.gather_thread = threading.Thread(target=self.gather_data, daemon=True)
        self.gather_thread.start()
        self.update_timer(controller)

    def update_timer(self, controller):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        formatted_time = f"{minutes}:{seconds:02d}"

        self.canvas.itemconfig(self.timer_text_id, text=formatted_time)

        if self.remaining_time > 0 and self.gathering:
            self.remaining_time -= 1
            # store the after id so we can cancel it on skip
            self._timer_after_id = self.after(1000, self.update_timer, controller)
        else:
            # stop gathering if time is up (or we've been stopped)
            self.gathering = False
            if self.gather_thread and self.gather_thread.is_alive():
                self.gather_thread.join(timeout=2)
            self.canvas.itemconfig(self.timer_text_id, text="Done...")
            controller.show_frame(ResultPage)



class ResultPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.bg_image = Image.open("integration/background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        # Load mean sensor data
        try:
            data = pd.read_csv("gathered_data.csv").values[0]
            model = joblib.load("svm_best_model.joblib")
            # Reshape for prediction (1, 6)
            pred = model.predict(np.array(data).reshape(1, -1))[0]
            result = pred
        except Exception as e:
            result = f"Error: {e}"

        color_map = {
            "Soy Sauce": "#F79503",         #placeholders for their colors
            "Fish Sauce": "#F79503",        
            "Oyster Sauce": "#F79503",      
            "Worcestershire Sauce": "#F79503", 
        }
        
        result_color = color_map.get(str(result), "orange")
        self.canvas.create_text(400, 200, text=f"RESULT: {result}",
                font=RESULTFONT, fill=result_color)

        button1 = ttk.Button(self.canvas, text="Restart", style="TButton", 
                             command=lambda: [controller.show_frame(ExhaustPage),
                                              controller.frames[ExhaustPage].start_timer(controller)])
        
        self.canvas.create_window(400, 300, window=button1)

        exit_button = ttk.Button(self.canvas, text="Exit", style="Exit.TButton", command=controller.quit)
        self.canvas.create_window(700, 430, window=exit_button)

class ExhaustPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bg_image = Image.open("integration/background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=70, anchor="n", width=550, height=45)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="PROCESS: Exhaustion in Progress",
                                font=TEXTFONT, fill="white")
        
        exit_button = ttk.Button(self.canvas, text="Exit", style="Exit.TButton", command=controller.quit)
        self.canvas.create_window(700, 430, window=exit_button)

        self.timer_text_id = self.canvas.create_text(400, 250, text="10:00",
                                                     font=TEXTFONT, fill="WHITE")

        self.remaining_time = 600

        next_button = ttk.Button(self.canvas, text="skip", style="TButton", command=lambda: controller.show_frame(ClassificationPage))
        self.canvas.create_window(400, 320, window=next_button) ## Para pang check lang ng panels will be removed later on


    def start_timer(self, controller):
        self.remaining_time = 600
        self.update_timer(controller)

    def update_timer(self, controller):
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        formatted_time = f"{minutes}:{seconds:02d}"

        self.canvas.itemconfig(self.timer_text_id, text=formatted_time)

        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.after(1000, self.update_timer, controller)
        else:
            self.canvas.itemconfig(self.timer_text_id, text="Done...")
            controller.show_frame(ClassificationPage) 
        

if __name__ == "__main__":
    app = App()
    app.geometry("800x480")
    app.resizable(False, False)
    app.mainloop()