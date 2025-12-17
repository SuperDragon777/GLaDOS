import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import sys

import subrunner
import hw
import limiter
hw.write()
subrunner.run("limiter.py")

debug_esc_close = True
glados_img_path = "img/glados.png"
right_offset = 20


root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "white")


glados_img = Image.open(glados_img_path)
glados_photo = ImageTk.PhotoImage(glados_img)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()


img_width = glados_img.width
img_height = glados_img.height


x = screen_width - img_width - right_offset
root.geometry(
    f"{img_width}x{img_height}+{x}+{0}"
    )

label = tk.Label(
    root,
    image=glados_photo,
    bg='white'
    )
label.pack()

def stop_all():
    subrunner.stop_all()
    root.destroy()
    sys.exit(0)

if debug_esc_close:
    root.bind("<Escape>", lambda e: stop_all())

root.mainloop()