import tkinter as tk
from tkinter import ttk
import random
from PIL import Image, ImageTk

LABELFONT = ("Segoe UI", 16, "bold")
TEXTFONT = ("Segoe UI", 20, "bold")
BUTTONFONT = ("Segoe UI", 22)
CONDIMENTS = ["Soy Sauce", "Fish Sauce", "Oyster Sauce", "Worcestershire Sauce"]

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        container = tk.Frame(self)
        container.pack(fill ="both", expand =True)
        container.grid_rowconfigure(0, weight =1)
        container.grid_columnconfigure(0, weight =1)
        style = ttk.Style()
        style.configure("TButton", font=BUTTONFONT, padding=10)
        
        self.frames={}
        for F in (StartPage, BaselineReadingPage, ClassificationPage, ClassificationReadingPage, ResultPage):
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

        self.bg_image = Image.open("background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=60, anchor="n", width=700, height=50)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="Gather Baseline Data to Start",
                                font=TEXTFONT, fill="white")

        button1 = ttk.Button(self.canvas, text="Start", style="TButton",
                             command=lambda: [controller.show_frame(BaselineReadingPage),
                                              controller.frames[BaselineReadingPage].start_timer(controller)])
        self.canvas.create_window(400, 280, window=button1)

class BaselineReadingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        self.bg_image = Image.open("background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=60, anchor="n", width=700, height=50)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")
        self.canvas.create_text(400, 200, text="PROCESS: Gathering Baseline Data....",
                                font=TEXTFONT, fill="white")

        self.timer_text_id = self.canvas.create_text(400, 260, text="1:00",
                                                     font=TEXTFONT, fill="WHITE")

        self.remaining_time = 60

    def start_timer(self, controller):
        self.remaining_time = 60
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


class ClassificationPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.bg_image = Image.open("background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=60, anchor="n", width=700, height=50)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="Please place the Sample Inside the Chamber",
                                font=TEXTFONT, fill="white")

        button1 = ttk.Button(self.canvas, text="Start Classifying", style="TButton",
                             command=lambda: [controller.show_frame(ClassificationReadingPage),
                                              controller.frames[ClassificationReadingPage].start_timer(controller)])
        self.canvas.create_window(400, 260, window=button1)


class ClassificationReadingPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.bg_image = Image.open("background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=60, anchor="n", width=700, height=50)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        self.canvas.create_text(400, 200, text="PROCESS: Gathering Data....",
                                font=TEXTFONT, fill="white")

        self.timer_text_id = self.canvas.create_text(400, 260, text="10:00",
                                                     font=TEXTFONT, fill="WHITE")

        self.remaining_time = 600

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
            controller.show_frame(ResultPage) 


class ResultPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.bg_image = Image.open("background.png")
        self.bg_image = self.bg_image.resize((800, 480), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        self.canvas = tk.Canvas(self, width=800, height=480, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        title_frame = tk.Frame(self, bg="white", bd=0, relief="flat")
        title_frame.place(relx=0.5, y=60, anchor="n", width=700, height=50)

        title_label = tk.Label(title_frame,
                               text="SVM Dark Condiment Classification using E-Nose",
                               font=LABELFONT, bg="white")
        title_label.pack(expand=True, fill="both")

        result = random.choice(CONDIMENTS)
        self.canvas.create_text(400, 200, text=f"RESULT: {result}",
                font=TEXTFONT, fill="orange")

        button1 = ttk.Button(self.canvas, text="Restart", style="TButton",
                             command=lambda: controller.show_frame(ClassificationPage))
        self.canvas.create_window(400, 260, window=button1)
        

if __name__ == "__main__":
    app = App()
    app.geometry("800x480")
    app.resizable(False, False)
    app.mainloop()