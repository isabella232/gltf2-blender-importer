import bpy
import bpy.utils.previews

from collections import OrderedDict
import threading
import requests
import os

from io_scene_gltf2_importer import *
from Converter import *
from bpy.props import (StringProperty,
                       EnumProperty,
                       BoolProperty,
                       PointerProperty)


ADDON_NAME = 'io_sketchfab'
GITHUB_REPOSITORY_URL = 'https://github.com/sketchfab/gltf2-blender-importer'
GITHUB_REPOSITORY_API_URL = 'https://api.github.com/repos/sketchfab/gltf2-blender-importer'
SKETCHFAB_REPORT_URL = 'https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Blender+Plugin'

bl_info = {
    'name': 'Sketchfab AssetBrowser',
    'description': 'Browse and download free Sketchfab downloadable models',
    'author': 'Sketchfab',
    'license': 'GPL',
    'deps': '',
    'version': (0, 0, 1),
    'blender': (2, 7, 9),
    'location': 'View3D > Tools > Sketchfab',
    'warning': '',
    'wiki_url': 'https://github.com/sketchfab/gltf2-blender-importer/releases',
    'tracker_url': 'https://github.com/sketchfab/gltf2-blender-importer/issues',
    'link': 'https://github.com/sketchfab/gltf2-blender-importer',
    'support': 'COMMUNITY',
    'category': 'Add Mesh'
    }

# Move to CONFIG.py
# URLS
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
SKFB_TEMP_DIR = os.path.join(bpy.context.user_preferences.filepaths.temporary_directory, 'sketchfab_downloads')
SKFB_THUMB_DIR = os.path.join(SKFB_TEMP_DIR, 'thumbnails')
SKFB_MODEL_DIR = os.path.join(SKFB_TEMP_DIR, 'imports')

# Settings
THUMBNAIL_SIZE = (256, 512)
preview_collection = {}

PLUGIN_VERSION = str(bl_info['version']).strip('() ').replace(',', '.')

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
    return '{}/{}/download'.format(SKETCHFAB_MODEL, uid)


def thumbnail_file_exists(uid):
    return os.path.exists(os.path.join(SKFB_THUMB_DIR, '{}.jpeg'.format(uid)))


def clean_thumbnail_directory():
    if not os.path.exists(SKFB_THUMB_DIR):
        return

    from os import listdir
    for file in listdir(SKFB_THUMB_DIR):
        os.remove(os.path.join(SKFB_THUMB_DIR, file))

    print('Cleaned thumbnails')

def clean_downloaded_model_dir(uid):
    import shutil
    shutil.rmtree(os.path.join(SKFB_MODEL_DIR, uid))
    print('Cleaning downloaded file ' + os.path.join(SKFB_MODEL_DIR, uid))

def get_sketchfab_login_props():
    return bpy.context.window_manager.sketchfab_api


def get_sketchfab_props():
    return bpy.context.window_manager.sketchfab_browser


def get_sketchfab_props_proxy():
    return bpy.context.window_manager.sketchfab_browser_proxy


def refresh_search2(self, context):
    pprops = get_sketchfab_props_proxy()
    props = get_sketchfab_props()

    props.query = pprops.query
    props.animated = pprops.animated
    props.pbr = pprops.pbr
    props.staffpick = pprops.staffpick
    props.categories = pprops.categories
    props.face_count = pprops.face_count
    props.sort_by = pprops.sort_by
    bpy.ops.wm.sketchfab_search('EXEC_DEFAULT')


class SketchfabApi:
    def __init__(self):
        self.access_token = ''
        self.headers = {}
        self.display_name = ''
        self.plan_type = ''
        self.next_results_url = None
        self.prev_results_url = None
        pass

    def build_headers(self):
        self.headers = {'Authorization': 'Bearer ' + self.access_token}

    def login(self, email, password):
        url = '{}&username={}&password={}'.format(SKETCHFAB_OAUTH, email, password)
        if True:
            bpy.ops.wm.login_modal('INVOKE_DEFAULT')
        else:
            requests.post(url, hooks={'response': self.parse_login})

    def is_user_logged(self):
        if self.access_token and self.headers:
            return True

        return False

    def logout(self):
        self.access_token = ''
        self.headers = {}

    def request_user_info(self):
        requests.get(SKETCHFAB_ME, headers=self.headers, hooks={'response': self.parse_user_info})

    def get_user_info(self):
        if self.display_name and self.plan_type:
            return 'as {} ({})'.format(self.display_name, self.plan_type)
        else:
            return ('', '')

    def parse_user_info(self, r, *args, **kargs):
        user_data = r.json()
        self.display_name = user_data['displayName']
        self.plan_type = user_data['account']

    def parse_login(self, r, *args, **kwargs):
        if r.status_code == 200 and 'access_token' in r.json():
            self.access_token = r.json()['access_token']
            self.build_headers()
            print('Logged in => ' + self.access_token)
            self.request_user_info()
        else:
            if 'error_description' in r.json():
                print("No")
            else:
                print('Login failed.\n {}'.format(r.json()))

    def get_thumbnail_url(self, thumbnails_json):
        for image in thumbnails_json['images']:
            if int(image['height']) >= THUMBNAIL_SIZE[0] and int(image['height']) <= THUMBNAIL_SIZE[1]:
                return image['url']

    def request_thumbnail(self, thumbnails_json):
        url = self.get_thumbnail_url(thumbnails_json)
        thread = ThumbnailCollector(url)
        thread.start()

    def request_model_info(self, uid):
        url = SKETCHFAB_MODEL + '/' + uid
        model_infothr = GetRequestThread(url, self.handle_model_info)
        model_infothr.start()

    def handle_model_info(self, r, *args, **kwargs):
        uid = get_uid_from_model_url(r.url)
        model = get_sketchfab_props().search_results['current'][uid]
        json_data = r.json()
        model.license = json_data['license']['fullName']
        model.animated = int(json_data['animationCount']) > 0
        get_sketchfab_props().search_results['current'][uid] = model

    def search(self, query, search_cb):
        search_query = '{}{}'.format(BASE_SEARCH, query)
        searchthr = GetRequestThread(search_query, search_cb)
        searchthr.start()

    def search_cursor(self, url, search_cb):
        requests.get(url, hooks={'response': search_cb})

    def get_download_url(self, uid):
        requests.get(build_download_url(uid), headers=self.headers, hooks={'response': self.handle_download})

    def handle_download(self, r, *args, **kwargs):
        if 'gltf' not in r.json():
            return

        skfb = get_sketchfab_props()
        uid = get_uid_from_model_url(r.url)
        current_model = skfb.search_results['current'][uid]

        gltf = r.json()['gltf']
        current_model.download_link = gltf['url']
        current_model.download_size = humanify_size(gltf['size'])

    def get_archive(self, uid):
        url = get_sketchfab_props().search_results['current'][uid].download_link
        if url is None:
            print(url + 'is None')
            return


        if False:
            thread = DownloadThread(url, uid)
            thread.start()
        else:
            r = requests.get(url, stream=True)
            temp_dir = os.path.join(SKFB_MODEL_DIR, uid)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            archive_path = os.path.join(temp_dir, '{}.zip'.format(uid))
            if not os.path.exists(archive_path):
                wm = bpy.context.window_manager
                wm.progress_begin(0, 100)
                set_log("Downloading model..")
                with open(archive_path, "wb") as f:
                    total_length = r.headers.get('content-length')
                    if total_length is None:  # no content length header
                        f.write(r.content)
                    else:
                        dl = 0
                        total_length = int(total_length)
                        for data in r.iter_content(chunk_size=4096):
                            dl += len(data)
                            f.write(data)
                            done = int(100 * dl / total_length)
                            wm.progress_update(done)
                            set_log("Downloading model..{}%".format(done))

                wm.progress_end()
            else:
                print('Model already downloaded')

            gltf_path, gltf_zip = unzip_archive(archive_path)
            import traceback
            try:
                import_model(gltf_path)
                # clean_downloaded_model_dir(uid)
            except Exception as e:
                print(traceback.format_exc())

def set_login_status(status_type, status):
    login_props = get_sketchfab_login_props()
    login_props.status = status
    login_props.status_type = status_type

def set_import_status(status):
    props = get_sketchfab_props()
    props.import_status = status

def set_results_status(status):
    props = get_sketchfab_props()
    props.result_size = 8.0 if status else 7.9
    print(props.result_size)

# Property used for login (importer + future exporter)
class SketchfabLoginProps(bpy.types.PropertyGroup):

    def update_tr(self, context):
        if not self.password:
            return

        self.status = ''
        if self.email != self.last_username or self.password != self.last_password:
            last_username = self.email
            last_password = self.password
            bpy.ops.wm.sketchfab_login('EXEC_DEFAULT')

    email = StringProperty(
            name="email",
            description="User email",
            default="")

    password = StringProperty(
            name="password",
            description="User password",
            subtype='PASSWORD',
            default="",
            update=update_tr
            )

    access_token = StringProperty(
            name="access_token",
            description="oauth access token",
            subtype='PASSWORD',
            default="dr5ysFbOC5thVkvvraCQT1oPaopyP5"
            )

    skfb_api = SketchfabApi()

    status = StringProperty(name='', default='')
    status_type = EnumProperty(
            name="Face Count",
            items= (('ERROR', "Error", ""),
                       ('INFO', "Information", ""),
                       ('FILE_REFRESH', "Progress", "")),
            description="Determines which icon to use",
            default='FILE_REFRESH'
            )

    last_username=''
    last_password=''


class SketchfabBrowserPropsProxy(bpy.types.PropertyGroup):
    # Search
    query = StringProperty(
            name="",
            update=refresh_search2,
            description="Query to search",
            default="",
            options={'SKIP_SAVE'}
            )

    pbr = BoolProperty(
            name="PBR",
            description="Search for PBR model only",
            default=False,
            update=refresh_search2,
            )

    categories = EnumProperty(
            name="Categories",
            items=SKETCHFAB_CATEGORIES,
            description="Show only models of category",
            default='ALL',
            update=refresh_search2
            )
    face_count = EnumProperty(
            name="Face Count",
            items=SKETCHFAB_FACECOUNT,
            description="Determines which meshes are exported",
            default='ANY',
            update=refresh_search2
            )

    sort_by = EnumProperty(
            name="Sort by",
            items=SKETCHFAB_SORT_BY,
            description="Sort ",
            default='RELEVANCE',
            update=refresh_search2
            )

    animated = BoolProperty(
            name="Animated",
            description="Show only models with animation",
            default=False,
            update=refresh_search2
            )
    staffpick = BoolProperty(
            name="Staffpick",
            description="Show only staffpick models",
            default=False,
            update=refresh_search2
            )


class SketchfabBrowserProps(bpy.types.PropertyGroup):
    # Search
    query = StringProperty(
            name="Search",
            description="Query to search",
            default=""
            )

    pbr = BoolProperty(
            name="PBR",
            description="Search for PBR model only",
            default=False
            )

    categories = EnumProperty(
            name="Categories",
            items=SKETCHFAB_CATEGORIES,
            description="Show only models of category",
            default='ALL',
             )

    face_count = EnumProperty(
            name="Face Count",
            items=SKETCHFAB_FACECOUNT,
            description="Determines which meshes are exported",
            default='ANY',
            )

    sort_by = EnumProperty(
            name="Sort by",
            items=SKETCHFAB_SORT_BY,
            description="Sort ",
            default='RELEVANCE',
            )

    animated = BoolProperty(
            name="Animated",
            description="Show only models with animation",
            default=False,
            )

    staffpick = BoolProperty(
            name="Staffpick",
            description="Show only staffpick models",
            default=True,
            )

    status = StringProperty(name='status', default='idle')

    use_preview = BoolProperty(
        name="Use Preview",
        description="Show results using preview widget instead of regular buttons with thumbnails as icons",
        default=True
        )

    search_results = {}
    current_key = StringProperty(name='current', default='current')
    has_searched_next = BoolProperty(name='next', default=False)
    has_searched_prev = BoolProperty(name='prev', default=False)

    skfb_api = SketchfabLoginProps.skfb_api
    custom_icons = bpy.utils.previews.new()
    has_loaded_thumbnails = BoolProperty(default=False)

    is_latest_version = False

    import_status = StringProperty(name='import', default='')


def list_current_results(self, context):
    skfb = get_sketchfab_props()

    if skfb.has_loaded_thumbnails and 'thumbnails' in preview_collection:
        return preview_collection['thumbnails']

    res = []
    missing_thumbnail = False
    if 'current' in skfb.search_results and len(skfb.search_results['current']):
        skfb_results = skfb.search_results['current']
        for i, result in enumerate(skfb_results):
            if result in skfb_results:
                model = skfb_results[result]
                if model.uid in skfb.custom_icons:
                    res.append((model.uid, model.title, "", skfb.custom_icons[model.uid].icon_id, i))
                else:
                    res.append((model.uid, model.title, "", sketchfab_icon['model'].icon_id, i))
                    missing_thumbnail = True
            else:
                print('Result issue')

    # Default element to avoid having an empty preview collection
    if not res:
        res.append(('NORESULTS', 'empty', "", sketchfab_icon['model'].icon_id, 0))

    preview_collection['thumbnails'] = tuple(res)
    skfb.has_loaded_thumbnails = not missing_thumbnail
    return preview_collection['thumbnails']

def draw_filters(layout, context):
    props = get_sketchfab_props_proxy()
    col = layout.box().column(align=True)

    col.prop(props, "pbr")
    col.prop(props, "staffpick")
    # col.prop(props, "animated")

    col.separator()
    col.prop(props, "categories")

    col.label('Sort by')
    sb = col.row()
    sb.prop(props, "sort_by", expand=True)

    col.label('Face count')
    col.prop(props, "face_count", expand=True)


def draw_search(layout, context):
    layout.row()
    props = get_sketchfab_props_proxy()
    col = layout.box().column(align=True)
    col.prop(props, "query")
    col.operator("wm.sketchfab_search", text="Search", icon='VIEWZOOM')

    pprops = get_sketchfab_props()
    col.prop(pprops, "use_preview")

def draw_model_info(layout, model, context):
    p2 = layout.box().column(align=True)
    p2.label('Name: {}'.format(model.title))
    p2.label('Author: {}'.format(model.author))

    if model.license:
        p2.label('License: {}'.format(model.license))
        if(model.animated):
            p2.label('Animation is not supported (possible issues)', icon='ERROR')
    else:
        p2.label('Fetching..')
    p2.operator("wm.sketchfab_view", text="View on Sketchfab", icon='WORLD').model_uid = model.uid

    p3 = layout.column(align=True)

    skfb = get_sketchfab_props()
    p3.enabled = skfb.skfb_api.is_user_logged()
    downloadlabel = "Import model ({})".format(model.download_size if model.download_size else 'fetching data') if p3.enabled is True else 'You need to be logged in to download a model'
    if skfb.import_status:
        downloadlabel = skfb.import_status

    download_icon = 'EXPORT' if p3.enabled else 'INFO'
    p3.label('')
    p3.operator("wm.sketchfab_download", icon=download_icon, text=downloadlabel, translate=False, emboss=True).model_uid = model.uid

# utils
def set_log(log):
    get_sketchfab_props().status = log


def get_uid_from_thumbnail_url(thumbnail_url):
    return thumbnail_url.split('/')[4]


def get_uid_from_model_url(model_url):
    return model_url.split('/')[5]


def unzip_archive(archive_path):
    if os.path.exists(archive_path):
        set_import_status('Unzipping model')
        import zipfile
        zip_ref = zipfile.ZipFile(archive_path, 'r')

        extract_dir = os.path.dirname(archive_path)
        zip_ref.extractall(extract_dir)
        zip_ref.close()

        gltf_file = os.path.join(extract_dir, 'scene.gltf')
        return gltf_file, archive_path

    else:
        print('ERROR: archive doesn\'t exist')


def run_async(func):
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def import_model(gltf_path):
    bpy.ops.wm.import_modal('INVOKE_DEFAULT', gltf_path=gltf_path)
    # thread = ImportThread(gltf_path)
    # thread.start()
    # thread.join()


def build_search_request(query, pbr, animated, staffpick, face_count, category, sort_by):
    final_query = '&q={}'.format(query)

    # Disabled until animation import is implemented
    if animated:
        final_query = final_query + '&animated=true'

    if staffpick:
        final_query = final_query + '&staffpicked=true'

    if sort_by == 'LIKES':
        final_query = final_query + '&sort_by=-likeCount'
    elif sort_by == 'RECENT':
        final_query = final_query + '&sort_by=-publishedAt'
    elif sort_by == 'VIEWS':
        final_query = final_query + '&sort_by=-viewCount'

    if face_count == '10K':
        final_query = final_query + '&max_face_count=10000'
    elif face_count == '50K':
        final_query = final_query + '&min_face_count=10000&max_face_count=50000'
    elif face_count == '100K':
        final_query = final_query + '&min_face_count=50000&max_face_count=100000'
    elif face_count == '250K':
        final_query = final_query + "&min_face_count=100000&max_face_count=250000"
    elif face_count == '250KP':
        final_query = final_query + "&min_face_count=250000"

    if category != 'ALL':
        final_query = final_query + '&categories={}'.format(category)

    if pbr:
        final_query = final_query + '&pbr_type=metalness'

    return final_query


def parse_results(r, *args, **kwargs):
    skfb = get_sketchfab_props()
    json_data = r.json()

    if 'current' in skfb.search_results:
        skfb.search_results['current'].clear()
        del skfb.search_results['current']

    skfb.search_results['current'] = OrderedDict()

    for result in list(json_data['results']):
        uid = result['uid']
        skfb.search_results['current'][result['uid']] = SketchfabModel(result)

        if not os.path.exists(os.path.join(SKFB_THUMB_DIR, uid) + '.jpeg'):
            skfb.skfb_api.request_thumbnail(result['thumbnails'])
        elif not uid in skfb.custom_icons:
            skfb.custom_icons.load(uid, os.path.join(SKFB_THUMB_DIR, "{}.jpeg".format(uid)), 'IMAGE')

    if json_data['next']:
        skfb.skfb_api.next_results_url = json_data['next']
    else:
        skfb.skfb_api.next_results_url = None

    if json_data['previous']:
        skfb.skfb_api.prev_results_url = json_data['previous']
    else:
        skfb.skfb_api.prev_results_url = None


class ThumbnailCollector(threading.Thread):
    def __init__(self, url):
        self.url = url
        threading.Thread.__init__(self)

    def set_url(self, url):
        self.url = url

    def run(self):
        if not self.url:
            return
        requests.get(self.url, stream=True, hooks={'response': self.handle_thumbnail})

    def handle_thumbnail(self, r, *args, **kwargs):
        uid = r.url.split('/')[4]
        if not os.path.exists(SKFB_THUMB_DIR):
            os.makedirs(SKFB_THUMB_DIR)
        thumbnail_path = os.path.join(SKFB_THUMB_DIR, uid) + '.jpeg'

        with open(thumbnail_path, "wb") as f:
            total_length = r.headers.get('content-length')

            if total_length is None and r.content:
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)

        props = get_sketchfab_props()
        if uid not in props.custom_icons:
            props.custom_icons.load(uid, os.path.join(SKFB_THUMB_DIR, "{}.jpeg".format(uid)), 'IMAGE')
        else:
            print('RELOADING ' + uid)


class ImportThread(threading.Thread):
    def __init__(self, gltf_path):
        self.gltf_path = gltf_path
        threading.Thread.__init__(self)

    def run(self):
        bpy.context.scene.render.engine = 'CYCLES'
        gltf_data = glTFImporter(self.gltf_path, Log.default())
        success, txt = gltf_data.read()
        if not success:
            print('Failed to read GLTF')
        try:
            model_name = 'GLTFModel'
            if 'extras' in gltf_data.scene.gltf.json['asset'] and 'title' in gltf_data.scene.gltf.json['asset']['extras']:
                model_name = gltf_data.scene.gltf.json['asset']['extras']['title']

            blender_scene(gltf_data.scene, root_name=model_name)
            print(self.gltf_path)
        except Exception:
            import traceback
            print(traceback.format_exc())


class LoginModal(bpy.types.Operator):
    bl_idname = "wm.login_modal"
    bl_label = "Import glTF model into Sketchfab"
    bl_options = {'INTERNAL'}

    is_logging = BoolProperty(default=False)


    def __init__(self):
        print('start')

    def __del__(self):
        print('END')

    def exectue(self, context):
        print('LOGIN')
        return {'FINISHED'}

    def handle_login(self, r, *args, **kwargs):
        browser_props = get_sketchfab_props()
        print("RESPONSE")
        if r.status_code == 200 and 'access_token' in r.json():
            browser_props.skfb_api.access_token = r.json()['access_token']
            browser_props.skfb_api.build_headers()
            print('Logged in => ' + bpy.context.window_manager.sketchfab_browser.skfb_api.access_token)
            set_login_status('INFO', '')
            browser_props.skfb_api.request_user_info()
        else:
            if 'error_description' in r.json():
                set_login_status('ERROR', 'Failed to authenticate: bad login/password')
            else:
                set_login_status('ERROR', 'Failed to authenticate: bad login/password')
                print('Login failed.\n {}'.format(r.json()))

        self.is_logging = False


    def modal(self, context, event):
        if self.is_logging:
            print(self.is_logging)
            set_login_status('FILE_REFRESH', 'Login to your Sketchfab account...')
            return {'RUNNING_MODAL'}
        else:
            return {'FINISHED'}

    def invoke(self, context, event):
        print('invoke')
        self.is_logging = True
        context.window_manager.modal_handler_add(self)
        login_props = get_sketchfab_login_props()
        if not login_props.password:
            set_login_status('ERROR', 'Failed to authenticate: bad login/password')
            return {'FINISHED'}
        else:
            url = '{}&username={}&password={}'.format(SKETCHFAB_OAUTH, login_props.email, login_props.password)
            requests.post(url, hooks={'response': self.handle_login})


            return {'RUNNING_MODAL'}


class ImportModalOperator(bpy.types.Operator):
    bl_idname = "wm.import_modal"
    bl_label = "Import glTF model into Sketchfab"
    bl_options = {'INTERNAL'}

    gltf_path = StringProperty()

    def __init__(self):
        print('start')

    def __del__(self):
        print('END')

    def exectue(self, context):
        print('IMPORT')
        return {'FINISHED'}

    def modal(self, context, event):
        bpy.context.scene.render.engine = 'CYCLES'
        gltf_data = glTFImporter(self.gltf_path, Log.default())
        success, txt = gltf_data.read()
        if not success:
            print('Failed to read GLTF')
        try:
            model_name = 'GLTFModel'
            if 'extras' in gltf_data.scene.gltf.json['asset'] and 'title' in gltf_data.scene.gltf.json['asset']['extras']:
                model_name = gltf_data.scene.gltf.json['asset']['extras']['title']

            blender_scene(gltf_data.scene, root_name=model_name)
            print(self.gltf_path)
            set_import_status('')
            return {'FINISHED'}
        except Exception:
            import traceback
            print(traceback.format_exc())
            set_import_status('')
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        set_import_status('Importing...')
        return {'RUNNING_MODAL'}


class DownloadThread(threading.Thread):
    def __init__(self, url, uid):
        self.url = url
        self.uid = uid
        threading.Thread.__init__(self)

    def run(self):
        set_import_status('Downloading model')
        r = requests.get(self.url, stream=True)
        temp_dir = os.path.join(SKFB_MODEL_DIR, self.uid)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        archive_path = os.path.join(temp_dir, '{}.zip'.format(self.uid))

        if not os.path.exists(archive_path):
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
            with open(archive_path, "wb") as f:
                total_length = r.headers.get('content-length')

                if total_length is None:
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        wm.progress_update(done)

            wm.progress_end()
        else:
            print('Model already downloaded')

        import_model(unzip_archive(archive_path))
        # clean_downloaded_model_dir(self.uid)
        # print('OK')


class GetRequestThread(threading.Thread):
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback
        threading.Thread.__init__(self)

    def run(self):
        requests.get(self.url, hooks={'response': self.callback})


# Panels
class View3DPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Sketchfab Assets Browser"
    bl_category = "Sketchfab"

    @classmethod
    def poll(cls, context):
        return (context.scene is not None)


class LoginPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_test_1"
    bl_label = "Login to your Sketchfab account"

    is_logged = BoolProperty()

    def draw(self, context):
        props = get_sketchfab_login_props()

        layout = self.layout

        if props.skfb_api.is_user_logged():
            self.bl_label = 'Logged in as {}'.format(props.skfb_api.get_user_info())
            layout.operator('wm.sketchfab_login', text='Logout', icon='GO_LEFT').authenticate = False
            if props.status:
                layout.prop(props,'status', icon=props.status_type)
        else:
            layout.prop(props, "email")
            layout.prop(props, "password")
            layout.operator('wm.sketchfab_login', text='Login', icon='WORLD').authenticate = True
            self.bl_label = "Login to your Sketchfab account"
            if props.status:
                layout.prop(props,'status', icon=props.status_type)


class FiltersPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_sketchfab_filters"
    bl_label = "Filters"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        # self.layout.box().column(align=True).operator('wm.sketchfab_browse', text="Browse Sketchfab")
        # self.layout.label('Debug')
        # self.layout.operator('wm.skfb_debug', 'PERFORM')
        draw_filters(self.layout, context)


def draw_results_icons(results, props, nbcol=4):
    props = get_sketchfab_props()
    current = props.search_results['current']

    dimx = nbcol if current else 0
    dimy = int(24 / nbcol) if current else 0
    if dimx is not 0 and dimy is not 0:
        for r in range(dimy):
            ro = results.row()
            for col in range(dimx):
                col2 = ro.column(align=True)
                index = r * dimx + col
                if index >= len(current.keys()):
                    return

                model = current[list(current.keys())[index]]

                if model.uid in props.custom_icons:
                    col2.operator("wm.sketchfab_modelview", icon_value=props.custom_icons[model.uid].icon_id, text="{}".format(model.title + ' by ' + model.author)).uid = list(current.keys())[index]
                else:
                    col2.operator("wm.sketchfab_modelview", text="{}".format(model.title + ' by ' + model.author)).uid = list(current.keys())[index]
    else:
        results.row()
        results.row().label('No results')
        results.row()


class ResultsPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_sketchfab_results"
    bl_label = "Results"

    uid = ''
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        props = get_sketchfab_props()
        results = layout.column(align=True)
        model = None

        rrr = col.row()
        if props.skfb_api.prev_results_url:
            rrr.operator("wm.sketchfab_search_prev", text="Previous page", icon='GO_LEFT')

        if props.skfb_api.next_results_url:
            rrr.operator("wm.sketchfab_search_next", text="Next page", icon='RIGHTARROW')

        if 'current' not in props.search_results:
            self.bl_label = 'No results'
            return

        elif len(props.search_results['current']) == 0:
            self.bl_label = 'No results'
            return
        else:
            self.bl_label = "Results"

        if props.use_preview:
            result_label = 'Select a model {}'.format('in current result page' if props.skfb_api.next_results_url else '{} results'.format(len(props.search_results['current'])))
            col.label(result_label)
            try:
                col.template_icon_view(bpy.context.window_manager, 'result_previews', show_labels=True, scale=8.0)
            except Exception:
                print('NO')
                pass

            if bpy.context.window_manager.result_previews not in props.search_results['current']:
                p2 = layout.box().column(align=True)
                p2.label('Fetching results...')
                return

            model = props.search_results['current'][bpy.context.window_manager.result_previews]

            if not model:
                return

            if self.uid != model.uid:
                self.uid = model.uid

                if not model.info_requested:
                    props.skfb_api.request_model_info(model.uid)
                    model.info_requested = True

                if not model.download_url_requested:
                    props.skfb_api.get_download_url(model.uid)
                    model.download_url_requested = True

                if props.skfb_api.is_user_logged() and not model.download_link:
                    props.skfb_api.get_download_url(model.uid)

            draw_model_info(col, model, context)

        else:
            draw_results_icons(results, props, 2)




# Operators:
class SketchfabLogger(bpy.types.Operator):
    bl_idname = 'wm.sketchfab_login'
    bl_label = 'Sketchfab Login'
    bl_options= {'INTERNAL'}

    authenticate = BoolProperty(default=True)

    def execute(self, context):
        set_login_status('FILE_REFRESH', 'Login to your Sketchfab account...')
        wm = context.window_manager
        if self.authenticate and wm.sketchfab_api.password:
            wm.sketchfab_browser.skfb_api.login(wm.sketchfab_api.email, wm.sketchfab_api.password)
        else:
            wm.sketchfab_browser.skfb_api.logout()
            wm.sketchfab_api.password = ''
            set_login_status('FILE_REFRESH', '')
        return {'FINISHED'}


# Operator to perform search on Sketchfab
class SketchfabBrowse(View3DPanel, bpy.types.Panel):
    bl_idname = "wm.sketchfab_browse"
    bl_label = "Browse Sketchfab"

    def draw(self, context):
        draw_search(self.layout, context)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=900, height=850)


class SketchfabModel:
    def __init__(self, json_data):
        self.title = str(json_data['name'])
        self.author = json_data['user']['displayName']
        self.uid = json_data['uid']
        self.vertex_count = json_data['vertexCount']
        self.face_count = json_data['faceCount']

        self.info_requested = False
        self.license = None
        self.animated = False

        self.download_url_requested = False
        self.download_size = None
        self.download_link = None

        self.thumbnail_url = os.path.join(SKFB_THUMB_DIR, '{}.jpeg'.format(self.uid))


class SketchfabModelView(bpy.types.Operator):
    bl_idname = "wm.sketchfab_modelview"
    bl_label = "Download Sketchfab model"
    bl_options= {'INTERNAL'}

    uid = bpy.props.StringProperty(name="uid")

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        skfb = context.window_manager.sketchfab_browser
        model = skfb.search_results['current'][self.uid]

        layout = self.layout
        col = layout.column()

        if not model:
            return

        if not model.info_requested:
            skfb.skfb_api.request_model_info(model.uid)
            model.info_requested = True

        if not model.download_url_requested:
            skfb.skfb_api.get_download_url(model.uid)
            model.download_url_requested = True

        col.label(text='{} by {}'.format(model.title, model.author))
        col.operator("wm.sketchfab_view", text="View on Sketchfab", icon='WORLD').model_uid = self.uid

        try:
            bpy.context.window_manager.result_previews = self.uid
            col.template_icon_view(bpy.context.window_manager, 'result_previews', show_labels=True, scale=5.0)
        except Exception:
            pass

        col.label('License {}'.format(model.license if model.license else '(fetching)'), icon='FILE_SCRIPT')

        user_logged = skfb.skfb_api.is_user_logged()

        if model.download_link:
            col.operator("wm.sketchfab_download", text="Download model ({})".format(model.download_size if model.download_size else 'fetching data')).model_uid = self.uid
        elif not user_logged:
            p3 = col.column()
            p3.enabled = False
            p3.operator("wm.sketchfab_download", text='You need to be logged in to import a model', icon='ERROR')
        else:
            col.operator("wm.sketchfab_download", text='Model is not available', icon='INFO')


    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

class SketchfabDownloadModel(bpy.types.Operator):
    bl_idname = "wm.sketchfab_download"
    bl_label = "Downloading"
    bl_options= {'INTERNAL'}

    model_uid = bpy.props.StringProperty(name="uid")

    def execute(self, context):
        skfb_api = context.window_manager.sketchfab_browser.skfb_api
        skfb_api.get_archive(self.model_uid)
        return {'FINISHED'}


class ViewOnSketchfab(bpy.types.Operator):
    bl_idname = "wm.sketchfab_view"
    bl_label = "Open on Browser"
    bl_options= {'INTERNAL'}

    model_uid = bpy.props.StringProperty(name="uid")

    def execute(self, context):
        import webbrowser
        webbrowser.open('{}/models/{}'.format(SKETCHFAB_URL, self.model_uid))
        return {'FINISHED'}

def clear_search():
    skfb = get_sketchfab_props()
    skfb.has_loaded_thumbnails = False
    skfb.search_results.clear()
    skfb.custom_icons.clear()
    bpy.data.window_managers['WinMan']['result_previews'] = 0


class SketchfabSearch(bpy.types.Operator):
    bl_idname = "wm.sketchfab_search"
    bl_label = "Search Sketchfab"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        # prepare request for search
        clear_search()
        skfb = get_sketchfab_props()
        skfb.skfb_api.prev_results_url = None
        skfb.skfb_api.next_results_url = None
        final_query = build_search_request(skfb.query, skfb.pbr, skfb.animated, skfb.staffpick, skfb.face_count, skfb.categories, skfb.sort_by)
        skfb.skfb_api.search(final_query, parse_results)
        return {'FINISHED'}


class SketchfabSearchNextResults(bpy.types.Operator):
    bl_idname = "wm.sketchfab_search_next"
    bl_label = "Search Sketchfab"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        # prepare request for search
        clear_search()
        skfb_api = get_sketchfab_props().skfb_api
        skfb_api.search_cursor(skfb_api.next_results_url, parse_results)
        return {'FINISHED'}


class SketchfabSearchPreviousResults(bpy.types.Operator):
    bl_idname = "wm.sketchfab_search_prev"
    bl_label = "Search Sketchfab"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        # prepare request for search
        clear_search()
        skfb_api = get_sketchfab_props().skfb_api
        skfb_api.search_cursor(skfb_api.prev_results_url, parse_results)
        return {'FINISHED'}


class SketchfabOpenModel(bpy.types.Operator):
    bl_idname = "wm.sketchfab_open"
    bl_label = "Downloading"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="I'm downloading your model!")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=550)


class SketchfabPopup(bpy.types.Operator):
    bl_idname = "wm.sketchfab_error"
    bl_label = "Sketchfab"
    bl_options= {'INTERNAL'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label('YOLO')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=550)

class VersionPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_sketchfab_version"
    bl_label = "Sketchfab plugin v{}".format(PLUGIN_VERSION)

    def draw(self, context):
        self.layout.alignment = 'CENTER'
        skfb = get_sketchfab_props()
        if not skfb.is_latest_version:
            self.layout.operator('wm.skfb_new_version', text='New version available', icon='NEW')

        rr = self.layout.row()
        rr.operator('wm.skfb_help', text='Documentation', icon='QUESTION')
        rr.operator('wm.skfb_report_issue', text='Report an issue', icon='ERROR')

class SketchfabNewVersion(bpy.types.Operator):
    bl_idname = "wm.skfb_new_version"
    bl_label = "Sketchfab"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        import webbrowser
        webbrowser.open('{}/releases/latest'.format(GITHUB_REPOSITORY_URL))
        return {'FINISHED'}

class SketchfabReportIssue(bpy.types.Operator):
    bl_idname = "wm.skfb_report_issue"
    bl_label = "Sketchfab"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        import webbrowser
        webbrowser.open(SKETCHFAB_REPORT_URL)
        return {'FINISHED'}

class SketchfabHelp(bpy.types.Operator):
    bl_idname = "wm.skfb_help"
    bl_label = "Sketchfab"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        import webbrowser
        webbrowser.open('{}/releases/latest'.format(GITHUB_REPOSITORY_URL))
        return {'FINISHED'}

class SketchfabDebug(bpy.types.Operator):
    bl_idname = "wm.sketchfab_debug"
    bl_label = "Open temp dir"
    bl_options= {'INTERNAL'}

    def execute(self, context):
        command = 'echo ' + SKFB_TEMP_DIR + '| clip'
        os.system(command)
        if 'thumbnails' in preview_collection:
            del preview_collection['thumbnails']

        return {'FINISHED'}


classes = (
    # Properties
    SketchfabBrowserProps,
    SketchfabLoginProps,
    SketchfabBrowserPropsProxy,

    # Panels
    LoginPanel,
    SketchfabBrowse,
    FiltersPanel,
    ResultsPanel,
    VersionPanel,
    ViewOnSketchfab,
    SketchfabModelView,
    SketchfabDownloadModel,
    SketchfabLogger,


    # Operators
    SketchfabSearch,
    SketchfabSearchNextResults,
    SketchfabSearchPreviousResults,
    SketchfabNewVersion,
    SketchfabReportIssue,
    SketchfabHelp,
    ImportModalOperator,
    LoginModal,

    # Misc and Debug
    SketchfabPopup,
    SketchfabDebug
    )


def check_plugin_version(request, *args, **kwargs):
    response = request.json()
    if response and len(response):
        latest_release_version = set(response[0]['tag_name'].split('.'))
        if latest_release_version == bl_info['version']:
            skfb.is_latest_version = True
        else:
            print('NEW VERSION AVAILABLE: {}'.format(latest_release_version))
    else:
        print('Failed to retrieve plugin version')

def register():
    global sketchfab_icon
    sketchfab_icon = bpy.utils.previews.new()
    sketchfab_icon.load("skfb", "D:\\logo.png", 'IMAGE')
    sketchfab_icon.load("model", "D:\\placeholder.png", 'IMAGE')

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.sketchfab_browser = PointerProperty(
                type=SketchfabBrowserProps)

    bpy.types.WindowManager.sketchfab_browser_proxy = PointerProperty(
                type=SketchfabBrowserPropsProxy)

    bpy.types.WindowManager.sketchfab_api = PointerProperty(
                type=SketchfabLoginProps,
                )

    preview_collection['thumbnails'] = sketchfab_icon
    bpy.types.WindowManager.result_previews = EnumProperty(items=list_current_results)

    requests.get(SKETCHFAB_PLUGIN_VERSION, hooks={'response': check_plugin_version})


def unregister():
    # sketchfab_icon.clear()
    # del sketchfab_icon

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.sketchfab_api
    del bpy.types.WindowManager.sketchfab_browser
    del bpy.types.WindowManager.sketchfab_browser_proxy
    del bpy.types.WindowManager.result_previews

    clean_thumbnail_directory()


if __name__ == "__main__":
    register()
