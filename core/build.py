import docker
import maplex
import os
import shutil

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from statics import *

import PIL._tkinter_finder

class BuildUp:

    def __init__(self, buildOptions: dict, root: ttk.Frame):

        # Logging setup
        self.logger = maplex.Logger(__name__)
        self.logger.info("Initializing BuildUp App.")

        self.configFile = maplex.MapleJson("config.json")
        self.config = self.configFile.read(KEY_OP_APPLICATION)
        self.confImageList = self.config.get(KEY_OP_IMAGES, [])
        self.updatedImageList = []

        self.loadOptions(buildOptions)
        self.root = root
        self.packagePath = self.config.get(KEY_OP_PACKAGE, {}).get(KEY_OUTPUT_DIRECTORY, "./packages")

        if not os.path.exists(self.packagePath):

            self.logger.debug(f"Package path {self.packagePath} does not exist. Creating directory.")
            os.makedirs(self.packagePath)

        self.logger.info("BuildUp App initialized successfully.")

    def loadOptions(self, buildOptions: dict):

        self.logger.debug("Loading options for BuildUp.")
        self.buildAll = buildOptions.get(KEY_COM_BUILD_ALL, False)
        self.imageOptions = buildOptions.get(KEY_OP_IMAGES, {})
        self.logger.debug(f"Options loaded: buildAll={self.buildAll}, imageOptions={self.imageOptions}")

    def startBuild(self):

        self.logger.info("Starting build process.")

        for imageConfig in self.confImageList:

            self.buildAndSaveImage(imageConfig)
            self.packageImage(imageConfig)
            self.updateImageConfig(imageConfig)

        self.updateConfig()

        if self.buildAll:
            
            self.logger.info("Build All option selected. Packaging all images.")
            self.packageAllImages()

    def buildAndSaveImage(self, imageConfig: dict):

        imageName = imageConfig.get(KEY_NAME, "Unnamed Image")
        baseImage = imageConfig.get(KEY_BASE_IMAGE, "UnknownBase")
        imageOptions = self.imageOptions.get(imageName, {})
        self.logger.debug(f"Processing image: {imageName}")

        if self.buildAll or imageOptions.get(KEY_BUILD, False):

            try:

                self.logger.info(f"Building image: {imageName}")
                contextPath = imageConfig.get(KEY_CONTEXT_PATH, ".")
                client = docker.from_env()

                def buildAndSave(latest=False):

                    # Build the image

                    tagVersion = "latest" if latest else imageOptions.get(KEY_VERSION, "latest")
                    fullImageName = f"{baseImage}:{tagVersion}"

                    self.logger.debug(f"Building image with context: {contextPath}, tag: {fullImageName}")
                    image, buildLogs = client.images.build(path=contextPath, tag=fullImageName, rm=True)
                    self.logger.info(f"Image {fullImageName} built successfully.")

                    # Save the image

                    packagePath = os.path.join(self.packagePath, f"{baseImage}_{tagVersion}.tar")
                    self.logger.debug(f"Saving image {fullImageName} to package path: {packagePath}")

                    with open(packagePath, "wb") as f:
                        for chunk in image.save(named=True):
                            f.write(chunk)

                    self.logger.info(f"Image {fullImageName} saved successfully at {packagePath}.")

            except Exception as e:

                self.logger.ShowError(e, f"Failed to build and save image {imageName}")
                Messagebox.show_error(f"Failed to build and save image {imageName}: {e}", "Build Error", parent=self.root)

            buildAndSave()
            buildAndSave(latest=True)

    def packageImage(self, imageConfig: dict):

        imageName = imageConfig.get(KEY_NAME, "Unnamed Image")
        baseImage = imageConfig.get(KEY_BASE_IMAGE, "UnknownBase")
        imageOptions = self.imageOptions.get(imageName, {})
        self.logger.info(f"Packaging image: {imageName}")

        if self.buildAll or imageOptions.get(KEY_BUILD, False) or imageOptions.get(KEY_PACK_VOLUMES, False):

            try:

                def package(latest=False):

                    tagVersion = "latest" if latest else imageOptions.get(KEY_VERSION, "latest")
                    savedImage = os.path.join(self.packagePath, f"{baseImage}_{tagVersion}.tar")
                    savePath = os.path.join(self.packagePath, f"{baseImage}_{tagVersion}")

                    if not os.path.exists(savePath):

                        os.makedirs(savePath)

                    if self.buildAll or imageOptions.get(KEY_BUILD, False):

                        shutil.move(savedImage, savePath)
                        self.logger.debug(f"Image {imageName} moved to {savePath} for packaging.")

                    if imageOptions.get(KEY_PACK_VOLUMES, False):

                        volumes = imageConfig.get(KEY_VOLUMES, [])
                        
                        for index, volume in enumerate(volumes):

                            volumePath = os.path.join(savePath, f"volume_{index}")
                            shutil.copytree(volume, volumePath)
                            self.logger.debug(f"Volume {volume} copied to {volumePath} for packaging.")

                    shutil.make_archive(savePath, 'gztar', savePath)
                    self.logger.info(f"Image {imageName} packaged successfully at {savePath}.tar.gz")

            except Exception as e:

                self.logger.ShowError(e, f"Failed to package image {imageName}")
                Messagebox.show_error(f"Failed to package image {imageName}: {e}", "Packaging Error", parent=self.root)

            package()
            package(latest=True)

    def updateImageConfig(self, imageConfig: dict):

        imageName = imageConfig.get(KEY_NAME, "Unnamed Image")
        imageOptions = self.imageOptions.get(imageName, {})
        self.logger.info(f"Updating config for image: {imageName}")

        if imageOptions.get(KEY_RELEASE, False):

            currentVersion = imageConfig.get(KEY_VERSION, "0.0.0")
            versionParts = currentVersion.split(".")

            versionParts[-1] = str(int(versionParts[-1]) + 1)
            newVersion = ".".join(versionParts)
            imageConfig[KEY_VERSION] = newVersion
            self.logger.debug(f"Image {imageName} version updated to {newVersion} in configuration.")

        self.updatedImageList.append(imageConfig)

    def updateConfig(self):

        try:

            self.logger.info("Updating configuration file with new image versions.")
            configData = self.configFile.read()
            configData[KEY_OP_APPLICATION][KEY_OP_IMAGES] = self.updatedImageList
            self.configFile.write(configData)
            self.logger.info("Configuration file updated successfully.")

        except Exception as e:

            self.logger.ShowError(e, "Failed to update configuration file with new image versions")
            Messagebox.show_error(f"Failed to update configuration file: {e}", "Configuration Update Error", parent=self.root)

    def packageAllImages(self):

        savePath = os.path.join(self.packagePath, "all_images")

        if not os.path.exists(savePath):

            os.makedirs(savePath)

        for imageConfig in self.confImageList:

            baseImage = imageConfig.get(KEY_BASE_IMAGE, "UnknownBase")
            packagePath = os.path.join(self.packagePath, f"{baseImage}_latest.tar.gz")

            if os.path.exists(packagePath):

                shutil.copy(packagePath, savePath)
                self.logger.debug(f"Image package {packagePath} copied to {savePath} for all images packaging.")

        shutil.make_archive(savePath, 'gztar', savePath)
        self.logger.info(f"All images packaged successfully at {savePath}.tar.gz")