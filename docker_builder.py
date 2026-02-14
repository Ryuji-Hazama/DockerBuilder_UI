import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
import maplex
import os
import shutil

import PIL._tkinter_finder

# Static key names
KEY_NAME = "Name"
KEY_BUILD = "Build"
KEY_DELETE = "Delete"
KEY_BUILD_REF = "BuildRef"
KEY_DELETE_REF = "DeleteRef"
KEY_OPTIONS = "Options"

KEY_COM_SKIP_EXISTING = "SkipExisting"

KEY_OP_IMAGES = "Images"
KEY_OP_COMMON = "CommonOptions"


class dockerBuilder:

    def __init__(self):

        # Logging setup
        self.logger = maplex.Logger(__name__)
        self.logger.info("Initializing Docker Builder App.")

        # Load configuration

        self.configFile = maplex.MapleJson("config.json")
        self.config = self.configFile.read("ApplicationSettings")
        self.imageList = self.config.get("Images", [])

        # Main window setup
        self.root = ttk.Window("Docker Builder", "superhero")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        self.root.attributes("-zoomed", True)  # Start maximized

        self.setupVariables()
        self.setup_ui()
        self.addEvents()

        self.logger.info("Docker Builder App initialized successfully.")

    def setupVariables(self):

        self.logger.debug("Setting up application variables.")

        # Initialize any necessary variables here

        self.commonOptions = {}
        self.commonOptions[KEY_COM_SKIP_EXISTING] = ttk.BooleanVar()

        self.variableDictionary = {}

        for image in self.imageList:

            imageName = image.get(KEY_NAME, "Unnamed Image")
            imageVarDict = {}
            imageVarDict[KEY_BUILD] = ttk.BooleanVar()
            imageVarDict[KEY_BUILD_REF] = None
            imageVarDict[KEY_DELETE] = ttk.BooleanVar()
            imageVarDict[KEY_DELETE_REF] = None
            self.variableDictionary[imageName] = imageVarDict

    def setup_ui(self):

        try:

            self.logger.info("Setting up UI elements.")

            self.generateTitle()
            self.generateForm()
            self.generateButtons()

            self.logger.info("UI elements set up successfully.")

        except Exception as e:

            self.logger.ShowError(e, "Failed to set up UI elements", True)

    def addEvents(self):

        self.logger.debug("Adding event handlers.")

        # Radio buttons checked event
        def on_radio_change():
            selected_option = self.build_option.get()
            self.logger.debug(f"Build option changed to: {selected_option}")

            # Enable/disable checkbuttons based on radio selection

            if selected_option == "All":
                checkButtonState = DISABLED
            else:
                checkButtonState = NORMAL

            for imageVarKey in self.variableDictionary:

                imageVarDict = self.variableDictionary[imageVarKey]

                if imageVarDict[KEY_BUILD_REF] is not None:

                    imageVarDict[KEY_BUILD_REF].config(state=checkButtonState)

        self.build_option.trace_add("write", lambda *args: on_radio_change())

    def generateTitle(self):

        self.logger.debug("Generating title label.")

        title = ttk.Label(self.root, text="Docker Builder", font=("Helvetica", 24))
        title.pack(pady=20)

    def generateForm(self):

        self.logger.debug("Generating form elements.")

        self.generateMasterToggles()
        self.generateImageCheckbuttons()
        self.generateSkipExistingCheckbox()

    def generateMasterToggles(self):

        form_frame = ttk.Frame(self.root)
        form_frame.pack(pady=10)

        # Radio buttons (All/Selected)
        self.build_option = ttk.StringVar(value="Selected")
        selected_radio = ttk.Radiobutton(
            form_frame,
            text="Build Selected Images",
            variable=self.build_option,
            value="Selected"
        )
        all_radio = ttk.Radiobutton(
            form_frame,
            text="Build All Images",
            variable=self.build_option,
            value="All"
        )
        selected_radio.grid(row=0, column=0, padx=10, pady=5)
        all_radio.grid(row=0, column=1, padx=10, pady=5)

    def generateImageCheckbuttons(self):

        form_frame = ttk.Frame(self.root)
        form_frame.pack(pady=10)

        # Checkbuttons for each images

        for index, image in enumerate(self.imageList):

            currentVarDict = self.variableDictionary[image.get(KEY_NAME, f"Image {index+1}")]

            form_image_region = ttk.Frame(form_frame)
            form_image_region.grid(row=index+1, column=0, sticky=W)

            imageName = image.get(KEY_NAME, f"Image {index+1}")
            imageVar = currentVarDict[KEY_BUILD]
            checkButton = ttk.Checkbutton(form_image_region, text=imageName, variable=imageVar)
            checkButton.grid(row=0, column=0, sticky=W, padx=20, pady=5)
            currentVarDict[KEY_BUILD_REF] = checkButton

            form_image_options_region = ttk.Frame(form_frame)
            form_image_options_region.grid(row=index+1, column=1, sticky=W)

            deleteCheckButton = ttk.Checkbutton(
                form_image_options_region,
                text="Delete Existing Image",
                variable=currentVarDict[KEY_DELETE]
            )
            deleteCheckButton.grid(row=0, column=0, sticky=W, padx=20, pady=5)
            currentVarDict[KEY_DELETE_REF] = deleteCheckButton

            self.variableDictionary[image.get(KEY_NAME, f"Image {index+1}")] = currentVarDict

    def generateSkipExistingCheckbox(self):

        self.logger.debug("Generating 'Skip Existing Images' checkbox.")

        form_frame = ttk.Frame(self.root)
        form_frame.pack(pady=10)

        # Skip existing images checkbox
        skip_existing_chk = ttk.Checkbutton(
            form_frame,
            text="Skip Existing Images",
            variable=self.commonOptions[KEY_COM_SKIP_EXISTING]
        )
        skip_existing_chk.grid(row=0, column=0, sticky=W, padx=10, pady=5)

    def generateButtons(self):

        self.logger.debug("Generating action buttons.")

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=20)

        build_button = ttk.Button(
            button_frame,
            text="Build",
            command=self.build_images,
            bootstyle=SUCCESS
        )
        test_button = ttk.Button(
            button_frame,
            text="Test",
            command=self.test_images,
            bootstyle=INFO
        )
        exit_button = ttk.Button(
            button_frame,
            text="Exit",
            command=self.quitApp,
            bootstyle=DANGER
        )
        build_button.grid(row=0, column=0, padx=10)
        test_button.grid(row=0, column=1, padx=10)
        exit_button.grid(row=0, column=2, padx=10)

    def build_images(self):

        self.logger.info("Build button clicked. Starting build process.")

        buildOptions = {KEY_OP_IMAGES: [], KEY_OP_COMMON: {}}

        # Gather selected images

        for imageVarDictkey in self.variableDictionary:

            imageVarDict = self.variableDictionary[imageVarDictkey]
            
            if imageVarDict[KEY_BUILD].get():

                imageOptions = {
                    KEY_NAME: imageVarDictkey,
                    KEY_DELETE: imageVarDict[KEY_DELETE].get()
                }
                buildOptions[KEY_OP_IMAGES].append(imageOptions)

        # Gather common options

        commonOptions = {
            KEY_COM_SKIP_EXISTING: self.commonOptions[KEY_COM_SKIP_EXISTING].get()
        }
        buildOptions[KEY_OP_COMMON] = commonOptions

        self.logger.debug(f"Build options gathered: {buildOptions}")

    def test_images(self):

        pass  # Placeholder for test logic

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
            #Messagebox.show_error("This application must be run as root.", title="Permission Error")
            #self.logger.fatal("Application not run as root. Exiting.")
            #return False
            pass    # For development purposes, we will allow non-root execution. Remove this pass and uncomment the above lines for production.
        
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