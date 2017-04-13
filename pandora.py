#!/usr/bin/python
'''
sinusbot script: pandora 07.04.2017 Erebos
'''
# standard libs
import os
import datetime
import hashlib
import uuid
import sqlite3
import traceback

# other libs
from tinytag import TinyTag


# CLIIO class
class CLIIO:

    # meths
    @classmethod
    def main(cls):
        box = BOX()
        argv = os.sys.argv[1:]

        if len(argv) > 0:
            counter = 0
            while argv[counter:]:
                re_value = box.commands(argv[counter].strip('-')[0])(*argv[counter:])
                cls.print_to_shell(re_value[0] + '\n')
                counter += re_value[1]
        else:
            box.commands('help')
            for cmd in cls.get_cmd('>> '):
                cmd = cmd.split(' ', 1)
                cls.print_to_shell(box.commands(cmd[0][0])(*cmd)[0])

    @staticmethod
    def get_cmd(placeholder):
        while True:
            yield input(placeholder)

    @staticmethod
    def get_input(placeholder):
        return input(placeholder)

    @staticmethod
    def print_to_shell(output_str):
        print(output_str)


# FILEIO class
class FILEIO:
    @staticmethod
    def get_folderns_and_files(root_dir):
        for path, subdirs, files in os.walk(root_dir):
            yield (path.split('/')[-1],)

            if subdirs:
                yield subdirs

            for name in files:
                yield os.path.join(path, name)

    @staticmethod
    def create_slink(source, link_dst):
        os.symlink(source, link_dst)

    @staticmethod
    def del_all_slinks(sldir):
        for path, subdirs, files in os.walk(sldir):
            for name in files:
                os.remove(os.path.join(path, name))


# DBIO class
class DBIO:
    # meths
    @staticmethod
    def to_db(box, hope):
        dbe_log = None
        db_conn = None
        try:
            '''"db_conn.execute("CREATE TABLE files ( uuid STRING PRIMARY KEY ON CONFLICT IGNORE, artist STRING NOT NULL, title STRING NOT NULL, album STRING NOT NULL, trackinfo STRING NOT NULL, created DATETIME NOT NULL, createdby STRING NOT NULL , type STRING NOT NULL DEFAULT('file'), playcount INT NOT NULL DEFAULT(0), size INT NOT NULL DEFAULT(0));")"'''
            root_dir = '/opt/ts3soundboard'
            db_conn = sqlite3.connect(f'{root_dir}/data/db/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483.sqlite')
            db_cursor = db_conn.cursor()

            for evil in hope.values():
                try:
                    values_for_db = evil.for_db()
                    db_cursor.execute(f"INSERT INTO files (uuid, artist, title, album, trackinfo, created, createdby, type, playcount, size) VALUES ('{values_for_db['uuid']}', '{values_for_db['artist']}', '{values_for_db['title']}', '{values_for_db['album']}', '{values_for_db['trackinfo']}', '{values_for_db['created']}', '{values_for_db['createby']}', '{values_for_db['type']}', '{values_for_db['playcount']}', '{values_for_db['size']}');")
                    db_conn.commit()
                    CLIIO.print_to_shell(values_for_db['uuid'])

                except Exception as e:
                    if not dbe_log:
                        dbe_log = open('dbe_log.txt', 'a')
                        dbe_log.write(f'INSERT_Hope_Error: {str(evil)} {e}\n{traceback.format_exc()}')
                    continue

            for evils in box:
                try:
                    values_for_db = evils.for_db()
                    db_cursor.execute(f"INSERT INTO files (uuid, artist, title, album, trackinfo, created, createdby, type, playcount, size) VALUES ('{values_for_db['uuid']}', '{values_for_db['artist']}', '{values_for_db['title']}', '{values_for_db['album']}', '{values_for_db['trackinfo']}', '{values_for_db['created']}', '{values_for_db['createby']}', '{values_for_db['type']}', '{values_for_db['playcount']}', '{values_for_db['size']}');")
                    db_conn.commit()
                    FILEIO.create_slink(evils.get_song(), f'{root_dir}/data/store/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483/{evils.get_path()}')
                    os.symlink(evils.get_song(), f'{root_dir}/data/store/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483/{evils.get_path()}')
                    CLIIO.print_to_shell(values_for_db['uuid'])

                except Exception as e:
                    if not dbe_log:
                        dbe_log = open('dbe_log.txt', 'a')
                        dbe_log.write(f'INSERT_Box_Error: {str(evils)} {e}\n{traceback.format_exc()}')
                    continue

        except Exception as e:
            CLIIO.print_to_shell(f'Error to_db {e}')
            exit()

        finally:
            if dbe_log:
                dbe_log.close()
                CLIIO.print_to_shell('database errorlog closed')

            if db_conn:
                db_conn.close()
                CLIIO.print_to_shell('database closed')

    @staticmethod
    def del_db():
        root_dir = '/opt/ts3soundboard'
        try:
            db_conn = sqlite3.connect(f'{root_dir}/data/db/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483.sqlite')
            db_cursor = db_conn.cursor()

            db_cursor.execute("DELETE FROM files WHERE type='file';")
            db_conn.commit()

            db_cursor.execute("DELETE FROM files WHERE type='folder';")
            db_conn.commit()

            FILEIO.del_all_slinks(f'{root_dir}/data/store/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483/')

        except Exception as e:
            CLIIO.print_to_shell(f'Error to_db {e}')
            exit()

        finally:
            if db_conn:
                db_conn.close()
                CLIIO.print_to_shell('database closed')


# TOOLBOX class
class TOOLBOX:
    # meths
    @staticmethod
    def get_hash(path, hash_type='sha256'):
        f = None
        try:
            func = getattr(hashlib, hash_type)()
            f = os.open(path, (os.O_RDONLY))
            for block in iter(lambda: os.read(f, 2048*func.block_size), b''):
                func.update(block)

        except Exception as e:
            CLIIO.print_to_shell(f'ERRER get_hash {e}')
            exit()

        finally:
            if f:
                os.close(f)
                CLIIO.print_to_shell('file closed')

        return str(func.hexdigest())

    @staticmethod
    def get_time():
        return datetime.datetime.now()


# BOX object
class BOX:
    # fields
    __box = []
    __hope = {}

    # ctor
    def __init__(self, box=[], hope={}):
        self.__box = box
        self.__hope = hope

    # meths
    def commands(self, cmd):
        return{
            'a': lambda: self.add_song,
            'l': lambda: self.list_songs,
            'h': lambda: self.help,
            'e': lambda: exit()
        }.get(cmd, lambda: self.help)()

    def add_song(self, *args):
        ae_log = None
        parent = ''

        if not args[1:]:
            print('shit')
            args = (args[0], 'noarg')

        '''supp_formats = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.wma', '.opus', '.mp4')'''
        supp_formats = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.wma', '.opus')
        arg_counter = 1

        try:
            for index, arg in enumerate(args[1:]):
                arg = arg.strip('\'\"')
                if os.path.isdir(arg):
                    for dn_or_s in FILEIO.get_folderns_and_files(arg):
                        try:
                            if isinstance(dn_or_s, tuple):
                                parent_dir = dn_or_s[0]
                                if parent_dir:
                                    if parent_dir not in self.__hope:
                                        evil = EVIL(parent_dir)
                                        self.__hope[parent_dir] = evil
                                        parent = evil.get_uuid()

                                    else:
                                        parent = self.__hope[parent_dir].get_uuid()
                                    CLIIO.print_to_shell(f'\n\n\n{parent_dir} {parent}\n\n\n')

                            elif isinstance(dn_or_s, list):
                                for dn in dn_or_s:
                                    evil = EVIL(dn, parent)
                                    self.__hope[dn] = evil
                                CLIIO.print_to_shell(dn_or_s)

                            elif dn_or_s.endswith(supp_formats):
                                CLIIO.print_to_shell(dn_or_s)
                                evils = EVILS(dn_or_s, parent)
                                self.__box.append(evils)
                                CLIIO.print_to_shell(str(evils) + '\n')

                        except Exception as e:
                            if not ae_log:
                                ae_log = open('ae_log.txt', 'a')
                                ae_log.write(f'ADD_Error: {dn_or_s}: {e}\n{traceback.format_exc()}')
                            continue

                elif arg.endswith(supp_formats):
                    CLIIO.print_to_shell(arg)
                    evils = EVILS(arg)
                    self.__box.append(evils)
                    CLIIO.print_to_shell(evils)
                else:
                    if index == 0:
                        CLIIO.print_to_shell('What song do you want to add?')
                        self.add_song([CLIIO.get_input('> ').strip('\'\"')])
                    break

                arg_counter += 1

        finally:
            if ae_log:
                ae_log.close()
                CLIIO.print_to_shell('adding errorlog closed')

            DBIO.del_db()
            DBIO.to_db(self.__box, self.__hope)
            return ('done', arg_counter)

    def list_songs(self, *args):
        out_string = ''
        for value in self.__box:
            if out_string == '':
                out_string += value.get_artist() + '\t' + value.get_title()
            else:
                out_string += '\n' + value.get_artist() + '\t' + value.get_title()
        return (out_string, 1)

    def help(self, *args):
        return ('useable commands and arguments are:\n\thelp\t--help -h\n\tadd\t--add -a\n\tlist\t--list -l\n\texit\t--exit -e', 1)


# super EVIL object
class EVIL:
    # fields
    _uuid = ''
    _artist = ''
    _title = ''
    _album = ''
    _trackinfo = ''
    _parent = ''
    _created = ''
    _createby = 'fd3591e0-97e0-4a5f-ad08-697c37f0e2bc'
    _type = 'folder'
    _playcount = 0
    _size = 0

    # ctor
    def __init__(self, title, parent=''):
        self._uuid = str(uuid.uuid4())
        self._artist = self._artist
        self._title = title
        self._album = self._album
        self._created = TOOLBOX.get_time()
        self._createby = self._createby
        self._type = self._type
        self._playcount = self._playcount
        self._size = self._size
        self._parent = parent
        self._trackinfo = f'{{"v":1,"uuid":"{self._uuid}","parent":"{self._parent}","type":"{self._type}","path":"","title":"{self._title}"}}'

    def __repr__(self):
            return f'{self.__class__.__name__}({self._title})'

    def __str__(self):
            return f'{self._uuid}, {self._artist}, {self._title}, {self._album}, {self._trackinfo}, {self._parent}, {self._created}, {self._createby}, {self._type}, {self._playcount}'

    # props
    def get_uuid(self):
        return self._uuid

    def get_title(self):
        return self._title

    def for_db(self):
        return {
            'uuid': self._uuid,
            'artist': self._artist.replace('\'', '\'\''),
            'title': self._title.replace('\'', '\'\''),
            'album': self._album.replace('\'', '\'\''),
            'trackinfo': self._trackinfo.replace('\'', '\'\''),
            'created': self._created,
            'createby': self._createby,
            'type': self._type,
            'playcount': self._playcount,
            'size': self._size
        }


# EVILS object
class EVILS(EVIL):
    # fields
    _song = ''
    _tag = ''
    _path = ''
    _duration = 0
    _bitrate = 0
    _samplerate = 0
    _filesize = 0
    _filename = ''
    _track = ''
    _genre = ''

    # ctor
    def __init__(self, song, parent=''):
        self._song = song
        self._tag = TinyTag.get(song)
        self._path = TOOLBOX.get_hash(song)
        self._artist = self._tag.artist or self._artist
        self._title = self._tag.title or self._title
        self._album = self._tag.album or self._album
        self._duration = int(self._tag.duration * 1000)
        self._bitrate = int(self._tag.bitrate * 1000)
        self._samplerate = int(self._tag.samplerate)
        self._filesize = self._tag.filesize
        self._filename = self._tag.title or self._filename
        self._track = self._tag.track or self._track
        self._genre = self._tag.genre or self._genre
        super().__init__(self._title, parent)
        self._type = 'file'
        self._trackinfo = f'{{"v":1,"uuid":"{self._uuid}","parent":"{self._parent}","type":"{self._type}","path":"{self._path}","codec":"-","duration":{self._duration},"bitrate":{self._bitrate},"samplerate":{self._samplerate},"filesize":{self._filesize},"filename":"{self._filename}","title":"{self._title}","artist":"{self._artist}","album":"{self._album}","track":{self._track},"genre":"{self._genre}"}}'

    def __repr__(self):
            return f'{self.__class__.__name__}({self._song})'

    def __str__(self):
            return f'{self._uuid}, {self._artist}, {self._title}, {self._album}, {self._trackinfo}, {self._created}, {self._createby}, {self._type}, {self._playcount}, {self._filesize}'

    # props
    def get_artist(self):
        return self._artist

    def get_path(self):
        return self._path

    def get_song(self):
        return self._song


try:
    if __name__ == '__main__':
        CLIIO.main()

except Exception as e:
    CLIIO.print_to_shell(f'Oh no! Something has gone wrong. {e}\n{traceback.format_exc()}')

finally:
    print('cya')
    exit()
