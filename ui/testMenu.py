import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
import maplex

from statics import *
from core import *

class testMenu:

    def __init__(self, root: ttk.Frame):

        # Logging setup
        self.root = root
        self.logger = maplex.Logger(__name__)
        self.logger.info("Initializing Test Menu.")

        # Load configuration

        self.configFile = maplex.MapleJson("config.json")
        self.config = self.configFile.read("ApplicationSettings")

        # Test instance variables

        self.testInstance = None

        # Setup variables

        self.refOptions = {}
        self.setValiables()

    def setValiables(self):

        self.logger.debug("Setting up test application variables.")

        skipExisting = {KEY_VALUE: ttk.BooleanVar(), KEY_REF: None}
        runButton = {KEY_VALUE: None, KEY_REF: None}
        stopButton = {KEY_VALUE: None, KEY_REF: None}

        self.refOptions[KEY_COM_SKIP_EXISTING] = skipExisting
        self.refOptions[KEY_BUTTON_RUN] = runButton
        self.refOptions[KEY_BUTTON_STOP] = stopButton

    def cleanForm(self):

        self.logger.debug("Cleaning form for fresh UI generation.")

        # Destroy all child widgets in the root frame
        for widget in self.root.winfo_children():
            widget.destroy()

    def generateUI(self):

        self.logger.debug("Generating UI elements.")

        self.generateCheckboxes()
        self.generateButtons()

    def generateCheckboxes(self):

        checkbox_frame = ttk.Frame(self.root)
        checkbox_frame.pack(pady=10)

        skip_existing_checkbox = ttk.Checkbutton(
            checkbox_frame,
            text="Skip Existing",
            variable=self.refOptions[KEY_COM_SKIP_EXISTING][KEY_VALUE]
        )
        skip_existing_checkbox.grid(row=0, column=0, padx=10)
        self.refOptions[KEY_COM_SKIP_EXISTING][KEY_REF] = skip_existing_checkbox

    def generateButtons(self):

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        test_button = ttk.Button(
            button_frame,
            text="Run Tests",
            command=self.onTestClick,
            bootstyle="success"
        )
        test_button.grid(row=0, column=0, padx=10)
        self.refOptions[KEY_BUTTON_RUN][KEY_REF] = test_button
        stop_button = ttk.Button(
            button_frame,
            text="Stop Tests",
            command=self.stopTests,
            bootstyle="warning-outline"
        )
        stop_button.grid(row=0, column=1, padx=10)
        self.refOptions[KEY_BUTTON_STOP][KEY_REF] = stop_button

    def getTestInstance(self):

        if self.testInstance is None:

            self.testInstance = TestUp(self.options, self.root)

    def onTestClick(self):

        self.logger.info("Test button clicked.")
        testButton = self.refOptions[KEY_BUTTON_RUN][KEY_REF]
        testButton.config(state=DISABLED)

        # Get options

        self.options = {
            KEY_COM_SKIP_EXISTING: self.refOptions[KEY_COM_SKIP_EXISTING][KEY_VALUE].get(),
            KEY_COMPOSE_FILE_PATH: self.config.get("BuildSettings", {}).get("ComposeFilePath", "./compose.yaml"),
            KEY_COMPOSE_COMMAND: self.config.get("BuildSettings", {}).get("ComposeCommand", "docker-compose")
        }

        # Run tests

        self.getTestInstance()
        self.testInstance.up()
        testButton.config(state=NORMAL)

    def stopTests(self):

        self.logger.info("Stop Tests button clicked.")
        stopButton = self.refOptions[KEY_BUTTON_STOP][KEY_REF]
        stopButton.config(state=DISABLED)

        if self.testInstance:

            self.testInstance.down()
            self.testInstance = None

        else:

            self.logger.warn("No test instance found to stop.")
            Messagebox.show_warning("No test instance is currently running.", "Stop Tests", parent=self.root)

        stopButton.config(state=NORMAL)

    def show(self):

        self.cleanForm()
        self.generateUI()