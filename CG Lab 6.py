import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk


def affine(image, scale, restore=False):
    factor = scale if restore else 1 / scale
    cx, cy = image.width / 2, image.height / 2
    coefficients = (-factor, 0, cx * (1 + factor), 0, factor, cy * (1 - factor))
    return image.transform(
        image.size, Image.Transform.AFFINE, coefficients,
        resample=Image.Resampling.NEAREST, fillcolor="white",
    )


def exponential(image):
    width, height = image.size
    if width == 1:
        return image.copy()

    span = width - 1
    columns = [round(span * math.log1p(math.expm1(1) * x / span)) for x in range(width)]
    pixels = image.load()
    result = Image.new("RGB", image.size)
    result.putdata([pixels[x, y] for y in range(height) for x in columns])
    return result


class LabWindow:
    def __init__(self, root):
        self.root = root
        root.title("Form1")
        root.geometry("842x562")
        root.resizable(False, False)
        root.configure(bg="#eeeeee")

        self.images = {}
        self.previews = {}
        self.panels = {}
        self.applied_scale = None
        for name, x, y in (
            ("source", 16, 20), ("affine", 504, 20),
            ("restored", 16, 304), ("nonlinear", 504, 304),
        ):
            panel = tk.Label(root, bg="#eeeeee", bd=0, anchor="nw",
                             highlightthickness=1, highlightbackground="#999999")
            panel.place(x=x, y=y, width=320, height=240)
            self.panels[name] = panel

        self.dimensions = tk.Label(root, bg="#eeeeee", font=("Tahoma", 8))
        self.dimensions.place(x=176, y=0, anchor="n")
        self.button("Открыть", 17, self.open_image)
        tk.Label(root, text="Масштаб", bg="#eeeeee").place(x=361, y=91)
        self.scale_entry = ttk.Entry(root)
        self.scale_entry.insert(0, "0.5")
        self.scale_entry.place(x=423, y=89, width=60, height=23)
        self.button("Аффинные", 121, self.apply_affine)
        self.button("Сохранить", 236, lambda: self.save("affine"))
        self.button("Обратно", 305, self.restore)
        self.button("Сохранить", 337, lambda: self.save("restored"))
        self.button("Нелинейные", 417, self.apply_nonlinear)
        self.button("Сохранить", 520, lambda: self.save("nonlinear"))

    def button(self, text, y, command):
        ttk.Button(self.root, text=text, command=command).place(
            x=370, y=y, width=102, height=23
        )

    def show(self, name, image):
        preview = image.copy()
        preview.thumbnail((320, 240), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(preview, master=self.root)
        self.panels[name].configure(image=photo, highlightthickness=0)
        self.previews[name] = photo
        self.images[name] = image

    def clear(self, name):
        self.panels[name].configure(image="", highlightthickness=1)
        self.previews.pop(name, None)
        self.images.pop(name, None)

    def open_image(self):
        path = filedialog.askopenfilename(
            parent=self.root, title="Открыть изображение",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp"),
                       ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            messagebox.showerror("Ошибка чтения", str(error), parent=self.root)
            return

        self.show("source", image)
        self.dimensions.configure(text=f"{image.width} × {image.height}")
        for name in ("affine", "restored", "nonlinear"):
            self.clear(name)
        self.applied_scale = None

    def apply_affine(self):
        if "source" not in self.images:

            return
        try:
            scale = float(self.scale_entry.get().replace(",", "."))
            if not math.isfinite(scale) or scale <= 0 or not math.isfinite(1 / scale):
                raise ValueError
        except (ValueError, OverflowError):

            return

        self.show("affine", affine(self.images["source"], scale))
        self.applied_scale = scale
        self.clear("restored")

    def restore(self):
        if "affine" not in self.images:

            return
        self.show("restored", affine(self.images["affine"], self.applied_scale, restore=True))

    def apply_nonlinear(self):
        if "source" not in self.images:

            return
        self.show("nonlinear", exponential(self.images["source"]))

    def save(self, name):
        if name not in self.images:

            return
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Сохранить изображение", defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")],
        )
        if path:
            try:
                self.images[name].save(path)
            except (OSError, ValueError) as error:
                messagebox.showerror("Ошибка записи", str(error), parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    LabWindow(root)
    root.mainloop()
