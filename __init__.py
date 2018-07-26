import bpy

from collections import OrderedDict
import time
import threading
import tempfile
import json
import requests
import os
from pathlib import Path

from io_scene_gltf2_importer import *
from Converter import *
from bpy.types import AddonPreferences
from bpy.props import (StringProperty,
                       EnumProperty,
                       BoolProperty,
                       PointerProperty,
                       )


ADDON_NAME = 'io_sketchfab'

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
    'wiki_url': 'https://github.com/s-leger/archipack/wiki',
    'tracker_url': 'https://github.com/s-leger/archipack/issues',
    'link': 'https://github.com/s-leger/archipack',
    'support': 'COMMUNITY',
    'category': 'Add Mesh'
    }

# URLS
SKETCHFAB_URL = 'https://sketchfab.com'
DUMMY_CLIENTID = 'IUO8d5VVOIUCzWQArQ3VuXfbwx5QekZfLeDlpOmW'
SKETCHFAB_OAUTH = SKETCHFAB_URL + '/oauth2/token/?grant_type=password&client_id=' + DUMMY_CLIENTID
SKETCHFAB_API = 'https://api.sketchfab.com'
SKETCHFAB_SEARCH = SKETCHFAB_API + '/v3/search'
SKETCHFAB_MODEL = SKETCHFAB_API + '/v3/models'
BASE_SEARCH = SKETCHFAB_SEARCH +'?type=models&downloadable=true&pbr_type=metalness&pbr_type=false'
DEFAULT_SEARCH = SKETCHFAB_SEARCH + '?type=models&downloadable=true&staffpicked=true&sort_by=-publishedAt&pbr_type=metalness&pbr_type=false'
#SKETCHFAB_CATEGORIES = SKETCHFAB_API + '/v3/categories'
SKETCHFAB_ME = '{}/v3/me'.format(SKETCHFAB_URL)

# PATH management
SKFB_TEMP_DIR = os.path.join(bpy.context.user_preferences.filepaths.temporary_directory, 'sketchfab_downloads')
SKFB_THUMB_DIR = os.path.join(SKFB_TEMP_DIR, 'thumbnails')
SKFB_MODEL_DIR = os.path.join(SKFB_TEMP_DIR, 'imports')

# Settings
THUMBNAIL_SIZE = (256, 512)
preview_collection = {}
class SketchfabBrowserPreferences(AddonPreferences):
    bl_idname = ADDON_NAME

    # The following property is read-only to limit the scope of the
    # addon and allow for proper testing within this scope.
    skfb_temp_directory = StringProperty(
        name = 'Temporary path for downloads/thumbnails',
        subtype = 'DIR_PATH',
        default = os.path.join(bpy.context.user_preferences.filepaths.temporary_directory + 'sketchfab_downloads')
    )

SKETCHFAB_CATEGORIES = (('ALL', 'All categories', 'All categories'),
                   ('animals-pets','Animals & Pets', 'Animals and Pets'),
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
                   ('250kP', "250k +", ""))

SKETCHFAB_SORT_BY = (('RELEVANCE', "Relevance", ""),
                   ('LIKES', "Likes", ""),
                   ('VIEWS', "Views", ""),
                   ('RECENT', "Recent", ""))


def preferences() -> SketchfabBrowserPreferences:
    pass
    #return bpy.context.user_preferences.addons[ADDON_NAME].preferences

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

def thumbnail_file_exists(uid):
    return os.path.exists(os.path.join(SKFB_THUMB_DIR, '{}.jpeg'.format(uid)))

def get_sketchfab_props():
    return bpy.context.window_manager.sketchfab_browser

def get_sketchfab_props_proxy():
    return bpy.context.window_manager.sketchfab_browser_proxy

def refresh_search2(self, context):
    pprops = get_sketchfab_props_proxy()
    props = get_sketchfab_props()

    props.query = pprops.query
    props.animated = pprops.animated
    props.staffpick = pprops.staffpick
    props.categories = pprops.categories
    props.face_count = pprops.face_count
    props.sort_by = pprops.sort_by
    bpy.ops.wm.sketchfab_search('EXEC_DEFAULT')

class SketchfabApi:
    def __init__ (self):
        self.search_cb = None
        self.access_token = ''
        self.headers = {}
        self.display_name = ''
        self.plan_type = ''
        self.next_results_url = None
        self.prev_results_url = None
        pass

    def build_headers(self):
        self.headers = {'Authorization' : 'Bearer ' + self.access_token}

    def login(self, email, password):
        url = '{}&username={}&password={}'.format(SKETCHFAB_OAUTH, email, password)
        if True:
            thread = LoginThread(url)
            thread.start()
        else:
            requests.post(url, hooks={'response': self.parse_login})

    def logout(self):
        self.headers = {}

    def is_user_logged(self):
        if self.access_token and self.headers:
            return True
        return False

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
                bpy.ops.wm.sketchfab_error('EXEC_DEFAULT', message='Failed')
                # report('ERROR', r.json()['error_description'])
            else:
                print('Login failed.\n {}'.format(r.json()))

    def get_thumbnail_url(self, thumbnails_json):
        for image in thumbnails_json['images']:
            if int(image['height']) > THUMBNAIL_SIZE[0] and int(image['height']) < THUMBNAIL_SIZE[1]:
                return image['url']

    def request_thumbnail(self, thumbnails_json):
        url = self.get_thumbnail_url(thumbnails_json)
        thread = ThumbnailCollector(url)
        thread.start()

    def handle_thumbnail(self, r, *args, **kwargs):
        uid = get_uid_from_thumbnail_url(r.url)

        if not os.path.exists(SKFB_THUMB_DIR):
            os.makedirs(SKFB_THUMB_DIR)

        thumbnail_path = os.path.join(SKFB_THUMB_DIR, uid) + '.jpeg'

        with open(thumbnail_path, "wb") as f:
            total_length = r.headers.get('content-length')

            if total_length is None and r.content: # no content length header
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(100 * dl / total_length)

        img_name = '{}'.format(uid)
        img = bpy.data.images.load(thumbnail_path, check_existing=True)
        img.name = img_name
        tex = bpy.data.textures.new(img_name, 'IMAGE') if img_name not in bpy.data.textures else bpy.data.textures[img_name]
        tex.image = img

        props = get_sketchfab_props()
        if uid not in props.custom_icons:
            props.custom_icons.load(uid, os.path.join(SKFB_THUMB_DIR, "{}.jpeg".format(uid)), 'IMAGE')

    def request_model_info(self, uid):
        print('REQUEST!')
        url = SKETCHFAB_MODEL + '/' + uid
        model_infothr= GetRequestThread(url, self.handle_model_info)
        model_infothr.start()

    def handle_model_info(self, r, *args, **kwargs):
        uid = get_uid_from_model_url(r.url)
        model = get_sketchfab_props().search_results['current'][uid]
        json_data = r.json()
        model.license = json_data['license']['fullName']
        get_sketchfab_props().search_results['current'][uid] = model

    def handle_download(self, r, *args, **kwargs):
        if not 'gltf' in r.json():
            return

        uid = get_uid_from_model_url(r.url)
        skfb = get_sketchfab_props()
        skfb.search_results['current'][uid].download_link = r.json()['gltf']['url']
        skfb.search_results['current'][uid].download_size = humanify_size(r.json()['gltf']['size'])

    def search(self, query, search_cb):
        #self.search_cb = search_cb
        search_query = '{}{}'.format(BASE_SEARCH, query) if query else DEFAULT_SEARCH
        searchthr= GetRequestThread(search_query, search_cb)
        searchthr.start()
        #search_rq = requests.get(search_query, hooks={'response': self.search_cb})

    def search_cursor(self, url, search_cb):
        self.search_cb = search_cb
        search_rq = requests.get(url, hooks={'response': self.search_cb})

    def get_download_url(self, uid):
        download_rq = requests.get(SKETCHFAB_MODEL + '/' + uid + '/download', headers=self.headers, hooks={'response': self.handle_download})

    def get_archive(self, uid):
        url = get_sketchfab_props().search_results['current'][uid].download_link
        print(url)
        if False:
            thread = DownloadThread(url, uid)
            thread.start()
        else:
            r = requests.get(url, stream=True)
            temp_dir =  os.path.join(SKFB_MODEL_DIR, uid)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            archive_path = os.path.join(temp_dir, '{}.zip'.format(uid))
            print(archive_path)
            if not os.path.exists(archive_path):
                wm = bpy.context.window_manager
                wm.progress_begin(0, 100)
                set_log("Downloading model..")
                with open(archive_path, "wb") as f:
                    # print("Downloading {}".format(archive_path))
                    total_length = r.headers.get('content-length')

                    if total_length is None: # no content length header
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


            gltf_path = unzip_archive(archive_path)
            import traceback
            try:
                import_model(gltf_path)
            except Exception as e:
                print(traceback.format_exc())


# Property used for login (importer + future exporter)
class SketchfabLoginProps(bpy.types.PropertyGroup):

    def update_tr(self, context):
        bpy.ops.wm.sketchfab_login('EXEC_DEFAULT')

    email = StringProperty(
            name="email",
            description="User email",
            default = "")

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
            default=""
            )

    skfb_api = SketchfabApi()

class SketchfabBrowserPropsProxy(bpy.types.PropertyGroup):
    # Search
    query = StringProperty(
            name="",
            update=refresh_search2,
            description="Query to search",
            default=""
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

    search_results = {}
    search_results_thumbnails = {}

    skfb_api = SketchfabLoginProps.skfb_api
    custom_icons = bpy.utils.previews.new()

    use_preview = BoolProperty(
        name="Use Preview",
        description="Show results as buttons with icon as thumbnail",
        default=False
        )

def list_current_results(self, context):
    skfb = get_sketchfab_props()
    skfb_results = skfb.search_results['current']
    res = []

    for i, result in enumerate(skfb_results):
        if not result in skfb_results:
            print('RESULT ISSUE')
        else:
            model = skfb_results[result]
            if model.uid in skfb.custom_icons:
                res.append((model.uid, model.title , "", skfb.custom_icons[model.uid].icon_id, i))

    pcoll = preview_collection['main']
    pcoll.my_previews = res
    return pcoll.my_previews

def draw_results_icons(results, props, nbcol = 4):
    props = get_sketchfab_props()
    current = props.search_results['current']
    # current_thumbnails = props.search_results_thumbnails['current']
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

                if thumbnail_file_exists(model.uid) and model.uid not in props.custom_icons:
                    props.custom_icons.load(model.uid, os.path.join(SKFB_THUMB_DIR, "{}.jpeg".format(model.uid)), 'IMAGE')

                if model.uid in props.custom_icons:
                    col2.operator("wm.sketchfab_modelview", icon_value=props.custom_icons[model.uid].icon_id, text="{}".format(model.title + ' by ' + model.author)).uid = list(current.keys())[index]
                else:
                    col2.operator("wm.sketchfab_modelview", text="{}".format(model.title + ' by ' + model.author)).uid = list(current.keys())[index]
    else:
        results.row()
        results.row().label('No results')
        results.row()

def draw_filters(layout, context):
    wm = context.window_manager
    props = get_sketchfab_props_proxy()
    col = layout.box().column(align=True)
    col.prop(props, "categories")

    col.prop(props, "animated")
    col.prop(props, "staffpick")

    col.label('Sort by')
    sb = col.row()
    sb.prop(props, "sort_by", expand=True)

    col.label('Face count')
    col.prop(props, "face_count", expand=True)

def draw_search(layout, context):
    wm = context.window_manager
    layout.row()
    props = get_sketchfab_props_proxy()
    split = layout.split(percentage=0.5)
    col = layout.box().column(align=True)
    col.prop(props, "query")
    col.operator("wm.sketchfab_search", text="Search")

def draw_results(layout, context):
    col = layout.column(align=True)
    props = get_sketchfab_props()
    col.prop(props, "use_preview")
    results = layout.column(align=True)
    model = None

    rrr = col.row()
    if props.skfb_api.prev_results_url:
        rrr.operator("wm.sketchfab_search_prev", text="Previous page", icon='GO_LEFT')

    if props.skfb_api.next_results_url:
        rrr.operator("wm.sketchfab_search_next", text="Next page", icon='RIGHTARROW')

    if 'current' not in props.search_results:
        results.row()
        results.row().label('Searching for models..')
        results.row()
        return

    if len(props.search_results['current']) == 0:
        results.row()
        results.row().label('No results found')
        results.row()
        return

    if props.use_preview:
        result_label = 'Select a model {}'.format('in current result page' if props.skfb_api.next_results_url else '{} results'.format(len(props.search_results['current'])))
        col.label(result_label)

        col.template_icon_view(bpy.context.window_manager, 'result_previews', show_labels=True, scale=8.0)
        # cc.template_icon_view(bpy.context.window_manager, 'result_previews', show_labels=True, scale=8.0)
        # cc2.template_icon_view(bpy.context.window_manager, 'result_previews', show_labels=True, scale=8.0)
        if bpy.context.window_manager.result_previews not in props.search_results['current']:
            p2=layout.box().column(align=True)
            p2.label('Fetching results...')
            return

        model = props.search_results['current'][bpy.context.window_manager.result_previews]
    else:
        draw_results_icons(results, props, 2)

    if not model:
        return

    if not model.license:
        print("request model info")
        props.skfb_api.request_model_info(model.uid)

    if props.skfb_api.is_user_logged() and not model.download_link:
        print("request download link")
        props.skfb_api.get_download_url(model.uid)

    p2=layout.column(align=True)
    p2.label('Name: {}'.format(model.title))
    p2.label('Author: {}'.format(model.author))

    p2.operator("wm.sketchfab_view", text="View on Sketchfab").model_uid = model.uid
    if model.license:
        p2.label('License {}'.format(model.license))
    else:
        p2.label('Fetching..')

    p3=layout.column(align=True)
    p4=layout.column(align=True)
    p3.enabled = props.skfb_api.is_user_logged() == True
    downloadlabel = "Download model ({})".format(model.download_size if model.download_size else 'fetching data') if p3.enabled else 'You need to be logged in to download a model'
    p3.operator("wm.sketchfab_download", icon_value=sketchfab_icon['skfb'].icon_id, text=downloadlabel).model_uid = model.uid

    p4.label('')
    p4.operator('wm.sketchfab_debug')

# utils
def set_log(log):
    get_sketchfab_props().status = log

def get_uid_from_thumbnail_url(thumbnail_url):
    return thumbnail_url.split('/')[4]

def get_uid_from_model_url(model_url):
    return model_url.split('/')[5]

def unzip_archive(archive_path):
    if os.path.exists(archive_path):
        import zipfile
        zip_ref = zipfile.ZipFile(archive_path, 'r')
        extract_dir = os.path.dirname(archive_path)
        zip_ref.extractall(extract_dir)
        zip_ref.close()
        gltf_file = os.path.join(extract_dir, 'scene.gltf')
        with open(gltf_file, 'r') as f:
            content = f.read()

        return gltf_file
    else:
        print('ERROR: archive doesn\'t exist')

def run_async(func):
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target = func, args = args, kwargs = kwargs)
        func_hl.start()
        return func_hl

    return async_func

def import_model(gltf_path):
    thread = ImportThread(gltf_path)
    thread.start()
    thread.join()

def toSearchRequest(query, animated, staffpick, face_count, category, sort_by):
    final_query = ''
    if animated:
        final_query = final_query +'&animated=true'

    if staffpick:
        final_query = final_query +'&staffpicked=true'

    if sort_by == 'LIKES':
        final_query = final_query + '&sort_by=-viewCount'
    elif sort_by == 'RECENT':
        final_query = final_query + '&sort_by=-publishedAt'
    elif sort_by == 'VIEWS':
        final_query = final_query + '&sort_by=-likeCount'

    if category != 'ALL':
        final_query = final_query + '&categories={}'.format(category)

    final_query = final_query + '&q=' + query

    return final_query

def parse_results(r, *args, **kwargs):
    skfb = get_sketchfab_props()
    json_data = r.json()
    skfb.search_results['current'] = OrderedDict()

    for result in json_data['results']:
        skfb.search_results['current'][result['uid']] = SketchfabModel(result)

        if True or not os.path.exists(os.path.join(SKFB_THUMB_DIR, result['uid']) + '.jpeg'):
            skfb.skfb_api.request_thumbnail(result['thumbnails'])

    if json_data['next']:
        skfb.skfb_api.next_results_url = json_data['next']

    if json_data['previous']:
        skfb.skfb_api.prev_results_url = json_data['previous']

# TREADED
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

            if total_length is None and r.content: # no content length header
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    done = int(100 * dl / total_length)

        # img_name = '{}'.format(uid)
        # img = bpy.data.images.load(thumbnail_path, check_existing=True)
        # img.name = img_name
        # tex = bpy.data.textures.new(img_name, 'IMAGE') if img_name not in bpy.data.textures else bpy.data.textures[img_name]
        # tex.image = img
        props =get_sketchfab_props()
        if uid not in props.custom_icons:
            props.custom_icons.load(uid, os.path.join(SKFB_THUMB_DIR, "{}.jpeg".format(uid)), 'IMAGE')



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
            blender_scene(gltf_data.scene, root_name=gltf_data.scene.gltf.json['asset']['extras']['title'])
        except:
            import traceback
            print(traceback.format_exc())

class DownloadThread(threading.Thread):
    def __init__(self, url, uid):
        self.url = url
        self.uid = uid
        threading.Thread.__init__(self)

    def run(self):
        r = requests.get(self.url, stream=True)
        temp_dir =  os.path.join(SKFB_MODEL_DIR, self.uid)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        archive_path = os.path.join(temp_dir, '{}.zip'.format(self.uid))

        if not os.path.exists(archive_path):
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
            with open(archive_path, "wb") as f:
                total_length = r.headers.get('content-length')

                if total_length is None: # no content length header
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

class GetRequestThread(threading.Thread):
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback
        threading.Thread.__init__(self)

    def run(self):
        r = requests.get(self.url, hooks={'response' : self.callback})

class LoginThread(threading.Thread):
    def __init__(self, url):
        self.url = url
        threading.Thread.__init__(self)

    def run(self):
        r = requests.post(self.url, hooks={'response' : self.handle_login})

    def handle_login(self, r, *args, **kwargs):
        if r.status_code == 200 and 'access_token' in r.json():
            bpy.context.window_manager.sketchfab_browser.skfb_api.access_token = r.json()['access_token']
            bpy.context.window_manager.sketchfab_browser.skfb_api.build_headers()
            print('Logged in => ' + bpy.context.window_manager.sketchfab_browser.skfb_api.access_token)
            bpy.context.window_manager.sketchfab_browser.skfb_api.request_user_info()
        else:
            if 'error_description' in r.json():
                bpy.ops.wm.sketchfab_error('EXEC_DEFAULT', message='Failed')
                # report('ERROR', r.json()['error_description'])
            else:
                print('Login failed.\n {}'.format(r.json()))


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
    bl_label = "Login"

    is_logged = BoolProperty()

    def draw(self, context):
        props = context.window_manager.sketchfab_api

        layout = self.layout
        layout.label("Sketchfab account:")
        col = layout.box().column(align=True)
        if props.skfb_api.is_user_logged():
            col.label('Successfully logged in {}'.format((props.skfb_api.get_user_info())))
            col.operator('wm.sketchfab_login', 'Logout').authenticate = False
        else:
            col.prop(props, "email")
            col.prop(props, "password")
            col.operator('wm.sketchfab_login', 'Login').authenticate = True

class BrowsEbuttonPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_test_2"
    bl_label = "Browse Sketchfab"

    def draw(self, context):
        # self.layout.box().column(align=True).operator('wm.sketchfab_browse', text="Browse Sketchfab")
        # self.layout.label('Debug')
        # self.layout.operator('wm.skfb_debug', 'PERFORM')
        draw_search(self.layout, context)

class FiltersPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_sketchfab_filters"
    bl_label = "Filters"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        # self.layout.box().column(align=True).operator('wm.sketchfab_browse', text="Browse Sketchfab")
        # self.layout.label('Debug')
        # self.layout.operator('wm.skfb_debug', 'PERFORM')
        draw_filters(self.layout, context)

class ResultsPanel(View3DPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_sketchfab_results"
    bl_label = "Results"

    def draw(self, context):
        # self.layout.box().column(align=True).operator('wm.sketchfab_browse', text="Browse Sketchfab")
        # self.layout.label('Debug')
        # self.layout.operator('wm.skfb_debug', 'PERFORM')
        draw_results(self.layout, context)


# Operators:
class SketchfabLogger(bpy.types.Operator):
    bl_idname = 'wm.sketchfab_login'
    bl_label = 'Sketchfab Login'

    authenticate = BoolProperty(default=True)

    def execute(self, context):
        wm = context.window_manager
        if self.authenticate and wm.sketchfab_api.password:
            wm.sketchfab_browser.skfb_api.login(wm.sketchfab_api.email, wm.sketchfab_api.password)
        else:
            wm.sketchfab_browser.skfb_api.logout()
            wm.sketchfab_api.password = ''
        return {'FINISHED'}

# Operator to perform search on Sketchfab
class SketchfabBrowse(bpy.types.Operator):
    bl_idname = "wm.sketchfab_browse"
    bl_label = "Browse Sketchfab"

    email = StringProperty(
            name="Email",
            default="you@example.com",
            )

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        draw_search(self.layout, context)

    def check(self, context):
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=900, height=850)

class SketchfabModel:
    def __init__(self, json_data):
        self.title = json_data['name']
        self.author = json_data['user']['displayName']
        self.uid = json_data['uid']
        self.vertex_count = json_data['vertexCount']
        self.face_count = json_data['faceCount']
        self.download_link = None
        self.license = None
        self.download_size = None
        self.thumbnail_url = os.path.join(SKFB_THUMB_DIR, '{}.jpeg'.format(self.uid))

class SketchfabModelView(bpy.types.Operator):
    bl_idname = "wm.sketchfab_modelview"
    bl_label = "Download Sketchfab model"

    addCurrentScene = BoolProperty(
                      name="Add to Scene",
                      default=True)

    uid = bpy.props.StringProperty(name="uid")

    model_info = {}
    preview = bpy.utils.previews.new()

    def execute(self, context):
        print('LOADING ' + uid)
        return {'FINISHED'}

    def parse_model_info(self, r, *args, **kwargs):
        if r.status_code != 200:
            print('Failed to retrieve model info')
            return

        json_data = r.json()
        model_info['name'] = json_data['name']

    def draw(self, context):
        position = [0.0, 0.0]
        width = 150.0
        height = 150.0
        import bgl
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBegin(bgl.GL_QUADS)
        bgl.glTexCoord2f(1, 1)
        bgl.glVertex2f(position[0],position[1])
        bgl.glTexCoord2f(0, 1)
        bgl.glVertex2f((position[0]+width),position[1])
        bgl.glTexCoord2f(0, 0)
        bgl.glVertex2f((position[0]+width), (position[1]+height))
        bgl.glTexCoord2f(1, 0)
        bgl.glVertex2f(position[0], (position[1]+height))
        bgl.glEnd()
        bgl.glDisable(bgl.GL_BLEND)

        skfb = context.window_manager.sketchfab_browser
        model = skfb.search_results['current'][self.uid]

        layout = self.layout
        bpy.context.window_manager.result_previews = self.uid
        col = layout.column()
        rr = col
        if not model:
            return

        if not model.license:
            skfb.skfb_api.request_model_info(model.uid)

        if not model.download_link:
            skfb.skfb_api.get_download_url(model.uid)

        rr.label(text='{} by {}'.format(model.title, model.author))
        rr.operator("wm.sketchfab_view", text="View on Sketchfab").model_uid = self.uid

        col.template_icon_view(bpy.context.window_manager, 'result_previews', show_labels=True, scale=8.0)

        col.label('License {}'.format(model.license))

        if model.download_link:
            col.operator("wm.sketchfab_download", text="Download model ({})".format(model.download_size if model.download_size else 'fetching data')).model_uid = self.uid

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

class SketchfabDownloadModel(bpy.types.Operator):
    bl_idname = "wm.sketchfab_download"
    bl_label = "Downloading"

    model_uid = bpy.props.StringProperty(name="uid")

    def execute(self, context):
        skfb_api = context.window_manager.sketchfab_browser.skfb_api
        skfb_api.get_archive(self.model_uid)
        return {'FINISHED'}

class ViewOnSketchfab(bpy.types.Operator):
    bl_idname = "wm.sketchfab_view"
    bl_label = "Open on Browser"

    model_uid = bpy.props.StringProperty(name="uid")

    def execute(self, context):
        import webbrowser
        webbrowser.open('{}/models/{}'.format(SKETCHFAB_URL, self.model_uid))
        return {'FINISHED'}

class SketchfabSearch(bpy.types.Operator):
    bl_idname = "wm.sketchfab_search"
    bl_label = "Search Sketchfab"

    def execute(self, context):
        # prepare request for search
        skfb = context.window_manager.sketchfab_browser
        skfb.custom_icons.clear()
        skfb_api = context.window_manager.sketchfab_browser.skfb_api
        skfb.search_results.clear()
        skfb.search_results_thumbnails.clear()
        skfb.skfb_api.prev_results_url = None
        skfb.skfb_api.next_results_url = None
        final_query = toSearchRequest(skfb.query, skfb.animated, skfb.staffpick, skfb.face_count, skfb.categories, skfb.sort_by)
        skfb_api.search(final_query, parse_results)

        return {'FINISHED'}

class SketchfabSearchNextResults(bpy.types.Operator):
    bl_idname = "wm.sketchfab_search_next"
    bl_label = "Search Sketchfab"

    def execute(self, context):
        # prepare request for search
        skfb = context.window_manager.sketchfab_browser
        skfb_api = context.window_manager.sketchfab_browser.skfb_api
        skfb.search_results.clear()
        skfb.search_results_thumbnails.clear()
        skfb_api.search_cursor(skfb_api.next_results_url, parse_results)

        return {'FINISHED'}

class SketchfabSearchPreviousResults(bpy.types.Operator):
    bl_idname = "wm.sketchfab_search_prev"
    bl_label = "Search Sketchfab"

    def execute(self, context):
        # prepare request for search
        skfb = context.window_manager.sketchfab_browser
        skfb_api = context.window_manager.sketchfab_browser.skfb_api
        skfb.search_results.clear()
        skfb.search_results_thumbnails.clear()
        skfb_api.search_cursor(skfb_api.prev_results_url, parse_results)

        return {'FINISHED'}

class SketchfabOpenModel(bpy.types.Operator):
    bl_idname = "wm.sketchfab_open"
    bl_label = "Downloading"

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

    message = StringProperty(name='Error', default='Failed')

    def execute(self, context):
        self.report({'INFO'}, "OOOK" )
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="I'm downloading your model!")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self, width=550)

class SketchfabDebug(bpy.types.Operator):
    bl_idname = "wm.skfb_debug"
    bl_label = "Downloading"

    def execute(self, context):
        context.window_manager.sketchfab_browser.skfb_api.request_categories()
        return {'FINISHED'}

classes = (
    # SketchfabBrowserPreferences,
    LoginPanel,
    BrowsEbuttonPanel,
    FiltersPanel,
    ResultsPanel,
    ViewOnSketchfab,
    SketchfabModelView,
    SketchfabDownloadModel,
    SketchfabLogger,
    SketchfabBrowse,
    SketchfabSearch,
    SketchfabSearchNextResults,
    SketchfabSearchPreviousResults,
    SketchfabBrowserProps,
    SketchfabLoginProps,
    SketchfabPopup,
    SketchfabDebug
    )



def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # addon_prefs = preferences()

    bpy.types.WindowManager.sketchfab_browser = PointerProperty(
                type=SketchfabBrowserProps)

    bpy.types.WindowManager.sketchfab_api = PointerProperty(
                type=SketchfabLoginProps)

    bpy.types.WindowManager.result_previews = EnumProperty(items=list_current_results)

    pcoll = bpy.utils.previews.new()
    pcoll.my_previews = ()

    preview_collection['main'] = pcoll

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.WindowManager.sketchfab_api
    del bpy.types.WindowManager.sketchfab_browser


if __name__ == "__main__":
    register()