import os
import bpy

#urls
class Config:
    ADDON_NAME = 'io_sketchfab'
    GITHUB_REPOSITORY_URL = 'https://github.com/sketchfab/gltf2-blender-importer'
    GITHUB_REPOSITORY_API_URL = 'https://api.github.com/repos/sketchfab/gltf2-blender-importer'
    SKETCHFAB_REPORT_URL = 'https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Blender+Plugin'

    SKETCHFAB_URL = 'https://sketchfab.com'
    DUMMY_CLIENTID = 'hGC7unF4BHyEB0s7Orz5E1mBd3LluEG0ILBiZvF9'
    SKETCHFAB_OAUTH = SKETCHFAB_URL + '/oauth2/token/?grant_type=password&client_id=' + DUMMY_CLIENTID
    SKETCHFAB_API = 'https://api.sketchfab.com'
    SKETCHFAB_SEARCH = SKETCHFAB_API + '/v3/search'
    SKETCHFAB_MODEL = SKETCHFAB_API + '/v3/models'
    BASE_SEARCH = SKETCHFAB_SEARCH + '?type=models&downloadable=true'
    DEFAULT_FLAGS = '&staffpicked=true&sort_by=-staffpickedAt'
    DEFAULT_SEARCH = SKETCHFAB_SEARCH + \
                     '?type=models&downloadable=true' + DEFAULT_FLAGS

    SKETCHFAB_ME = '{}/v3/me'.format(SKETCHFAB_URL)

    SKETCHFAB_PLUGIN_VERSION = '{}/releases'.format(GITHUB_REPOSITORY_API_URL)
    # PATH management
    SKETCHFAB_TEMP_DIR = os.path.join(bpy.context.user_preferences.filepaths.temporary_directory, 'sketchfab_downloads')
    SKETCHFAB_THUMB_DIR = os.path.join(SKETCHFAB_TEMP_DIR, 'thumbnails')
    SKETCHFAB_MODEL_DIR = os.path.join(SKETCHFAB_TEMP_DIR, 'imports')

    SKETCHFAB_CATEGORIES = (('ALL', 'All categories', 'All categories'),
                            ('animals-pets', 'Animals & Pets', 'Animals and Pets'),
                            ('architecture', 'Architecture', 'Architecture'),
                            ('art-abstract', 'Art & Abstract', 'Art & Abstract'),
                            ('cars-vehicles', 'Cars & vehicles', 'Cars & vehicles'),
                            ('characters-creatures', 'Characters & Creatures', 'Characters & Creatures'),
                            ('cultural-heritage-history', 'Cultural Heritage & History', 'Cultural Heritage & History'),
                            ('electronics-gadgets', 'Electronics & Gadgets', 'Electronics & Gadgets'),
                            ('fashion-style', 'Fashion & Style', 'Fashion & Style'),
                            ('food-drink', 'Food & Drink', 'Food & Drink'),
                            ('furniture-home', 'Furniture & Home', 'Furniture & Home'),
                            ('music', 'Music', 'Music'),
                            ('nature-plants', 'Nature & Plants', 'Nature & Plants'),
                            ('news-politics', 'News & Politics', 'News & Politics'),
                            ('people', 'People', 'People'),
                            ('places-travel', 'Places & Travel', 'Places & Travel'),
                            ('science-technology', 'Science & Technology', 'Science & Technology'),
                            ('sports-fitness', 'Sports & Fitness', 'Sports & Fitness'),
                            ('weapons-military', 'Weapons & Military', 'Weapons & Military'))

    SKETCHFAB_FACECOUNT = (('ANY', "All", ""),
                           ('10K', "Up to 10k", ""),
                           ('50K', "10k to 50k", ""),
                           ('100K', "50k to 100k", ""),
                           ('250K', "100k to 250k", ""),
                           ('250KP', "250k +", ""))

    SKETCHFAB_SORT_BY = (('RELEVANCE', "Relevance", ""),
                         ('LIKES', "Likes", ""),
                         ('VIEWS', "Views", ""),
                         ('RECENT', "Recent", ""))
    THUMBNAIL_SIZE = (256, 512)



class Utils:
    def humanify_size(size):
        suffix = 'B'
        readable = size

        # Megabyte
        if size > 1048576:
            suffix = 'MB'
            readable = size / 1048576.0
        # Kilobyte
        elif size > 1024:
            suffix = 'KB'
            readable = size / 1024.0

        readable = round(readable, 2)
        return '{}{}'.format(readable, suffix)

    def build_download_url(uid):
        return '{}/{}/download'.format(Config.SKETCHFAB_MODEL, uid)


    def thumbnail_file_exists(uid):
        return os.path.exists(os.path.join(Config.SKETCHFAB_THUMB_DIR, '{}.jpeg'.format(uid)))


    def clean_thumbnail_directory():
        if not os.path.exists(Config.SKETCHFAB_THUMB_DIR):
            return

        from os import listdir
        for file in listdir(Config.SKETCHFAB_THUMB_DIR):
            os.remove(os.path.join(Config.SKETCHFAB_THUMB_DIR, file))


    def clean_downloaded_model_dir(uid):
        import shutil
        shutil.rmtree(os.path.join(Config.SKETCHFAB_MODEL_DIR, uid))


    def get_thumbnail_url(thumbnails_json):
        for image in thumbnails_json['images']:
            if int(image['height']) >= Config.THUMBNAIL_SIZE[0] and int(image['height']) <= Config.THUMBNAIL_SIZE[1]:
                return image['url']