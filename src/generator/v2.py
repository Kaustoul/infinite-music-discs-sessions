# -*- coding: utf-8 -*-
#
#Infinite Music Discs generator module implementation
#Generation tool, datapack design, and resourcepack design by link2_thepast
#
#Generates datapack v2.0
from typing import Union, TextIO

import os
import json
import shutil
import zipfile

from src.definitions import Constants, Helpers, Status, DiscListContents
from src.generator.base import VirtualGenerator



class GeneratorV2(VirtualGenerator):

    #TODO: what happens when command syntax changes? Can't be backwards compatible
    #  and copy from reference files... different sets of reference files?
    #  command-to-string generation engine? too complex to maintain?
    def generate_datapack(self, entry_list: DiscListContents, user_settings={}):

        #read settings
        pack_format = user_settings.get('version').get('dp', Constants.DEFAULT_PACK_FORMAT)
        offset = user_settings.get('offset', 0)

        for i,entry in enumerate(entry_list.entries):
            entry.custom_model_data = i + offset + 1

        datapack_name = user_settings.get('name', Constants.DEFAULT_PACK_NAME)
        datapack_name = datapack_name + Constants.DATAPACK_SUFFIX

        dp_version_str = f'v{self._version_major}.{self._version_minor}'

        #write datapack
        try:
            self.write_dp_framework(entry_list, datapack_name, pack_format)

            self.write_func_tags(datapack_name)
            self.write_advancements(datapack_name)

            self.write_global_funcs(datapack_name, dp_version_str)
            self.write_funcs_to_register_jukebox(datapack_name)
            self.write_jukebox_tick_funcs(datapack_name)
            self.write_player_tick_funcs(datapack_name)
            self.write_funcs_entry_per_disc(datapack_name, entry_list)
            self.write_creeper_loottable(datapack_name, entry_list)
            self.write_per_disc_funcs(datapack_name, entry_list)

        except UnicodeEncodeError:
            return Status.BAD_UNICODE_CHAR

        except FileExistsError:
            return Status.PACK_DIR_IN_USE

        #copy pack.png
        try:
            if 'pack' in user_settings:
                shutil.copyfile(user_settings['pack'], os.path.join(datapack_name, 'pack.png'))
            else:
                raise FileNotFoundError

        except (FileNotFoundError, IOError):
            print("Warning: No pack.png found. Your datapack will not have an icon.")

        #move pack to .zip, if selected
        use_zip = user_settings.get('zip', False)

        if use_zip:
            zip_status = self.zip_pack(datapack_name)

            if(zip_status != Status.SUCCESS):
                print("Error: Failed to zip datapack. Datapack has been generated as folder instead.")
                return zip_status

        return Status.SUCCESS

    # generate directory structure and framework files
    #TODO: move inside dp immediately so there's no risk of breaking external stuff
    def write_dp_framework(self, entry_list: DiscListContents, datapack_name: str, pack_format: int):

        #try to remove old datapack. If datapack folder exists but mcmeta does not,
        #  then this directory may belong to something else so don't delete
        if os.path.isdir(datapack_name):
            if not os.path.isfile(os.path.join(datapack_name, 'pack.mcmeta')):
                raise FileExistsError
            else:
                shutil.rmtree(datapack_name, ignore_errors=True)

        #build datapack directory tree
        os.makedirs(os.path.join(datapack_name, 'data', 'minecraft', 'tags', 'functions'))
        os.makedirs(os.path.join(datapack_name, 'data', 'minecraft', 'loot_tables', 'entities'))
        os.makedirs(os.path.join(datapack_name, 'data', datapack_name, 'functions'))
        os.makedirs(os.path.join(datapack_name, 'data', datapack_name, 'advancements'))

        #write 'pack.mcmeta'
        with open(os.path.join(datapack_name, 'pack.mcmeta'), 'w', encoding='utf-8') as pack:
            pack.write(json.dumps({
                'pack': {
                    'pack_format': pack_format,
                    'description': (Constants.DATAPACK_DESC % len(entry_list.internal_names))
                }
            }, indent=4))

    # generate minecraft function tags
    def write_func_tags(self, datapack_name: str):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'minecraft', 'tags', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', 'minecraft', 'tags', 'functions')

        #write 'load.json'
        self.copy_json_with_fmt(os.path.join(ref_dir, 'load.json'),
                                os.path.join(dst_dir, 'load.json'),
                                locals())

        #write 'tick.json'
        self.copy_json_with_fmt(os.path.join(ref_dir, 'tick.json'),
                                os.path.join(dst_dir, 'tick.json'),
                                locals())

    # generate advancements
    def write_advancements(self, datapack_name: str):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'advancements')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'advancements')

        #write 'placed_disc.json'
        self.copy_json_with_fmt(os.path.join(ref_dir, 'placed_disc.json'),
                                os.path.join(dst_dir, 'placed_disc.json'),
                                locals())

        #write 'placed_jukebox.json'
        self.copy_json_with_fmt(os.path.join(ref_dir, 'placed_jukebox.json'),
                                os.path.join(dst_dir, 'placed_jukebox.json'),
                                locals())

    # generate global functions
    def write_global_funcs(self, datapack_name: str, dp_version_str: str):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'functions')

        #write 'setup_load.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'setup_load.mcfunction'),
                           os.path.join(dst_dir, 'setup_load.mcfunction'),
                           locals())

        #write 'watchdog_reset_tickcount.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'watchdog_reset_tickcount.mcfunction'),
                           os.path.join(dst_dir, 'watchdog_reset_tickcount.mcfunction'),
                           locals())

        #write 'help.mcfunction'
        #users can run help function to see an FAQ + links to help resources
        self.copy_func_with_fmt(os.path.join(ref_dir, 'help.mcfunction'),
                           os.path.join(dst_dir, 'help.mcfunction'),
                           locals())

    # generate 'jukebox registration' functions
    # every jukebox must be registered with the datapack to detect
    #    discs inserted/removed with hoppers
    def write_funcs_to_register_jukebox(self, datapack_name: str):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'functions')

        #write 'on_placed_disc.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'on_placed_disc.mcfunction'),
                           os.path.join(dst_dir, 'on_placed_disc.mcfunction'),
                           locals())

        #write 'on_placed_jukebox.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'on_placed_jukebox.mcfunction'),
                           os.path.join(dst_dir, 'on_placed_jukebox.mcfunction'),
                           locals())

        #write 'raycast_start.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'raycast_start.mcfunction'),
                           os.path.join(dst_dir, 'raycast_start.mcfunction'),
                           locals())

        #write 'raycast_step.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'raycast_step.mcfunction'),
                           os.path.join(dst_dir, 'raycast_step.mcfunction'),
                           locals())

        #write 'raycast_hit.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'raycast_hit.mcfunction'),
                           os.path.join(dst_dir, 'raycast_hit.mcfunction'),
                           locals())

        #write 'register_jukebox_marker.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'register_jukebox_marker.mcfunction'),
                           os.path.join(dst_dir, 'register_jukebox_marker.mcfunction'),
                           locals())

    # generate jukebox related every-tick functions
    # not all functions run every tick; some are simply called by
    #    functions that run every tick
    def write_jukebox_tick_funcs(self, datapack_name: str):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'functions')

        #write 'jukebox_event_tick.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'jukebox_event_tick.mcfunction'),
                           os.path.join(dst_dir, 'jukebox_event_tick.mcfunction'),
                           locals())

        #write 'destroy_jukebox_marker.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'destroy_jukebox_marker.mcfunction'),
                           os.path.join(dst_dir, 'destroy_jukebox_marker.mcfunction'),
                           locals())

        #write 'jukebox_tick_timers.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'jukebox_tick_timers.mcfunction'),
                           os.path.join(dst_dir, 'jukebox_tick_timers.mcfunction'),
                           locals())

        #TODO: in multiplayer is marker tagged multiple times, once per player?
        #write 'stop_11.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'stop_11.mcfunction'),
                           os.path.join(dst_dir, 'stop_11.mcfunction'),
                           locals())

        #write 'jukebox_check_playing.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'jukebox_check_playing.mcfunction'),
                           os.path.join(dst_dir, 'jukebox_check_playing.mcfunction'),
                           locals())

        #TODO: technically should check if custommodeldata is within acceptable range
        #write 'jukebox_on_play.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'jukebox_on_play.mcfunction'),
                           os.path.join(dst_dir, 'jukebox_on_play.mcfunction'),
                           locals())

        #write 'pre_play.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'pre_play.mcfunction'),
                           os.path.join(dst_dir, 'pre_play.mcfunction'),
                           locals())

        #write 'register_jukebox_listener.mcfunction'
        #TODO: 2 lists is sloppy, try to optimize
        self.copy_func_with_fmt(os.path.join(ref_dir, 'register_jukebox_listener.mcfunction'),
                           os.path.join(dst_dir, 'register_jukebox_listener.mcfunction'),
                           locals())

        #write 'jukebox_on_stop.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'jukebox_on_stop.mcfunction'),
                           os.path.join(dst_dir, 'jukebox_on_stop.mcfunction'),
                           locals())

    # generate player related every-tick functions
    def write_player_tick_funcs(self, datapack_name: str):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'functions')

        #write 'register_players_tick.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'register_players_tick.mcfunction'),
                           os.path.join(dst_dir, 'register_players_tick.mcfunction'),
                           locals())

        #TODO: different global id per-datapack?
        #write 'register_player.mcfunction'
        self.copy_func_with_fmt(os.path.join(ref_dir, 'register_player.mcfunction'),
                           os.path.join(dst_dir, 'register_player.mcfunction'),
                           locals())

    # generate files with lines for every disc
    # used to select which disc-specific function to run
    def write_funcs_entry_per_disc(self, datapack_name: str, entry_list: DiscListContents):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'functions')

        #write 'play.mcfunction'
        self.copy_lines_to_func_with_fmt(os.path.join(ref_dir, 'play.mcfunction'),
                                      os.path.join(dst_dir, 'play.mcfunction'),
                                      entry_list,
                                      locals())

        #write 'play_duration.mcfunction'
        self.copy_lines_to_func_with_fmt(os.path.join(ref_dir, 'play_duration.mcfunction'),
                                      os.path.join(dst_dir, 'play_duration.mcfunction'),
                                      entry_list,
                                      locals())

        #write 'stop.mcfunction'
        self.copy_lines_to_func_with_fmt(os.path.join(ref_dir, 'stop.mcfunction'),
                                      os.path.join(dst_dir, 'stop.mcfunction'),
                                      entry_list,
                                      locals())

        #write 'set_disc_track.mcfunction'
        #note that v2 generator doesn't use ReplaceItemCommand for pre-1.17 compatibility
        #  since v2 datapack is not compatible with pre-1.19.4 versions anyway
        self.copy_lines_to_func_with_fmt(os.path.join(ref_dir, 'set_disc_track.mcfunction'),
                                      os.path.join(dst_dir, 'set_disc_track.mcfunction'),
                                      entry_list,
                                      locals())

        #write 'give_all_discs.mcfunction'
        self.copy_lines_to_func_with_fmt(os.path.join(ref_dir, 'give_all_discs.mcfunction'),
                                      os.path.join(dst_dir, 'give_all_discs.mcfunction'),
                                      entry_list,
                                      locals())

    # generate creeper loottable
    def write_creeper_loottable(self, datapack_name: str, entry_list: DiscListContents):

        dp_base = os.getcwd()
        dp_dir = os.path.join(dp_base, datapack_name, 'data', 'minecraft', 'loot_tables', 'entities')

        creeper_mdentries = []
        creeper_mdentries.append({'type':'minecraft:tag', 'weight':1, 'name':'minecraft:creeper_drop_music_discs', 'expand':True})

        for entry in entry_list.entries:
            creeper_mdentries.append({
                'type':'minecraft:item',
                'weight':1,
                'name':'minecraft:music_disc_11',
                'functions':[{
                    'function':'minecraft:set_nbt',
                    'tag':f'{{CustomModelData:{entry.custom_model_data}, HideFlags:32, display:{{Lore:[\"\\\"\\\\u00a77{entry.title}\\\"\"]}}}}'
                }]
            })

        creeper_normentries = [{
            'type':'minecraft:item',
            'functions':[{
                    'function':'minecraft:set_count',
                    'count':{'min':0.0, 'max':2.0, 'type':'minecraft:uniform'}
                }, {
                    'function':'minecraft:looting_enchant',
                    'count':{'min':0.0, 'max':1.0}
                }],
            'name':'minecraft:gunpowder'
        }]

        creeper_json = {
            'type':'minecraft:entity',
            'pools':[
                {'rolls':1, 'entries':creeper_normentries},
                {'rolls':1, 'entries':creeper_mdentries, 'conditions':[{
                    'condition':'minecraft:entity_properties',
                    'predicate':{'type':'#minecraft:skeletons'},
                    'entity':'killer'
                }]
            }]
        }

        #write 'creeper.json'
        with open(os.path.join(dp_dir, 'creeper.json'), 'w', encoding='utf-8') as creeper:
            creeper.write(json.dumps(creeper_json, indent=4))

    # generate per-disc functions
    # each disc gets a copy of these functions
    def write_per_disc_funcs(self, datapack_name: str, entry_list: DiscListContents):

        ref_base = os.path.abspath(Helpers.data_path())
        dst_base = os.getcwd()

        ref_dir = os.path.join(ref_base, 'reference', 'data', 'reference', 'functions')
        dst_dir = os.path.join(dst_base, datapack_name, 'data', datapack_name, 'functions')

        for entry in entry_list.entries:
            #make directory for this disc's functions
            os.makedirs(os.path.join(dst_dir, entry.internal_name))

            #write '*/play.mcfunction' files
            self.copy_func_with_fmt(os.path.join(ref_dir, 'disc', 'play.mcfunction'),
                               os.path.join(dst_dir, entry.internal_name, 'play.mcfunction'),
                               locals())

            #write '*/play_duration.mcfunction' files
            self.copy_func_with_fmt(os.path.join(ref_dir, 'disc', 'play_duration.mcfunction'),
                               os.path.join(dst_dir, entry.internal_name, 'play_duration.mcfunction'),
                               locals())

            #write '*/stop.mcfunction' files
            self.copy_func_with_fmt(os.path.join(ref_dir, 'disc', 'stop.mcfunction'),
                               os.path.join(dst_dir, entry.internal_name, 'stop.mcfunction'),
                               locals())

            #write 'give_*_disc.mcfunction' files
            self.copy_func_with_fmt(os.path.join(ref_dir, 'give_disc.mcfunction'),
                               os.path.join(dst_dir, f'give_{entry.internal_name}.mcfunction'),
                               locals())



    def generate_resourcepack(self, entry_list: DiscListContents, user_settings={}, cleanup_tmp: bool = True):

        #read settings
        pack_format = user_settings.get('version').get('rp', Constants.DEFAULT_PACK_FORMAT)
        offset = user_settings.get('offset', 0)

        resourcepack_name = user_settings.get('name', Constants.DEFAULT_PACK_NAME)
        resourcepack_name = resourcepack_name + Constants.RESOURCEPACK_SUFFIX

        #capture base dir
        base_dir = os.getcwd()

        #write resourcepack
        #use chdir to move around directory structure and reduce file paths
        try:
            self.write_rp_framework(entry_list, resourcepack_name, pack_format)

            os.chdir(os.path.join(base_dir, resourcepack_name, 'assets', 'minecraft', 'models', 'item'))
            self.write_item_models(entry_list, offset)

            os.chdir(os.path.join(base_dir, resourcepack_name, 'assets', 'minecraft'))
            self.copy_assets(entry_list)

        except UnicodeEncodeError:
            return Status.BAD_UNICODE_CHAR
        
        except FileExistsError:
            return Status.PACK_DIR_IN_USE
        
        finally:
            os.chdir(base_dir)

        #copy pack.png
        try:
            if 'pack' in user_settings:
                shutil.copyfile(user_settings['pack'], os.path.join(resourcepack_name, 'pack.png'))
            else:
                raise FileNotFoundError

        except (FileNotFoundError, IOError):
            print("Warning: No pack.png found. Your resourcepack will not have an icon.")

        #move pack to .zip, if selected
        use_zip = user_settings.get('zip', False)

        if use_zip:
            zip_status = self.zip_pack(resourcepack_name)

            if(zip_status != Status.SUCCESS):
                print("Error: Failed to zip resourcepack. Resourcepack has been generated as folder instead.")
                return zip_status

        #cleanup temp work directory
        if cleanup_tmp:
            shutil.rmtree(self.tmp_path, ignore_errors=True)
            self.tmp_path = None

        return Status.SUCCESS

    # generate directory structure and framework files
    def write_rp_framework(self, entry_list: DiscListContents, resourcepack_name: str, pack_format: int):

        #try to remove old resourcepack. If resourcepack folder exists but mcmeta does not,
        #  then this directory may belong to something else so don't delete
        if os.path.isdir(resourcepack_name):
            if not os.path.isfile(os.path.join(resourcepack_name, 'pack.mcmeta')):
                raise FileExistsError
            else:
                shutil.rmtree(resourcepack_name, ignore_errors=True)

        #build resourcepack directory tree
        os.makedirs(os.path.join(resourcepack_name, 'assets', 'minecraft', 'models', 'item'))
        os.makedirs(os.path.join(resourcepack_name, 'assets', 'minecraft', 'sounds', 'records'))
        os.makedirs(os.path.join(resourcepack_name, 'assets', 'minecraft', 'textures', 'item'))

        #write 'pack.mcmeta'
        with open(os.path.join(resourcepack_name, 'pack.mcmeta'), 'w', encoding='utf-8') as pack:
            pack.write(json.dumps({
                'pack':{
                    'pack_format':pack_format,
                    'description':(Constants.RESOURCEPACK_DESC % len(entry_list.internal_names))
                }
            }, indent=4))

        #write 'sounds.json'
        with open(os.path.join(resourcepack_name, 'assets', 'minecraft', 'sounds.json'), 'w', encoding='utf-8') as sounds:
            json_dict = {}

            for name in entry_list.internal_names:
                sound = {
                    'sounds':[{
                        'name':f'records/{name}',
                        'stream':True
                    }]
                }

                json_dict[f'music_disc.{name}'] = sound

            sounds.write(json.dumps(json_dict, indent=4))

    # generate item models
    def write_item_models(self, entry_list: DiscListContents, offset: int):

        #write 'music_disc_11.json'
        with open('music_disc_11.json', 'w', encoding='utf-8') as music_disc_11:
            json_list = []
            for i, name in enumerate(entry_list.internal_names):
                j = i + offset + 1

                json_list.append({
                    'predicate':{'custom_model_data':j},
                    'model':f'item/music_disc_{name}'
                })

            music_disc_11.write(json.dumps({
                'parent':'item/generated',
                'textures':{'layer0': 'item/music_disc_11'},
                'overrides':json_list
            }, indent=4))

        #write 'music_disc_*.json' files
        for name in entry_list.internal_names:
            with open(f'music_disc_{name}.json', 'w', encoding='utf-8') as music_disc:
                music_disc.write(json.dumps({
                    'parent':'item/generated',
                    'textures':{'layer0': f'item/music_disc_{name}'}
                }, indent=4))

    # generate assets dir
    def copy_assets(self, entry_list: DiscListContents):

        #copy sound and texture files
        for entry in entry_list.entries:
            shutil.copyfile(entry.track_file, os.path.join('sounds', 'records', f'{entry.internal_name}.ogg'))
            shutil.copyfile(entry.texture_file, os.path.join('textures', 'item', f'music_disc_{entry.internal_name}.png'))



    def zip_pack(self, pack_name: str):
        pack_name_zip = pack_name + Constants.ZIP_SUFFIX

        try:
            #remove old zip
            if os.path.exists(pack_name_zip):
                os.remove(pack_name_zip)

            #generate new zip archive
            with zipfile.ZipFile(pack_name_zip, 'w') as rp_zip:
                for root, dirs, files in os.walk(pack_name):
                    root_zip = os.path.relpath(root, pack_name)

                    for file in files:
                        rp_zip.write(os.path.join(root, file), os.path.join(root_zip, file))

            #remove pack folder
            if os.path.exists(pack_name_zip):
                shutil.rmtree(pack_name, ignore_errors=True)

        except (OSError, zipfile.BadZipFile):
            #remove bad zip, if it exists
            if os.path.exists(pack_name_zip):
                os.remove(pack_name_zip)

            return Status.BAD_ZIP
        
        return Status.SUCCESS

    # helper function that copies the contents of f_src into f_dst, while applying
    #   string formatting to every line
    # if called with fmt_dict=locals(), it will effectively format each line of
    #   f_src like an f-string, with all the variables in the caller's scope
    def copy_func_with_fmt(self, f_src: str, f_dst: str, fmt_dict):
        with open(f_src, 'r', encoding='utf-8') as src:
            with open(f_dst, 'w', encoding='utf-8') as dst:

                for line in src.readlines():

                    #decompose fmt_dict into its key-value pairs so
                    #  it can be used for string formatting
                    line_fmt = line.format(**fmt_dict)
                    dst.write(line_fmt)

    # helper function that copes the contents of f_src into f_dst once per
    #   disc. Also applies string formatting to every line
    #
    # if called with fmt_dict=locals(), it will effectively format each line of
    #   f_src like an f-string, with all the variables in the caller's scope.
    #   "entry" is explicitly included in the formatting since it didn't exist
    #   in the caller's scope
    def copy_lines_to_func_with_fmt(self, f_src: str, f_dst: str, entry_list: DiscListContents, fmt_dict):
        with open(f_src, 'r', encoding='utf-8') as src:
            with open(f_dst, 'w', encoding='utf-8') as dst:

                #return to the top of f_src with every disc to reread the same contents
                #more efficient than reopening the file every time
                for entry in entry_list.entries:
                    src.seek(0)
                    for line in src.readlines():

                        #decompose fmt_dict into its key-value pairs so
                        #  it can be used for string formatting
                        line_fmt = line.format(**fmt_dict, entry=entry)
                        dst.write(line_fmt)

    # recursively apply string formatting to any string-type
    #   value in the given json dict or json sub-list
    def fmt_json(self, json: Union[dict, list], fmt_dict):

        #change iterator depending on type, so that the iterated
        #  object's contents can always be accessed by json[k]
        #dict: json[key of element]
        #list: json[index of element]
        if type(json) == list:
            iterator = [i for i in range(len(json))]
        else:
            iterator = [k for k in json]

        for k in iterator:

            if type(json[k]) == str:
                json[k] = json[k].format(**fmt_dict)

            elif type(json[k]) in [dict, list]:
                json[k] = self.fmt_json(json[k], fmt_dict)

        return json

    # apply string formatting to each element of the given
    #   list and combine them into a single path string.
    # use ** to expand fmt_dict into kwargs and use *
    #   to splat fmt_path into multiple strings for
    #   os.path.join
    def fmt_path(self, path: list, fmt_dict) -> str:
        fmt_path = [p.format(**fmt_dict) for p in path]
        return os.path.join(*fmt_path)



    def write_single(self, src: dict, fmt_dict):
        fmt_dict.update(locals())
        f_dst = self.fmt_path(src['path'], fmt_dict)

        with open(f_dst, 'w', encoding='utf-8') as dst:
            self.write_pack_file(src, dst, fmt_dict)

    def write_copy(self, src: dict, entry_list: DiscListContents, fmt_dict):
        for entry in entry_list.entries:
            fmt_dict.update(locals())
            f_dst = self.fmt_path(src['path'], fmt_dict)

            with open(f_dst, 'w', encoding='utf-8') as dst:
                self.write_pack_file(src, dst, fmt_dict)

    def write_copy_within(self, src: dict, entry_list: DiscListContents, fmt_dict):
        f_dst = self.fmt_path(src['path'], fmt_dict)

        with open(f_dst, 'w', encoding='utf-8') as dst:
            for entry in entry_list.entries:
                fmt_dict.update(locals())

                self.write_pack_file(src, dst, fmt_dict)

    def write_pack_file(self, src: dict, dst: TextIO, fmt_dict):
        if type(src['contents']) == str:
            dst.writelines(src['contents'].lstrip().format(**fmt_dict))

        elif type(src['contents']) == dict:
            json.dump(self.fmt_json(src['contents'], fmt_dict), dst, indent=4)

    # helper function that copies the contents of f_src into f_dst, while applying
    #   string formatting to every string-type value in the given json file
    # if called with fmt_dict=locals(), it will effectively format each line of
    #   f_src like an f-string, with all the variables in the caller's scope
    def copy_json_with_fmt(self, f_src: str, f_dst: str, fmt_dict):
        with open(f_src, 'r', encoding='utf-8') as src:
            with open(f_dst, 'w', encoding='utf-8') as dst:

                src_fmt = json.load(src)
                src_fmt = self.fmt_json(src_fmt, fmt_dict)
                dst.write(json.dumps(src_fmt, indent=4))


