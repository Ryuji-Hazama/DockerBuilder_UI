import docker
import maplex
import os
import shutil
import threading

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox

from statics import *
from ui.dialog import ProgressWindow

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
        self.client = docker.from_env()
        self.builtImageList = []
        self.packagePath = self.config.get(KEY_OP_PACKAGE, {}).get(KEY_OUTPUT_DIRECTORY, "./packages")

        if not os.path.exists(self.packagePath):

            self.logger.debug(f"Package path {self.packagePath} does not exist. Creating directory.")
            os.makedirs(self.packagePath)
            self.changeOwnership(self.packagePath)

        self.logger.info("BuildUp App initialized successfully.")

    def loadOptions(self, buildOptions: dict):

        self.logger.debug("Loading options for BuildUp.")
        self.commonOptions = buildOptions.get(KEY_OP_COMMON, {})
        self.buildAll = self.commonOptions.get(KEY_COM_BUILD_ALL, False)
        self.imageOptions = buildOptions.get(KEY_OP_IMAGES, {})
        self.logger.debug(f"Options loaded: buildAll={self.buildAll}, imageOptions={self.imageOptions}")

    def startBuild(self):

        self.logger.info("Starting build process.")
        steps = len(self.confImageList) * 6 + [1, 2][self.buildAll]
        self.progressWindow = ProgressWindow("Building Images", steps)

        thread = threading.Thread(target=self.processBuild)
        thread.start()
        self.progressWindow.master.wait_window(self.progressWindow)

        #thread.join()

        Messagebox.show_info("Build process completed successfully!", "Build Complete", parent=self.root)
        self.logger.info("Build process completed successfully.")

    def processBuild(self):

        for imageConfig in self.confImageList:

            self.buildImage(imageConfig)
            self.updateImageConfig(imageConfig)

        self.saveImages()
        self.packageImages()
        self.updateConfig()

        if self.buildAll:

            self.logger.info("Build All option selected. Packaging all images.")
            self.packageAllImages()

        self.progressWindow.IncrementProgress("Build process completed.", 0.5)
        self.progressWindow.closeWindow()

    def buildImage(self, imageConfig: dict):

        imageName = imageConfig.get(KEY_NAME, "Unnamed Image")
        baseImage = imageConfig.get(KEY_BASE_IMAGE, "UnknownBase")
        imageOptions = self.imageOptions.get(imageName, {})
        packageVolumes = imageOptions.get(KEY_PACK_VOLUMES, False)
        packageVolumeList = imageConfig.get(KEY_VOLUMES, []) if packageVolumes else []
        packageVersion = imageOptions.get(KEY_VERSION, "latest")
        self.logger.debug(f"Processing image: {imageName}")

        if imageOptions.get(KEY_DELETE, False):

            self.logger.info(f"Delete option selected for image: {imageName}. Attempting to remove existing images with base image {baseImage}.")

            try:

                self.deleteOldPackages(baseImage)

            except Exception as e:

                self.logger.ShowError(e, f"Failed to delete old packages for image {imageName}")
                Messagebox.show_error(f"Failed to delete old packages for image {imageName}: {e}", "Delete Error", parent=self.root)

        if self.buildAll or imageOptions.get(KEY_BUILD, False):

            try:

                self.logger.info(f"Building image: {imageName}")
                contextPath = imageConfig.get(KEY_CONTEXT_PATH, ".")

                def buildAndSave(latest=True):

                    # Build the image

                    tagVersion = "latest" if latest else packageVersion
                    fullImageName = f"{baseImage}:{tagVersion}"
                    self.progressWindow.IncrementProgress(f"Processing image: {fullImageName}", 1)

                    self.logger.debug(f"Building image with context: {contextPath}, tag: {fullImageName}")
                    self.client.images.build(path=contextPath, tag=fullImageName, rm=True)
                    self.logger.info(f"Image {fullImageName} built successfully.")

                    # Save the image to temporary list

                    packagePath = os.path.join(self.packagePath, f"{baseImage}_{tagVersion}")
                    packageSet = [imageName, packagePath, fullImageName, packageVolumes, packageVolumeList]
                    self.builtImageList.append(packageSet)
                    self.progressWindow.IncrementProgress(stepCount=1)

            except Exception as e:

                self.logger.ShowError(e, f"Failed to build and save image {imageName}")
                Messagebox.show_error(f"Failed to build and save image {imageName}: {e}", "Build Error", parent=self.root)

            buildAndSave()

            if imageOptions.get(KEY_RELEASE, False):

                self.logger.info(f"Release option selected for image: {imageName}.")
                buildAndSave(False)

            else:

                self.progressWindow.IncrementProgress(stepCount=2)

        else:

            self.logger.info(f"Skipping build for image: {imageName} as it is not selected.")
            packagePath = os.path.join(self.packagePath, f"{baseImage}_latest")
            self.builtImageList.append([imageName, packagePath, None, packageVolumes, packageVolumeList])  # Add placeholder for packaging step

            if imageOptions.get(KEY_RELEASE, False):

                packagePath = os.path.join(self.packagePath, f"{baseImage}_{packageVersion}")
                self.builtImageList.append([imageName, packagePath, None, packageVolumes, packageVolumeList])  # Add placeholder for packaging step

            self.progressWindow.IncrementProgress(stepCount=4)

    def saveImages(self):

        for packageSet in self.builtImageList:

            try:

                imageName, packagePath, imageName, _, _ = packageSet

                if packagePath.endswith("_latest"):

                    self.progressWindow.IncrementProgress(f"Saving image {imageName}...", 1)

                # Get image object from Docker client

                if imageName is not None:

                    image = self.client.images.get(imageName)

                else:

                    image = None

                if image is not None:

                    tarPath = f"{packagePath}.tar"
                    self.logger.debug(f"Saving image {imageName} to temporary tar file {tarPath}")

                    with open(tarPath, 'wb') as f:
                        for chunk in image.save(named=True):
                            f.write(chunk)

                    self.logger.info(f"Image {imageName} saved successfully at {tarPath}")

                    if not packagePath.endswith("_latest"):

                        self.logger.info("Deleting non-latest image as release option is selected.")
                        self.client.images.remove(image=imageName, force=True)
                        self.logger.debug(f"Image {imageName} removed successfully after saving.")

            except Exception as e:

                self.logger.ShowError(e, f"Failed to save image {imageName}")
                Messagebox.show_error(f"Failed to save image {imageName}: {e}", "Save Error", parent=self.root)

    def packageImages(self):

        self.logger.info("Start packaging images")

        for packageSet in self.builtImageList:

            try:

                imageName, packagePath, image, packageVolumes, packageVolumeList = packageSet
                self.logger.info(f"Packaging image: {imageName} with package path: {packagePath}")

                if packagePath.endswith("_latest"):

                    self.progressWindow.IncrementProgress(f"Packaging image {imageName}...", 1)

                if image is None and not packageVolumes:

                    self.logger.info(f"No new image to package for {imageName} and no volumes to pack. Skipping packaging.")
                    continue

                if not os.path.exists(packagePath):

                    os.makedirs(packagePath)

                shutil.move(f"{packagePath}.tar", packagePath)
                self.logger.debug(f"Image tar moved to package path {packagePath} for image {imageName}.")

                if packageVolumes:

                    self.logger.info(f"Packing volumes for image: {imageName}")
                    self.progressWindow.IncrementProgress(f"Packing volumes for image {imageName}...", 0)
                    manufestPath = os.path.join(packagePath, "manifest.txt")

                    for index, volume in enumerate(packageVolumeList):

                        if os.path.exists(volume):

                            volumePackagePath = os.path.join(packagePath, f"volume_{index}")
                            
                            if not os.path.exists(volumePackagePath):

                                os.makedirs(volumePackagePath)

                            if os.path.isdir(volume):

                                baseDirName = os.path.basename(volume)
                                shutil.copytree(volume, os.path.join(volumePackagePath, baseDirName))

                            else:

                                shutil.copy2(volume, volumePackagePath)

                            with open(manufestPath, 'a') as manifestFile:
                                manifestFile.write(f"volume_{index}:{volume}\n")

                            self.logger.debug(f"Volume {volume} copied to {volumePackagePath} for image {imageName}.")

                self.createArchive(packagePath)
                self.logger.info(f"Image {imageName} packaged successfully at {packagePath}.tar.gz")

            except Exception as e:

                self.logger.ShowError(e, f"Failed to package image {imageName}")
                Messagebox.show_error(f"Failed to package image {imageName}: {e}", "Packaging Error", parent=self.root)

    def deleteOldPackages(self, baseImage: str):

        for file in os.listdir(self.packagePath):

            if file.startswith(f"{baseImage}_") and file.endswith(".tar.gz"):

                filePath = os.path.join(self.packagePath, file)
                os.remove(filePath)
                self.logger.debug(f"Old package {filePath} deleted for image {baseImage}.")

    def changeOwnership(self, filePath: str):

        ownershipConfig = self.config.get(KEY_OP_PACKAGE, {}).get(KEY_OP_OWNERSHIP, {})
        user = ownershipConfig.get(KEY_OP_USER, None)
        group = ownershipConfig.get(KEY_OP_GROUP, None)

        if user is not None and group is not None:

            shutil.chown(filePath, user=user, group=group)
            self.logger.debug(f"Ownership of {filePath} changed to user: {user}, group: {group}.")

        else:

            self.logger.warn(f"Ownership information not fully specified in configuration. Skipping ownership change for {filePath}.")

    def createArchive(self, directory: str):

        self.logger.debug(f"Creating archive for directory {directory}.")
        self.progressWindow.IncrementProgress(f"Creating archive for {directory}...", 0)
        archivePath = f"{directory}.tar.gz"
        shutil.make_archive(directory, 'gztar', directory)
        shutil.rmtree(directory)
        self.changeOwnership(archivePath)
        self.logger.info(f"Directory {directory} archived successfully at {archivePath}.")

    def updateImageConfig(self, imageConfig: dict):

        imageName = imageConfig.get(KEY_NAME, "Unnamed Image")
        imageOptions = self.imageOptions.get(imageName, {})
        self.logger.info(f"Updating config for image: {imageName}")

        if imageOptions.get(KEY_RELEASE, False):

            currentVersion = imageOptions.get(KEY_VERSION, "0.0.0")
            versionParts = currentVersion.split(".")

            versionParts[-1] = str(int(versionParts[-1]) + 1)
            newVersion = ".".join(versionParts)
            imageConfig[KEY_VERSION] = newVersion
            self.logger.debug(f"Image {imageName} version updated to {newVersion} in configuration.")

        self.updatedImageList.append(imageConfig)

    def updateConfig(self):

        self.logger.debug("Updating configuration file with new image versions.")
        self.progressWindow.IncrementProgress("Updating configuration file...", 0.5)

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
        self.progressWindow.IncrementProgress("Packaging all images...", 1)

        if not os.path.exists(savePath):

            os.makedirs(savePath)

        for imageConfig in self.confImageList:

            baseImage = imageConfig.get(KEY_BASE_IMAGE, "UnknownBase")
            packagePath = os.path.join(self.packagePath, f"{baseImage}_latest.tar.gz")

            if os.path.exists(packagePath):

                shutil.copy(packagePath, savePath)
                self.logger.debug(f"Image package {packagePath} copied to {savePath} for all images packaging.")

        self.createArchive(savePath)
        self.logger.info(f"All images packaged successfully at {savePath}.tar.gz")