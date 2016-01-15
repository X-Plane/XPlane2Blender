import bpy

def getImageByFilepath(filepath):
    image = None
    i = 0

    while image == None and i < len(bpy.data.images):
        if bpy.data.images[i].filepath == filepath:
            image = bpy.data.images[i]
        i += 1

    return image

def imageSizesEqual(a, b):
    return a.size[0] == b.size[0] and a.size[1] == b.size[1]

def getPixel(image, x, y):
    channels = image.channels
    i = (image.size[1] * y * channels) + (x * channels)
    pixel = []
    for ii in range(0, channels - 1):
        pixel.append(image.pixels[i + ii])

    return pixel

def setPixel(image, x, y, pixel):
    channels = image.channels
    i = (image.size[1] * y * channels) + (x * channels)
    for ii in range(0, channels - 1):
        image.pixels[i + ii] = pixel[ii]

def getGeneratedImage(targetName, width, height, channels):
    image = None
    alpha = channels == 2 or channels == 4
    # if channels == 1:
    #     color = (0.0)
    # if channels == 2:
    #     color = (0.0, 1.0)
    # if channels == 3:
    #     color = (0.0, 0.0, 0.0)
    # if channels == 4:
    color = (0.0, 0.0, 0.0, 1.0)

    if bpy.data.images.find(targetName) != -1:
        image = bpy.data.images[targetName]
        if image.size[0] != width or image.size[1] != height:
            image = None

    if image == None:
        image = bpy.ops.image.new(name = targetName, width = width, height = height, color = color, alpha = alpha)
        image = bpy.data.images[targetName]
        image.file_format = 'PNG'
        #image.channels = channels

    return image

def specularToGrayscale(specularImage, targetName):
    width = specularImage.size[0]
    height = specularImage.size[1]

    image = getGeneratedImage(targetName, width, height, 1)

    for y in range(0, height - 1):
        for x in range(0, width - 1):
            specularPixel = getPixel(specularImage, x, y)
            setPixel(image, x, y, (specularPixel[0]))

    return image

def normalWithoutAlpha(normalImage, targetName):
    width = normalImage.size[0]
    height = normalImage.size[1]

    image = getGeneratedImage(targetName, width, height, 3)
    print(normalImage.channels, normalImage.size[0], normalImage.size[1], len(normalImage.pixels))
    for y in range(0, height):
        for x in range(0, width):
            normalPixel = getPixel(normalImage, x, y)
            setPixel(image, x, y, (normalPixel[0], normalPixel[1], normalPixel[2]))

    return image

def combineSpecularAndNormal(specularImage, normalImage, targetName):
    if not imageSizesEqual(specularImage, normalImage):
        # TODO: provide more usefull output
        # and eventually use the debugger to log this error instead of rasining it
        raise Error('Image sizes do not match')

    width = specularImage.size[0]
    height = specularImage.size[1]

    image = getGeneratedImage(targetName, width, height, 4)

    for y in range(0, height):
        for x in range(0, width):
            specularPixel = getPixel(specularImage, x, y)
            normalPixel = getPixel(normalImage, x, y)
            setPixel(image, x, y, (normalPixel[0], normalPixel[1], normalPixel[2], specularPixel[0]))

    return image
