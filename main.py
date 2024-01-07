import os
import ctypes
import tkinter as tk
from tkinter import messagebox
import traceback

from multiprocessing import Queue, Process

from PIL import Image, PngImagePlugin  # type: ignore
from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore

HINT_WATING = "请拖拽PNG文件(们)到这里\nDrag and drop PNG file(s) here"


def clear_png(png_path: str):
    """Remove unnecessary PNG metadata."""

    if not os.path.exists(png_path):
        raise FileNotFoundError(f"{png_path} not found")

    name, suffix = os.path.splitext(png_path)
    save_path = name + "_clear" + suffix

    # Pillow supports limited basic metadata.
    # We can use it to reduce the size of the PNG file.

    with Image.open(png_path) as img:
        pnginfo = PngImagePlugin.PngInfo()
        for key, value in img.info.items():
            pnginfo.add_text(str(key), str(value))

        # Save
        try:
            img.save(save_path, pnginfo=pnginfo)
        except:
            data = list(img.getdata())
            image_without_metadata = Image.new(img.mode, img.size)
            image_without_metadata.putdata(data)
            image_without_metadata.save(save_path)

    return save_path

class ConverResult:
    def __init__(self, success: bool, msg: str):
        self.success = success
        self.msg = msg

    def is_success(self):
        return self.success


def worker(inq, outq):
    while True:
        path = inq.get()
        try:
            cleared_path = clear_png(path)
            outq.put(ConverResult(True, cleared_path))
        except Exception as e:
            outq.put(ConverResult(
                False, 
                f"Convert {path} failed\n{traceback.format_exc()}"
            ))


class ClearHandler:
    def __init__(self, label, windows):
        self.label = label
        self.windows = windows

        self.inq = Queue()
        self.outq = Queue()
        self.process = Process(target=worker, args=(self.inq, self.outq))
        self.process.start()

        self.num_processing = 0
        self.check()

    def add(self, path: str):
        self.num_processing += 1
        self.hint()
        self.inq.put(path)

    def add_files(self, event_data: str):
        files = str(event_data).strip('{}').split('} {')
        files = [file.replace(r'/', "\\") for file in files]
        for file in files:
            self.add(file)

    def check(self):
        while not self.outq.empty():
            result = self.outq.get()
            self.num_processing -= 1
            self.hint()
            if not result.is_success():
                messagebox.showerror("转换错误 Convert Error", f"\n{result.msg}")
        self.windows.after(500, self.check)
        

    def hint(self):
        if self.num_processing > 0:
            cn_hint = f"正在处理{self.num_processing}个文件，您可以继续添加文件"
            en_hint = f"Processing {self.num_processing} files, you can continue to add files"
            self.label.config(text=f"{cn_hint}\n{en_hint}")
        else:
            self.label.config(text=HINT_WATING)

    def stop(self):
        self.process.terminate()


g_handler: ClearHandler | None = None


def on_drop(event):
    """Handle file drop event"""
    global g_handler
    assert g_handler is not None
    g_handler.add_files(event.data)


def gui():
    "A GUI wich has a area where you can drag and drop the png file"

    # Create the main window
    root = TkinterDnD.Tk()
    root.title("PNG瘦身工具")
    root.geometry("360x260")

    file_dir = os.path.dirname(os.path.realpath(__file__))
    root.iconbitmap(os.path.join(file_dir, "icon.ico"))

    # Create a label with instructions
    label = tk.Label(
        root,
        text=HINT_WATING,
        padx=100,
        pady=100
    )
    label.pack()

    # Start clear process
    global g_handler
    g_handler = ClearHandler(label, root)

    # Enable file dropping
    label.drop_target_register(DND_FILES)  # type: ignore
    label.dnd_bind('<<Drop>>', on_drop)    # type: ignore

    # Run the application
    root.mainloop()

    # Stop clear process
    g_handler.stop()


if __name__ == "__main__":

    # Auto scale GUI on Windows
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    gui()
