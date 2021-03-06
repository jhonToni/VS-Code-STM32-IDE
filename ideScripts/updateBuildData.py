'''
Update/generate 'buildData.json' file in '.vscode' subfolder from new Makefile.
New Makefile is not updated by this script - it is updated with 'updateMakefile.py' or 'updateWorkspaceSources.py'
'''
import json
import datetime

import utilities as utils
import templateStrings as tmpStr

import updatePaths as pth
import updateMakefile as mkf
import updateWorkspaceSources as wks

__version__ = utils.__version__


class BuildDataStrings():
    cSources = 'cSources'
    asmSources = 'asmSources'

    cIncludes = 'cIncludes'
    asmIncludes = 'asmIncludes'

    cDefines = 'cDefines'
    asmDefines = 'asmDefines'

    cFlags = 'cFlags'
    asmFlags = 'asmFlags'

    buildDirPath = 'buildDir'

    gccInludePath = 'gccInludePath'
    gccExePath = 'gccExePath'

    buildToolsPath = 'buildToolsPath'
    targetExecutablePath = 'targetExecutablePath'

    openOCDPath = 'openOCDPath'
    openOCDTargetPath = 'openOCDTargetPath'
    openOCDInterfacePath = 'openOCDInterfacePath'

    stm32svdPath = 'stm32svdPath'

    cubeMxProjectPath = 'cubeMxProjectPath'


class BuildData():
    def __init__(self):
        self.mkfStr = mkf.MakefileStrings()
        self.cPStr = wks.CPropertiesStrings()
        self.bStr = BuildDataStrings()

    def checkBuildDataFile(self):
        '''
        Check if 'buildData.json' file exists. If it does, check if it is a valid JSON file.
        If it doesn't exist, create new according to template.
        '''
        if utils.fileFolderExists(utils.buildDataPath):
            # file exists, check if it loads OK
            try:
                with open(utils.buildDataPath, 'r') as buildDataFile:
                    data = json.load(buildDataFile)

                    print("Existing 'buildData.json' file found.")

            except Exception as err:
                errorMsg = "Invalid 'buildData.json' file. Creating new one. Error:\n"
                errorMsg += "Possible cause: invalid json format or comments (not supported by this scripts). Error:\n"
                errorMsg += str(err)
                print(errorMsg)

                self.createBuildDataFile()

        else:  # 'buildData.json' file does not exist jet, create it according to template string
            self.createBuildDataFile()
            print("New 'buildData.json' file created.")

    def createBuildDataFile(self):
        '''
        Create fresh 'buildData.json' file.
        '''
        try:
            with open(utils.buildDataPath, 'w') as buildDataFile:
                data = json.loads(tmpStr.buildDataTemplate)
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)

                buildDataFile.seek(0)
                buildDataFile.truncate()
                buildDataFile.write(dataToWrite)

                print("New 'buildData.json' file created.")

        except Exception as err:
            errorMsg = "Exception error creating new 'buildData.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)

    def getBuildData(self):
        '''
        Get data from current 'buildData.json' file.
        File existance is previoulsy checked in 'checkBuildDataFile()'.
        '''
        with open(utils.buildDataPath, 'r') as buildDataFile:
            data = json.load(buildDataFile)

        return data

    def addMakefileDataToBuildDataFile(self, buildData, makefileData):
        '''
        This function fills buildData.json file with data from 'Makefile'.
        Returns new data.
        '''
        # sources
        cSources = makefileData[self.mkfStr.cSources]
        buildData[self.bStr.cSources] = cSources

        asmSources = makefileData[self.mkfStr.asmSources]
        buildData[self.bStr.asmSources] = asmSources

        # includes
        cIncludes = makefileData[self.mkfStr.cIncludes]
        buildData[self.bStr.cIncludes] = cIncludes

        asmIncludes = makefileData[self.mkfStr.asmIncludes]
        buildData[self.bStr.asmIncludes] = asmIncludes

        # defines
        cDefines = makefileData[self.mkfStr.cDefines]
        buildData[self.bStr.cDefines] = cDefines

        asmDefines = makefileData[self.mkfStr.asmDefines]
        buildData[self.bStr.asmDefines] = asmDefines

        # compiler flags and paths
        cFlags = makefileData[self.mkfStr.cFlags]
        buildData[self.bStr.cFlags] = cFlags

        asmFlags = makefileData[self.mkfStr.asmFlags]
        buildData[self.bStr.asmFlags] = asmFlags

        # build folder must be always inside workspace folder
        buildDirPath = makefileData[self.mkfStr.buildDir]
        buildData[self.bStr.buildDirPath] = buildDirPath

        # Target executable '.elf' file
        projectName = makefileData[self.mkfStr.projectName]
        targetExecutablePath = utils.getBuildElfFilePath(buildDirPath, projectName)
        buildData[self.bStr.targetExecutablePath] = targetExecutablePath

        return buildData

    def addCubeMxProjectPathToBuildData(self, buildData):
        '''
        If utils.cubeMxProjectFilePath is not None, add/update 'cubeMxProjectPath' field to 'buildData.json'.
        '''
        if utils.cubeMxProjectFilePath is not None:
            buildData[self.bStr.cubeMxProjectPath] = utils.cubeMxProjectFilePath
        return buildData

    def overwriteBuildDataFile(self, data):
        '''
        Overwrite existing 'buildData.json' file with new data.
        '''
        try:
            with open(utils.buildDataPath, 'r+') as buildDataFile:
                data["VERSION"] = __version__
                data["LAST_RUN"] = str(datetime.datetime.now())

                buildDataFile.seek(0)
                buildDataFile.truncate()
                dataToWrite = json.dumps(data, indent=4, sort_keys=False)
                buildDataFile.write(dataToWrite)

            print("'buildData.json' file updated!")

        except Exception as err:
            errorMsg = "Exception error overwriting 'buildData.json' file:\n"
            errorMsg += str(err)
            utils.printAndQuit(errorMsg)


########################################################################################################################
if __name__ == "__main__":
    utils.verifyFolderStructure()

    paths = pth.UpdatePaths()
    makefile = mkf.Makefile()
    bData = BuildData()

    # Makefile must exist
    makefile.checkMakefileFile()  # no point in continuing if Makefile does not exist

    # build data (update tools paths if neccessary)
    bData.checkBuildDataFile()
    buildData = bData.getBuildData()
    if not paths.verifyExistingPaths(buildData):
        buildData = paths.forceUpdatePaths(buildData)
    makeExePath = buildData[bData.bStr.buildToolsPath]
    gccExePath = buildData[bData.bStr.gccExePath]

    # data from current Makefile
    makefileData = makefile.getMakefileData(makeExePath, gccExePath)

    # try to add CubeMX project file path
    buildData = bData.addCubeMxProjectPathToBuildData(buildData)

    buildData = bData.addMakefileDataToBuildDataFile(buildData, makefileData)
    bData.overwriteBuildDataFile(buildData)
