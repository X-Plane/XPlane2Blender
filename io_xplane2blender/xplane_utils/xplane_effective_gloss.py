import numpy
import bpy

def ggx_distribution_cdf(x, alpha):
    sin_x_squared = numpy.sin(x) ** 2
    cos_x_squared = numpy.cos(x) ** 2

    alpha_squared = alpha ** 2

    return sin_x_squared / (cos_x_squared * (alpha_squared - 1) + 1)

def get_effective_gloss(file_path) -> float:
    alpha = 0.5

    try:
        image = bpy.data.images.load(file_path)
    except RuntimeError:
        image = None

    if image != None:
        precision = 100
        
        normals = 2 * numpy.array(image.pixels, dtype=float) - 1
        normals = numpy.reshape(normals, (image.size[1], image.size[0], image.channels))

        angles = numpy.arccos(numpy.sqrt(numpy.clip(1 - numpy.sum(normals[:, :, :2] ** 2, axis=2), 0, 1)))
        
        histogram, bins = numpy.histogram(angles, bins=(2 * precision), range=(0, numpy.pi / 2), density=True)
        histogram *= bins[1:] - bins[:-1]
        
        error = numpy.inf
        
        for current_alpha in numpy.linspace(1 / precision, 1, precision):
            expected = ggx_distribution_cdf(bins, current_alpha)
            expected = expected[1:] - expected[:-1]

            current_error = numpy.sum(numpy.abs(expected - histogram))
            
            if current_error < error:
                error = current_error
                alpha = current_alpha

    return float(numpy.clip((1 - numpy.sqrt(alpha)) / 0.96875, 0, 1))