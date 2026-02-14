import docker
import maplex
import os

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from statics import *

import PIL._tkinter_finder

class TestUp:

    def __init__(self, composeOptions: dict, root: ttk.Window):

        # Logging setup
        self.logger = maplex.Logger(__name__)
        self.logger.info("Initializing TestUp App.")

        self.configFile = maplex.MapleJson("config.json")
        self.config = self.configFile.read("ApplicationSettings")

        self.loadOptions(composeOptions)
        self.root = root

        self.logger.info("TestUp App initialized successfully.")

    def loadOptions(self, composeOptions: dict):

        self.logger.debug("Loading options for TestUp.")
        self.skipExisting = composeOptions.get(KEY_COM_SKIP_EXISTING, False)
        self.composeFilePath = composeOptions.get(KEY_COMPOSE_FILE_PATH, "./compose.yaml")
        self.composeCommand = composeOptions.get(KEY_COMPOSE_COMMAND, "docker-compose")
        self.logger.debug(f"Options loaded: skipExisting={self.skipExisting}, composeFilePath={self.composeFilePath}, composeCommand={self.composeCommand}")

    def checkDockerComposeFile(self):

        self.logger.debug("Checking for docker-compose file.")

        if not os.path.exists(self.composeFilePath):

            self.logger.error(f"Docker-compose file not found at path: {self.composeFilePath}")
            Messagebox.show_error("Docker Compose", f"Docker-compose file not found at path: {self.composeFilePath}", parent=self.root)
            return False

        self.logger.debug("Docker-compose file found.")
        return True

    def removeExistingContainers(self):

        self.logger.info("Removing existing test containers if any.")

        imageList = self.getImageListFromConfig()
        client = docker.from_env()
        
        for image in imageList:

            self.logger.debug(f"Checking for existing images with image: {image}")
            containerImages = client.images.list(all=True, filters={"reference": image})
            self.logger.debug(f"Found {len(containerImages)} images with image {image}.")
            
            for image in containerImages:

                self.logger.info(f"Removing image {image.id} with image {image}")

                try:

                    image.remove(force=True)
                    self.logger.info(f"Image {image.id} removed successfully.")

                except Exception as e:

                    self.logger.error(f"Failed to remove image {image.id}: {e}")

    def runDockerComposeUp(self):
        
        command = f"{self.composeCommand} -f {self.composeFilePath} up -d"
        self.logger.info(f"Running command: {command}")
        os.system(command)
        Messagebox.show_info("Docker process started.", "Docker Compose", parent=self.root)
        self.logger.info("Docker-compose up process initiated.")

    def runDockerComposeDown(self):

        command = f"{self.composeCommand} -f {self.composeFilePath} down"
        self.logger.info(f"Running command: {command}")
        os.system(command)
        Messagebox.show_info("Docker process stopped.", "Docker Compose", parent=self.root)
        self.logger.info("Docker-compose down process initiated.")

    def getImageListFromConfig(self):

        self.logger.debug("Retrieving image list from configuration.")

        images = self.config.get("Images", [])
        imageList = [image.get("BaseImage", "") for image in images]
        self.logger.debug(f"Image list retrieved: {imageList}")

        return imageList
        
    def up(self):

        self.logger.info("Starting docker-compose up process.")
        
        if not self.checkDockerComposeFile():
            return

        if not self.skipExisting:

            self.removeExistingContainers()

        self.runDockerComposeUp()

    def down(self):

        self.logger.info("Starting docker-compose down process.")
        
        if not self.checkDockerComposeFile():
            return

        self.runDockerComposeDown()

# Instance getter for TestUp

testUpInstance = {}

def getTestUpInstance(name, composeOptions: dict, root: ttk.Window):
    if name not in testUpInstance:
        testUpInstance[name] = TestUp(composeOptions, root)
    return testUpInstance[name]