from dataPipelines.gc_thumbnails.utils import ThumbnailsCreator

def generate_png(f_name, out_dir="./"):
    png_generator = ThumbnailsCreator(
        file_name=f_name,
        output_directory=out_dir
    )
    result = png_generator.generate_png()

    return result
