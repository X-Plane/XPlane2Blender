def compare(refMat, mat, exportType):
    if exportType == 'scenery':
        return compareScenery(refMat, mat)
    elif exportType == 'instanced_scenery':
        return compareInstanced(refMat, mat)
    elif exportType == 'cockpit' or exportType == 'aircraft':
        return compareAircraft(refMat, mat)

def compareScenery(refMat, mat):
    errors = []

    if mat.texture != refMat.texture:
        errors.append('Texture must be %s.' % refMat.texture)

    if mat.textureLit != refMat.textureLit:
        errors.append('Lit/Emissive texture must be %s.' % refMat.textureLit)

    if mat.textureNormal != refMat.textureNormal:
        errors.append('Normal/Alpha/Specular texture must be %s.' % refMat.textureNormal)

    return errors

def compareInstanced(refMat, mat):
    errors = []

    if mat.texture != refMat.texture:
        errors.append('Texture must be %s.' % refMat.texture)

    if mat.textureLit != refMat.textureLit:
        errors.append('Lit/Emissive texture must be %s.' % refMat.textureLit)

    if mat.textureNormal != refMat.textureNormal:
        errors.append('Normal/Alpha/Specular texture must be %s.' % refMat.textureNormal)

    if mat.options.overrideSpecularity:
        if mat.options.shinyRatio != refMat.options.shinyRatio:
            errors.append('Specularity must be %f.' % refMat.options.shinyRatio)
    elif mat.blenderMaterial.specular_intensity != refMat.blenderMaterial.specular_intensity:
        errors.append('Specularity must be %f.' % refMat.blenderMaterial.specular_intensity)

    if mat.options.blend != refMat.options.blend:
        if refMat.options.blend:
            errors.append('Alpha cutoff must be enabled.')
        else:
            errors.append('Alpha cutoff must be disabled.')
    elif mat.options.blendRatio != refMat.options.blendRatio:
        errors.append('Alpha cutoff ratio must be %f' % refMat.options.blendRatio)

    return errors

def compareAircraft(refMat, mat):
    errors = []

    if mat.texture != refMat.texture:
        errors.append('Texture must be %s.' % refMat.texture)

    if mat.textureLit != refMat.textureLit:
        errors.append('Lit/Emissive texture must be %s.' % refMat.textureLit)

    if mat.textureNormal != refMat.textureNormal:
        errors.append('Normal/Alpha/Specular texture must be %s.' % refMat.textureNormal)

    return errors


def validate(mat, exportType):
    errors = []

    if mat.options == None:
        errors.append('Is invalid.')
        return errors

    if exportType == 'scenery':
        return validateScenery(mat)
    elif exportType == 'instanced_scenery':
        return validateInstanced(mat)
    elif exportType == 'cockpit' and mat.options.panel:
        return validatePanel(mat)
    elif exportType == 'cockpit' and not mat.options.panel:
        return validateCockpit(mat)
    elif exportType == 'aircraft':
        return validateAircraft(mat)
    elif (exportType == 'scenery' or exportType == 'instanced_scenery') and mat.options.draped:
        return validateDraped(mat)

    return errors

def validateScenery(mat):
    errors = []

    if mat.options.panel:
        errors.append('Must not be part of the cockpit panel.')

    if mat.options.draped:
        errors.append('Must not be draped.')

    if mat.options.solid_camera:
        errors.append('Must have camera collision disabled.')

    if mat.blenderObject.xplane.manip.enabled:
        errors.append('Must not be a manipulator.')

    return errors


def validateInstanced(mat):
    errors = []

    if mat.options.lightLevel:
        errors.append('Must not override light level.')

    if mat.options.panel:
        errors.append('Must not be part of the cockpit panel.')

    if mat.options.draped:
        errors.append('Must not be draped.')

    if mat.options.solid_camera:
        errors.append('Must have camera collision disabled.')

    if mat.options.poly_os > 0:
        errors.append('Must not have polygon offset.')

    if mat.blenderObject.xplane.manip.enabled:
        errors.append('Must not be a manipulator.')

    return errors


def validatePanel(mat):
    errors = []

    if mat.options.lightLevel:
        errors.append('Must not override light level.')

    if mat.textureLit:
        errors.append('Must not have a lit/emissive texture.')

    if mat.textureNormal:
        errors.append('Must not have a normal/alpha/specularity texture.')

    if not mat.options.panel:
        errors.append('Must be part of the cockpit panel.')

    if mat.options.draped:
        errors.append('Must not be draped.')

    if mat.options.surfaceType != 'none':
        errors.append('Must have the surface type "none".')

    return errors


def validateCockpit(mat):
    errors = []

    if mat.options.panel:
        errors.append('Must not be part of the cockpit panel.')

    if mat.options.draped:
        errors.append('Must not be draped.')

    return errors


def validateAircraft(mat):
    errors = []

    if mat.options.panel:
        errors.append('Must not be part of the cockpit panel.')

    if mat.options.draped:
        errors.append('Must not be draped.')

    if mat.blenderObject.xplane.manip.enabled:
        errors.append('Must not be a manipulator.')

    return errors


def validateDraped(mat):
    errors = []

    if mat.options.lightLevel:
        errors.append('Must not override light level.')

    if mat.options.panel:
        errors.append('Must not be part of the cockpit panel.')

    if not mat.options.draped:
        errors.append('Must be draped.')

    if mat.options.surfaceType != 'none':
        errors.append('Must have the surface type "none".')

    if not mat.options.draw:
        errors.append('Must have draw enabled.')

    if mat.options.solid_camera:
        errors.append('Must have camera collision disabled.')

    if mat.options.poly_os > 0:
        errors.append('Must not have polygon offset.')

    if mat.blenderObject.xplane.manip.enabled:
        errors.append('Must not be a manipulator.')

    return errors

def getFirstMatchingMaterial(materials, validation):
    for mat in materials:
        errors = validation(mat)

        if len(errors) == 0:
            return mat

    return None

def getReferenceMaterials(materials, exportType):
    refMats = []

    if exportType == 'cockpit':
        refMats.append(getFirstMatchingMaterial(materials, validateCockpit))
        refMats.append(getFirstMatchingMaterial(materials, validatePanel))
    elif exportType == 'aircraft':
        refMats.append(getFirstMatchingMaterial(materials, validateAircraft))
        refMats.append(getFirstMatchingMaterial(materials, validatePanel))
    elif exportType == 'scenerey':
        refMats.append(getFirstMatchingMaterial(materials, validateScenery))
        refMats.append(getFirstMatchingMaterial(materials, validateDraped))
    elif exportType == 'instanced_scenery':
        refMats.append(getFirstMatchingMaterial(materials, validateInstanced))
        refMats.append(getFirstMatchingMaterial(materials, validateDraped))

    return refMats
