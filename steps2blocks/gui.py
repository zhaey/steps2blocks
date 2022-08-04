import shutil
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

from convert import beatmap_from_sm
from smmap import load_sm


class FilePicker(ttk.Frame):

    def __init__(
            self,
            master,
            title: str,
            button_text: str,
            filetypes=None,
            **kwargs
    ):
        super().__init__(master, **kwargs)

        self.title = ttk.Label(self, text=title)
        self.path_value = tk.StringVar(self)
        self.path_entry = ttk.Entry(self, textvariable=self.path_value, state='readonly', width=64)
        self.button = ttk.Button(self, text=button_text, command=self.pick_file)

        self.filetypes = filetypes

        self.title.grid(column=0, row=0, sticky="w")
        self.path_entry.grid(column=0, row=1, sticky="we")
        self.button.grid(column=1, row=1, sticky="w", padx=(5, 0))

        self.columnconfigure(0, weight=1)

    def pick_file(self) -> None:
        path_str = filedialog.askopenfilename(
            parent=self,
            filetypes=self.filetypes
        )
        if path_str:
            self.path_value.set(path_str)


class IntPicker(ttk.Frame):

    def __init__(
            self,
            master,
            title: str,
            unit_text: str,
            init_value: int = 0,
            **kwargs
    ):
        super().__init__(master, **kwargs)

        validate_wrapper = (self.register(self.validate), "%P")

        self.title = ttk.Label(self, text=title)
        self.int_value = tk.StringVar(self, value=str(init_value))
        self.int_entry = ttk.Entry(self, textvariable=self.int_value, width=6, validatecommand=validate_wrapper,
                                   validate="key")
        self.unit_label = ttk.Label(self, text=unit_text)

        self.title.grid(column=0, row=0, sticky="w")
        self.int_entry.grid(column=0, row=1, sticky="we")
        self.unit_label.grid(column=1, row=1, sticky="w", padx=2)

        self.columnconfigure(0, weight=1)

    @staticmethod
    def validate(new_val: str):
        try:
            int(new_val)
        except ValueError:
            return False


class GUI(ttk.Frame):

    def __init__(self, *args, **kwargs):
        if 'padding' not in kwargs:
            kwargs['padding'] = (5, 5, 12, 12)
        super().__init__(*args, **kwargs)

        self.sm_path_picker = FilePicker(self, "Stepmania file:", "load .sm",
                                         (("sm4 chart", ".sm"),
                                          ("any", ".*")))
        self.sample_rate_picker = IntPicker(self, "Sample rate:", "Hz", 44100)
        self.song_length_picker = IntPicker(self, "Song length:", "s", 600)
        self.convert_button = ttk.Button(self, text="Convert", command=self.do_convert)

        self.sm_path_picker.grid(column=0, row=0, columnspan=5, sticky="we")
        self.sample_rate_picker.grid(column=0, row=5, sticky="w")
        self.song_length_picker.grid(column=1, row=5, sticky="w")
        self.convert_button.grid(column=4, row=5, sticky="e")

        self.rowconfigure("all", pad=5)
        self.columnconfigure("all", pad=5)
        self.columnconfigure(4, weight=1)

        self.master.bind("<Control-o>", lambda e: self.sm_path_picker.button.invoke())
        self.master.bind("<Control-s>", lambda e: self.convert_button.invoke())

    def do_convert(self) -> None:
        failure_str = "Conversion failed"
        sm_path = self.sm_path_picker.path_value.get()
        if not sm_path:
            messagebox.showerror(failure_str, "No .sm file selected!")
            return

        try:
            sm_song = load_sm(sm_path)
        except Exception as e:
            messagebox.showerror(failure_str, f"An exception was raised while loading your Stepmania chart:\n{e}")
            return

        sample_rate = int(self.sample_rate_picker.int_value.get())
        sample_count = int(self.song_length_picker.int_value.get()) * sample_rate
        try:
            bs_song = beatmap_from_sm(sm_song, sample_count, sample_rate)
        except Exception as e:
            messagebox.showerror(failure_str, f"An exception was raised during conversion:\n{e}")
            return

        output_path = filedialog.askdirectory(mustexist=False, title="Choose where to save your Beat Saber map")
        if not output_path:
            return

        try:
            bs_song.save_to_disk(output_path)
        except Exception as e:
            messagebox.showerror(failure_str, f"An exception was raised while trying to save your converted map:\n{e}")
            return

        try:
            sm_song_path = Path(sm_path).parent / sm_song.music_path
            if sm_song_path.is_file():
                bs_song_path = Path(output_path) / bs_song.song_filename
                if not bs_song_path.exists():
                    shutil.copy(sm_song_path, bs_song_path)
        except Exception as e:
            messagebox.showerror(failure_str, f"An exception was raised while trying to copy the audio:\n{e}")
            return

        messagebox.showinfo("Success!", "Chart has been converted")


def open_gui():
    root = tk.Tk()
    root.title("Steps2Blocks by Zhaey")
    root.attributes('-type', 'utility')
    gui = GUI(root)
    gui.grid(column=0, row=0, sticky="nwes")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.bind("<Escape>", lambda _: root.destroy())
    root.mainloop()


if __name__ == "__main__":
    open_gui()
