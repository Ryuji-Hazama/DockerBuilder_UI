import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.constants import *
import maplex
import os

import PIL._tkinter_finder

from statics import *
from core import BuildUp

class buildMenu:

    def __init__(self, root: ttk.Frame):

        # Logging setup
        self.logger = maplex.Logger(__name__)
        self.logger.info("Initializing Build Menu.")

        # Load configuration

        self.configFile = maplex.MapleJson("config.json")
        self.readConfig()

        self.root = root
        self.buildInstance = None
        self.options = {}

        self.logger.info("Build Menu initialized successfully.")

    def cleanForm(self):

        self.logger.debug("Cleaning form for fresh UI generation.")

        # Destroy all child widgets in the root frame
        for widget in self.root.winfo_children():
            widget.destroy()

    def setupValiables(self):
        
        self.logger.debug("Setting up application variables.")

        # Initialize any necessary variables here

        self.commonOptions = {}
        buildAllOption = {KEY_VALUE: ttk.BooleanVar(), KEY_REF: None}
        self.commonOptions[KEY_COM_BUILD_ALL] = buildAllOption

        self.variableDictionary = {}

        for image in self.imageList:

            imageName = image.get(KEY_NAME, "Unnamed Image")
            imageVarDict = {}
            buildDict = {KEY_VALUE: ttk.BooleanVar(), KEY_REF: None}
            deleteDict = {KEY_VALUE: ttk.BooleanVar(), KEY_REF: None}
            releaseDict = {KEY_VALUE: ttk.BooleanVar(), KEY_REF: None}
            packVolumesDict = {KEY_VALUE: ttk.BooleanVar(), KEY_REF: None}
            versionDict = {KEY_VALUE: ttk.StringVar(), KEY_REF: None}
            imageVarDict[KEY_BUILD] = buildDict
            imageVarDict[KEY_DELETE] = deleteDict
            imageVarDict[KEY_RELEASE] = releaseDict
            imageVarDict[KEY_PACK_VOLUMES] = packVolumesDict
            imageVarDict[KEY_VERSION] = versionDict
            self.variableDictionary[imageName] = imageVarDict

    def generateUI(self):

        self.logger.debug("Generating UI elements.")

        # Generate UI elements for build menu

        self.generateMasterToggles()
        self.generateImageCheckbuttons()
        self.generateButtons()

    def addEvents(self):

        self.logger.debug("Adding event handlers.")

        # Checkbutton checked event
        def on_checkbutton_change():
            build_all_selected = self.buildOptionButton.instate(['selected'])
            self.logger.debug(f"Build All option changed to: {build_all_selected}")

            # Enable/disable checkbuttons based on checkbutton selection

            if build_all_selected:
                checkButtonState = DISABLED
            else:
                checkButtonState = NORMAL

            for imageVarKey in self.variableDictionary:

                imageVarDict = self.variableDictionary[imageVarKey]

                if imageVarDict[KEY_BUILD][KEY_REF] is not None:

                    imageVarDict[KEY_BUILD][KEY_REF].config(state=checkButtonState)

                    if build_all_selected:
                        imageVarDict[KEY_BUILD][KEY_VALUE].set(True)

        self.buildOptionButton.config(command=on_checkbutton_change)

    def generateMasterToggles(self):

        form_frame = ttk.Frame(self.root)
        form_frame.pack(pady=10)

        # Check buttons for selecting build options
        self.buildOptionButton = ttk.Checkbutton(
            form_frame,
            text="Build All",
            variable=self.commonOptions[KEY_COM_BUILD_ALL][KEY_VALUE],
            bootstyle="primary-round-toggle"
        )
        self.buildOptionButton.grid(row=0, column=0, padx=10, pady=5)
        self.commonOptions[KEY_COM_BUILD_ALL][KEY_REF] = self.buildOptionButton

    def generateImageCheckbuttons(self):

        form_frame = ttk.Frame(self.root, padding=10)
        form_frame.pack(fill=X, expand=True, pady=10)
        frameStyleList = ["success.TFrame", "info.TFrame", "warning.TFrame"]

        # Checkbuttons for each images

        for index, image in enumerate(self.imageList):

            outerFrameStyle = frameStyleList[index % len(frameStyleList)]
            outerFrame = ttk.Frame(form_frame, style=outerFrameStyle, padding=1)
            outerFrame.pack(fill=X, pady=5)

            form_image_region = ttk.Frame(outerFrame, padding=5)
            form_image_region.pack(fill=BOTH, pady=0.1, padx=0.1)

            self.generateImageMasterbuttons(image, index, form_image_region)
            self.generateOptionsForImage(image, index, form_image_region)
            self.generateVersionEntry(image, index, form_image_region)

    def generateImageMasterbuttons(self, image: dict, index: int, root: ttk.Frame):
            
        currentVarDict = self.variableDictionary[image.get(KEY_NAME, f"Image {index+1}")]

        imageName = image.get(KEY_NAME, f"Image {index+1}")
        imageVar = currentVarDict[KEY_BUILD]
        checkButton = ttk.Checkbutton(
            root,
            text=imageName,
            variable=imageVar[KEY_VALUE]
        )
        checkButton.pack(side=TOP, anchor=W)
        imageVar[KEY_REF] = checkButton

    def generateOptionsForImage(self, image: dict, index: int, root: ttk.Frame):

        currentVarDict = self.variableDictionary[image.get(KEY_NAME, f"Image {index+1}")]

        form_image_options_region = ttk.Frame(root)
        form_image_options_region.pack(fill=X, pady=5)

        releaseCheckButton = ttk.Checkbutton(
            form_image_options_region,
            text="Build as Release",
            variable=currentVarDict[KEY_RELEASE][KEY_VALUE],
            bootstyle="danger-round-toggle"
        )
        releaseCheckButton.grid(row=0, column=0, sticky=W, padx=20, pady=5)
        currentVarDict[KEY_RELEASE][KEY_REF] = releaseCheckButton

        deleteCheckButton = ttk.Checkbutton(
            form_image_options_region,
            text="Delete Existing Image",
            variable=currentVarDict[KEY_DELETE][KEY_VALUE],
            bootstyle="warning-round-toggle"
        )
        deleteCheckButton.grid(row=0, column=1, sticky=W, padx=20, pady=5)
        currentVarDict[KEY_DELETE][KEY_REF] = deleteCheckButton

        imageVolumes = image.get(KEY_VOLUMES, [])

        if len(imageVolumes) > 0:

            packVolumesCheckButton = ttk.Checkbutton(
                form_image_options_region,
                text="Pack Volumes",
                variable=currentVarDict[KEY_PACK_VOLUMES][KEY_VALUE],
                bootstyle="info-round-toggle"
            )
            packVolumesCheckButton.grid(row=0, column=2, sticky=W, padx=20, pady=5)
            currentVarDict[KEY_PACK_VOLUMES][KEY_REF] = packVolumesCheckButton

        self.variableDictionary[image.get(KEY_NAME, f"Image {index+1}")] = currentVarDict

    def generateVersionEntry(self, image: dict, index: int, root: ttk.Frame):

        currentVarDict = self.variableDictionary[image.get(KEY_NAME, f"Image {index+1}")]

        form_image_version_region = ttk.Frame(root)
        form_image_version_region.pack(fill=X, pady=5)

        versionLabel = ttk.Label(form_image_version_region, text="Version:")
        versionLabel.grid(row=0, column=0, sticky=W, padx=20)

        currentVersion = image.get(KEY_VERSION, "")
        currentVarDict[KEY_VERSION][KEY_VALUE].set(currentVersion)

        versionEntry = ttk.Entry(
            form_image_version_region,
            textvariable=currentVarDict[KEY_VERSION][KEY_VALUE]
        )
        versionEntry.grid(row=0, column=1, sticky=W, padx=20)
        currentVarDict[KEY_VERSION][KEY_REF] = versionEntry

    def generateButtons(self):

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        build_button = ttk.Button(button_frame, text="Build", command=self.onBuildClick)
        build_button.grid(row=0, column=0, padx=10)

    def getBuildInstance(self):

        self.buildInstance = BuildUp(self.options, self.root)

    def gatherOptions(self):

        self.logger.debug("Gathering options from UI.")

        # Gather options for each image

        imageOptions = {}

        for imageName, imageVarDict in self.variableDictionary.items():

            buildOption = imageVarDict[KEY_BUILD][KEY_VALUE].get()
            deleteOption = imageVarDict[KEY_DELETE][KEY_VALUE].get()
            releaseOption = imageVarDict[KEY_RELEASE][KEY_VALUE].get()
            packVolumesOption = imageVarDict[KEY_PACK_VOLUMES][KEY_VALUE].get() if imageVarDict[KEY_PACK_VOLUMES][KEY_REF] is not None else False
            versionOption = imageVarDict[KEY_VERSION][KEY_VALUE].get()

            imageOptions[imageName] = {
                KEY_BUILD: buildOption,
                KEY_DELETE: deleteOption,
                KEY_RELEASE: releaseOption,
                KEY_PACK_VOLUMES: packVolumesOption,
                KEY_VERSION: versionOption
            }

        self.options[KEY_OP_IMAGES] = imageOptions
        self.options[KEY_OP_COMMON] = {
            KEY_COM_BUILD_ALL: self.commonOptions[KEY_COM_BUILD_ALL][KEY_VALUE].get()
        }

        self.buildAllSelected = self.options[KEY_OP_COMMON][KEY_COM_BUILD_ALL]

    def readConfig(self):

        self.config = self.configFile.read(KEY_OP_APPLICATION)
        self.imageList = self.config.get(KEY_OP_IMAGES, [])

    def onBuildClick(self):

        self.gatherOptions()
        self.getBuildInstance()
        self.buildInstance.startBuild()
        self.readConfig()
        self.show()

    def show(self):

        self.cleanForm()
        self.setupValiables()
        self.generateUI()
        self.addEvents()
