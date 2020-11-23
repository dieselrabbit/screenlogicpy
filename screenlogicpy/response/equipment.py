from .utility import getSome, getArray

#pylint: disable=unused-variable
def decode(buff):
    controlerType, offset = getSome("B", buff, 0)
    hardwareType, offset = getSome("B", buff, offset)

    skip1, offset = getSome("B", buff, offset)
    skip2, offset = getSome("B", buff, offset)
    controlerData, offset = getSome("I", buff, offset)

    versionDataArray, offset = getArray(buff, offset)
    speedDataArray, offset =  getArray(buff, offset)
    valveDataArray, offset =  getArray(buff, offset)
    remoteDataArray, offset =  getArray(buff, offset)
    sensorDataArray, offset =  getArray(buff, offset)
    delayDataArray, offset =  getArray(buff, offset)
    macrosDataArray, offset =  getArray(buff, offset)
    miscDataArray, offset =  getArray(buff, offset)
    lightDataArray, offset =  getArray(buff, offset)
    flowsDataArray, offset =  getArray(buff, offset)
    sgsDataArray, offset =  getArray(buff, offset)
    spaFlowsDataArray, offset =  getArray(buff, offset)