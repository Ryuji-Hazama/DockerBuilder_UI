import maplex
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

import PIL._tkinter_finder

class ProgressWindow(ttk.Frame):

    def __init__(self, titleMessage: str, steps: int):

        # Logging objects

        self.logger = maplex.Logger(__name__)

        self.master = ttk.Toplevel(titleMessage, resizable=(False, False), topmost=True)

        super().__init__(self.master, padding=(10, 10))
        self.pack(fill=BOTH, expand=YES)

        self.labelContainer = ttk.Frame(self)
        self.labelContainer.pack(fill=X, expand=YES)

        self.messageLb = ttk.Label(self.labelContainer, text="Requesting...")
        self.messageLb.pack(fill=X, expand=YES)

        progressContainer = ttk.Frame(self, padding=(30, 0))
        progressContainer.pack(fill=X, expand=YES)

        self.progressBar = ttk.Progressbar(
            progressContainer,
            bootstyle=SUCCESS,
            mode=DETERMINATE,
            length=200,
            maximum=steps,
            value=0
        )
        self.progressBar.pack(pady=10)

        self.logger.info("Progress window loaded.")

        self.master.grab_set()

    def PackLabel(self, messageText):

        self.messageLb.destroy()
        self.messageLb = ttk.Label(self.labelContainer, text=messageText)
        self.messageLb.pack(fill=X, expand=YES)

    def IncrementProgress(self, stepMessage: str | None = None, stepCount: float = 1.0):

        if stepMessage is not None:
            self.PackLabel(stepMessage)

        self.progressBar.step(stepCount)
        self.logger.trace(f"Progress incremented. Current value: {self.progressBar['value']} / {self.progressBar['maximum']}")

    def closeWindow(self):

        self.master.destroy()