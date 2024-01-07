import os
import ctypes
import tkinter as tk
from tkinter import messagebox

from PIL import Image
from tkinterdnd2 import DND_FILES, TkinterDnD  # type: ignore

HINT_WATING = "请拖拽PNG文件(们)到这里\nDrag and drop PNG file(s) here"

label = None


def clear_png(png_path: str):
    """Remove unnecessary PNG metadata."""

    if not os.path.exists(png_path):
        raise FileNotFoundError(f"{png_path} not found")

    name, suffix = os.path.splitext(png_path)
    save_path = name + "_clear" + suffix

    # Pillow supports limited basic metadata.
    # We can use it to reduce the size of the PNG file.

    img = Image.open(png_path)
    img.save(save_path, quality=100, **img.info)  
    return save_path


def parse_dropped_files(data: str):
    """Parse the dropped file paths from tkinterdnd2 event data."""
    files = data.strip('{}').split('} {')
    return [file.replace(r'/', "\\") for file in files]


def hint_processing(parsed_files: list[str]):
    """Show a hint of processing"""
    global label
    num_files = len(parsed_files)
    cn_hint = f"正在处理{num_files}个文件，请稍后..."
    en_hint = f"Processing {num_files} files, please waitint..."
    assert label is not None
    label.config(text=f"{cn_hint}\n{en_hint}")
    label.update()


def on_drop(event):
    """Handle file drop event"""
    global label
    assert label is not None

    parsed_files = parse_dropped_files(event.data)
    hint_processing(parsed_files)
    try:
        parsed_files = parse_dropped_files(event.data)
        cleared_paths = [
            clear_png(file)
            for file in parse_dropped_files(event.data)
        ]
        messagebox.showinfo(
            "成功 Success",
            f"{parsed_files}"
        )
    except Exception as e:
        # Show an error message
        messagebox.showerror("错误 Error", f"\n{e}")
    finally:
        label.config(text=HINT_WATING)


def gui():
    "A GUI wich has a area where you can drag and drop the png file"

    # Create the main window
    root = TkinterDnD.Tk()
    root.title("PNG瘦身工具")
    root.geometry("360x260")

    file_dir = os.path.dirname(os.path.realpath(__file__))
    root.iconbitmap(os.path.join(file_dir, "icon.ico"))

    # Create a label with instructions
    global label
    label = tk.Label(
        root,
        text=HINT_WATING,
        padx=100,
        pady=100
    )
    label.pack()

    # Enable file dropping
    label.drop_target_register(DND_FILES)  # type: ignore
    label.dnd_bind('<<Drop>>', on_drop)    # type: ignore

    # Run the application
    root.mainloop()


if __name__ == "__main__":

    # Auto scale GUI on Windows
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    gui()
