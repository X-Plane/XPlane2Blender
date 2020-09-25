import bpy


def getImageByFilepath(filepath):
    image = None
    i = 0

    while image == None and i < len(bpy.data.images):
        if bpy.data.images[i].filepath == filepath:
            image = bpy.data.images[i]
        i += 1

    return image


def getImagePixels(image):
    pixels = [0.0, 0.0, 0.0, 1.0] * int((len(image.pixels) / 4))
    # for i in range(0, len(image.pixels)):
    #    pixels.append(image.pixels[i])

    return pixels


def imageSizesEqual(a, b):
    return a.size[0] == b.size[0] and a.size[1] == b.size[1]


def getGeneratedImage(targetName, width, height, channels):
    image = None
    alpha = channels == 2 or channels == 4
    color = (0.0, 0.0, 0.0, 1.0)

    if bpy.data.images.find(targetName) != -1:
        image = bpy.data.images[targetName]
        if image.size[0] != width or image.size[1] != height:
            image = None

    if image == None:
        image = bpy.ops.image.new(
            name=targetName, width=width, height=height, color=color, alpha=alpha
        )
        image = bpy.data.images[targetName]
        image.file_format = "PNG"

    return image


def specularToGrayscale(specularImage, targetName):
    width = specularImage.size[0]
    height = specularImage.size[1]
    image = getGeneratedImage(targetName, width, height, 1)

    pixels = getImagePixels(image)
    specPixels = specularImage.pixels[:]

    for pi in range(0, len(specularImage.pixels), 4):
        for i in range(3):
            pixels[pi + i] = specPixels[pi + i]
        pixels[pi + 3] = 1.0

    image.pixels = pixels

    return image


def normalWithoutAlpha(normalImage, targetName):
    width = normalImage.size[0]
    height = normalImage.size[1]
    image = getGeneratedImage(targetName, width, height, 3)

    pixels = getImagePixels(image)
    normalPixels = normalImage.pixels[:]

    for pi in range(0, len(normalImage.pixels), 4):
        for i in range(3):
            pixels[pi + i] = normalPixels[pi + i]
        pixels[pi + 3] = 1.0

    image.pixels = pixels

    return image


def combineSpecularAndNormal(specularImage, normalImage, targetName):
    if not imageSizesEqual(specularImage, normalImage):
        # TODO: provide more usefull output
        # and eventually use the debugger to log this error instead of rasining it
        raise Exception("Image sizes do not match")

    width = specularImage.size[0]
    height = specularImage.size[1]
    image = getGeneratedImage(targetName, width, height, 4)

    pixels = getImagePixels(image)
    normalPixels = normalImage.pixels[:]
    specPixels = specularImage.pixels[:]

    for pi in range(0, len(normalImage.pixels), 4):
        for i in range(3):
            pixels[pi + i] = normalPixels[pi + i]

        pixels[pi + 3] = specPixels[pi]

    image.pixels = pixels

    return image
