import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.constants import *
import maplex
import os
import shutil

import PIL._tkinter_finder

from statics import *
from ui.menu import *

class dockerBuilder:

    def __init__(self):

        # Logging setup
        self.logger = maplex.Logger(__name__)
        self.logger.info("Initializing Docker Builder App.")

        # Main window setup
        self.root = ttk.Window("Docker Builder", "superhero")
        self.root.geometry("800x500")
        self.root.resizable(True, True)
        self.root.attributes("-zoomed", True)  # Start maximized

        # UI instance variables

        self.buildMenuInstance = None
        self.testMenuInstance = None

        self.setup_ui()

        self.logger.info("Docker Builder App initialized successfully.")

    def setup_ui(self):

        try:

            self.logger.info("Setting up UI elements.")

            self.generateSidePanel()
            self.generateMainPanel()
            self.onBuildClick()  # Show build menu by default

            self.logger.info("UI elements set up successfully.")

        except Exception as e:

            self.logger.ShowError(e, "Failed to set up UI elements", True)

    def generateSidePanel(self):

        left_f = ttk.Frame(self.root, width=200)
        left_f.pack(side=LEFT, fill=BOTH)

        mb_builder = ttk.Button(
            left_f,
            text="Build",
            command=self.onBuildClick,
            bootstyle="link-primary",
            width=10
        )
        mb_builder.pack(fill=X, padx=10, pady=5)

        mb_tester = ttk.Button(
            left_f,
            text="Test",
            command=self.onTestClick,
            bootstyle="link-success",
            width=10
        )
        mb_tester.pack(fill=X, padx=10, pady=5)

        quit_button = ttk.Button(
            left_f,
            text="Quit",
            command=self.quitApp,
            bootstyle="danger"
        )
        quit_button.pack(fill=X, padx=10, pady=5, side=BOTTOM)

    def generateMainPanel(self):

            self.main_frame = ttk.Frame(self.root, border=1, relief="solid")
            self.main_frame.pack(side=RIGHT, fill=BOTH, expand=True)

            self.generateTitle()
            self.generateMainFrame()

    def generateTitle(self):

        title_f = ttk.Frame(self.main_frame)
        title_f.pack(side=TOP, pady=10)

        title_label = ttk.Label(title_f, text="Docker Builder", font=("Helvetica", 24))
        title_label.pack()

    def generateMainFrame(self):

        self.menu_frame = ScrolledFrame(self.main_frame)
        self.menu_frame.pack(side=BOTTOM, fill=BOTH, expand=True, padx=5, pady=5)

    def onBuildClick(self):

        self.logger.info("Build button clicked.")

        if not self.buildMenuInstance:
            self.buildMenuInstance = buildMenu(self.menu_frame)
        
        self.buildMenuInstance.show()

    def onTestClick(self):

        self.logger.info("Test button clicked.")

        if not self.testMenuInstance:
            self.testMenuInstance = testMenu(self.menu_frame)
        
        self.testMenuInstance.show()

    def quitApp(self):

        self.logger.info("Exiting Docker Builder App.")
        self.root.quit()

    def checkUnix(self):

        if os.name != "posix":

            # Show error dialog
            Messagebox.show_error("This application is designed to run on Unix-like systems.\nWe say no to Microsoft.", title="Unsupported OS")
            self.logger.fatal("Unsupported operating system. Exiting.")
            return False

        return True 

    def checkRoot(self):

        if os.geteuid() != 0:

            # Show error dialog
            Messagebox.show_error("This application must be run as root.", title="Permission Error")
            self.logger.fatal("Application not run as root. Exiting.")
            return False
            #pass    # For development purposes, we will allow non-root execution. Remove this pass and uncomment the above lines for production.
        
        return True

    def checkDocker(self):

        self.logger.info("Checking for Docker installation.")

        if not shutil.which("docker"):

            Messagebox.show_error("Docker is not installed or not found in PATH.", title="Docker Not Found")
            self.logger.fatal("Docker not found. Exiting.")
            return False
        
        self.logger.info("Docker installation found.")
        return True

    def run(self):

        self.logger.info("Running Docker Builder App.")
        self.root.mainloop()

if __name__ == "__main__":

    app = dockerBuilder()
    if app.checkUnix() and app.checkRoot() and app.checkDocker():
        app.run()