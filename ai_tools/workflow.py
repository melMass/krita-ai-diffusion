from .image import Bounds, Extent, Image, Mask
from .diffusion import Progress
from . import diffusion
from . import settings

async def inpaint(image: Image, mask: Mask, prompt: str, progress: Progress):
    mask_image = mask.to_image(image.extent)

    max_res = settings.max_inpaint_resolution
    if image.width > max_res or image.height > max_res:
        original_width = image.width
        image = Image.downscale(image, max_res)
        mask_image = Image.downscale(mask_image, max_res)
        scale = image.width / original_width
        progress = Progress.forward(progress, 0.5)
        assert scale < 1
    else:
        scale = 1

    result = await diffusion.inpaint(image, mask_image, prompt, progress)
    result.debug_save('diffusion_inpaint_result')
    # Result is the whole image, but we really only need the inpainted region
    result = Image.sub_region(result, Bounds.scale(mask.bounds, scale))

    # If we downscaled the original image before, upscale now, but only
    # the inpainted region (rest of the image hasn't changed)
    if scale < 1:
        result = await diffusion.upscale(result, mask.bounds.extent, progress)

    result.debug_save('diffusion_upscale_result')
    # Set alpha in the result image according to the inpaint mask
    Mask.apply(result, mask)
    result.debug_save('diffusion_masked_result')
    return result