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
import threading
import queue
import traceback

# other libs
from tinytag import TinyTag


'''path to sinusbot root_dir'''
root_dir = '/opt/ts3soundboard/'

# queues for communication between threads
q_create_slink = queue.Queue()
q_to_db = queue.Queue()


# CLIIO class -> handles all command line input/output
class CLIIO:

    # run!
    @classmethod
    def run(cls):
        argv = os.sys.argv[1:]

        if len(argv) > 0:
            counter = 0
            while argv[counter:]:
                re_value = BOX.commands(argv[counter].strip('-')[0])(*argv[counter:])
                cls.print_to_shell(re_value[0] + '\n')
                counter += re_value[1]
        else:
            BOX.commands('help')
            for cmd in cls.get_cmd('>> '):
                cmd = cmd.split(' ', 1)
                cls.print_to_shell(BOX.commands(cmd[0][0])(*cmd)[0])

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


# FILEIO class -> handles all input/output from/to files
class FILEIO:
    @staticmethod
    def create_slink_t(pill2kill):
        fe_log = None

        try:
            while not pill2kill.is_set() or q_create_slink.full():
                try:
                    source, e_path_n = q_create_slink.get(block=True)
                    link_dst = [f'{root_dir}data/store/' + str(*name) + f'/{e_path_n}' for name in FILEIO.get_folderns_and_files(f'{root_dir}data/store/') if isinstance(name, tuple)][1]
                    os.symlink(source, link_dst)
                    q_create_slink.task_done()

                except Exception as e:
                    fe_log = FILEIO.write_to_log('fe_log.txt', f'S_LINK_Error: {e}\n{traceback.format_exc()}')
                    continue

        finally:
            if fe_log:
                CLIIO.print_to_shell('file create_slink_t error -> {root_dir}fe_log.txt')
            CLIIO.print_to_shell('create_slink_t closed')

    @staticmethod
    def get_folderns_and_files(source_dir):
        for path, subdirs, files in os.walk(source_dir):
            yield (path.split('/')[-1],)

            if subdirs:
                yield subdirs

            for name in files:
                yield os.path.join(path, name)

    @staticmethod
    def del_all_slinks():
        sldir = [f'{root_dir}data/store/' + str(*name) + '/' for name in FILEIO.get_folderns_and_files(f'{root_dir}data/store/') if isinstance(name, tuple)][1]
        for path, subdirs, files in os.walk(sldir):
            for name in files:
                os.remove(os.path.join(path, name))

    @staticmethod
    def write_to_log(name, log_msg):
        with open(f'{root_dir}{name}', 'a') as log:
            log.write(log_msg)
        return True


# DBIO class -> handles all input/output from/to database(sqlite file... I know)
class DBIO:
    # creating command of the tabel files: db_conn.execute("CREATE TABLE files ( uuid STRING PRIMARY KEY ON CONFLICT IGNORE, artist STRING NOT NULL, title STRING NOT NULL, album STRING NOT NULL, trackinfo STRING NOT NULL, created DATETIME NOT NULL, createdby STRING NOT NULL , type STRING NOT NULL DEFAULT('file'), playcount INT NOT NULL DEFAULT(0), size INT NOT NULL DEFAULT(0));")
    # meths
    @staticmethod
    def to_db_t(pill2kill):  # <- code of to_db_t thread
        dbe_log = None
        db_conn = None

        try:
            while not pill2kill.is_set() or q_to_db.full():
                try:
                    evil = q_to_db.get(block=True)  # -> wait for input
                    db_conn = sqlite3.connect([path for path in FILEIO.get_folderns_and_files(f'{root_dir}data/db/') if isinstance(path, str) and path != '/opt/ts3soundboard/data/db/global.sqlite'][0])
                    db_cursor = db_conn.cursor()
                    if isinstance(evil, EVILS):
                        values_for_db = evil.for_db()
                        db_cursor.execute(f"INSERT INTO files (uuid, artist, title, album, trackinfo, created, createdby, type, playcount, size) VALUES ('{values_for_db['uuid']}', '{values_for_db['artist']}', '{values_for_db['title']}', '{values_for_db['album']}', '{values_for_db['trackinfo']}', '{values_for_db['created']}', '{values_for_db['createby']}', '{values_for_db['type']}', '{values_for_db['playcount']}', '{values_for_db['size']}');")
                        db_conn.commit()

                    else:
                        values_for_db = evil.for_db()
                        db_cursor.execute(f"INSERT INTO files (uuid, artist, title, album, trackinfo, created, createdby, type, playcount, size) VALUES ('{values_for_db['uuid']}', '{values_for_db['artist']}', '{values_for_db['title']}', '{values_for_db['album']}', '{values_for_db['trackinfo']}', '{values_for_db['created']}', '{values_for_db['createby']}', '{values_for_db['type']}', '{values_for_db['playcount']}', '{values_for_db['size']}');")
                        db_conn.commit()

                    q_to_db.task_done()

                except Exception as e:
                    dbe_log = FILEIO.write_to_log('dbe_log.txt', f'INSERT_DB_Error: {e}\n{traceback.format_exc()}')
                    continue

        finally:
            if dbe_log:
                CLIIO.print_to_shell('database to_db_t error -> {root_dir}dbe_log.txt')

            if db_conn:
                db_conn.close()
                CLIIO.print_to_shell('to_db_t closed')

    @staticmethod
    def del_db():
        dbe_log = None
        db_conn = None
        try:
            db_conn = sqlite3.connect([path for path in FILEIO.get_folderns_and_files(f'{root_dir}data/db/') if isinstance(path, str) and path != '/opt/ts3soundboard/data/db/global.sqlite'][0])
            db_cursor = db_conn.cursor()

            db_cursor.execute("DELETE FROM files;")
            db_conn.commit()
            return True

        except Exception as e:
            dbe_log = FILEIO.write_to_log('dbe_log.txt', f'INSERT_DB_Error: {e}\n{traceback.format_exc()}')
            return False

        finally:
            if dbe_log:
                CLIIO.print_to_shell('database del_db error')

            if db_conn:
                db_conn.close()
                CLIIO.print_to_shell('database closed\n')


# TOOLBOX class
class TOOLBOX:
    # meths
    @staticmethod
    def get_hash(path, hash_type='sha256'):
        func = getattr(hashlib, hash_type)()
        with open(path, 'rb') as f:
            for block in iter(lambda: f.read(2048*func.block_size), b''):
                func.update(block)

        return str(func.hexdigest())

    @staticmethod
    def get_time():
        return datetime.datetime.now()

    # Welp, I know ignoring errors is... kinda stupid
    @staticmethod
    def ignore_exception(IgnoreException=Exception, DefaultVal=None):
        def dec(function):
            def _dec(*args, **kwargs):
                try:
                    return function(*args, **kwargs)
                except IgnoreException:
                    return DefaultVal
            return _dec
        return dec


# BOX object
class BOX:
    # meths
    @classmethod
    def commands(cls, cmd):
        return{
            'a': lambda: cls.add,
            'h': lambda: cls.help,
            'e': lambda: os.sys.exit()
        }.get(cmd, lambda: cls.help)()

    @classmethod
    def add(cls, *args):
        ae_log = None
        arg_counter = 1

        if not args[1:]:
            args = (args[0], 'noarg')

        try:
            DBIO.del_db()
            FILEIO.del_all_slinks()

            pill2kill = threading.Event()  # -> cyanide pills

            create_slink_thread = threading.Thread(target=FILEIO.create_slink_t, args=(pill2kill,))
            create_slink_thread.daemon = True  # -> dies after main thread is closed
            create_slink_thread.start()

            to_db_thread = threading.Thread(target=DBIO.to_db_t, args=(pill2kill,))
            to_db_thread.daemon = True
            to_db_thread.start()

            for index, arg in enumerate(args[1:]):
                arg = arg.strip('\'\"')
                for evil in cls.get_EVIL(arg):
                    if isinstance(evil, EVILS):
                        CLIIO.print_to_shell(evil.get_song())
                        CLIIO.print_to_shell(f'{evil}\n')
                        q_create_slink.put((evil.get_song(), evil.get_path()))
                        q_to_db.put(evil)
                    elif isinstance(evil, EVIL):
                        CLIIO.print_to_shell(f'\n\n{evil.get_title()}\t{evil.get_uuid()}\n\n\n')
                        q_to_db.put(evil)
                    elif evil:
                        ae_log = evil

                    arg_counter += 1

        finally:
            if ae_log:
                CLIIO.print_to_shell('adding error -> {root_dir}ae_log')

            pill2kill.set()
            create_slink_thread.join()
            to_db_thread.join()
            return ('done', arg_counter)

    # recursive EVIL object generator -> literally evil code
    @classmethod
    def get_EVIL(cls, arg, parent=''):
        ae_log = None

        '''supp_formats = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.wma', '.opus', '.mp4')'''
        supp_formats = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.wma', '.opus')

        if os.path.isdir(arg):
            arg_last_c = arg[-1]
            for dn_or_s in FILEIO.get_folderns_and_files(arg):
                try:
                    if isinstance(dn_or_s, tuple):
                        parent_dir = dn_or_s[0]
                        if parent_dir:
                            evil = EVIL(parent_dir, parent)
                            parent = evil.get_uuid()
                            yield evil

                    elif isinstance(dn_or_s, list):
                        for dn in dn_or_s:
                            if arg_last_c is '/':
                                yield from cls.get_EVIL(f'{arg}{dn}', parent)
                            else:
                                yield from cls.get_EVIL(f'{arg}/{dn}', parent)
                        return

                    elif dn_or_s.endswith(supp_formats):
                        yield EVILS(dn_or_s, parent)

                except Exception as e:
                    ae_log = FILEIO.write_to_log('ae_log.txt', f'ADD_Error: {dn_or_s}: {e}\n{traceback.format_exc()}')
                    continue

        elif arg.endswith(supp_formats):
            yield EVILS(arg, parent)

        else:
            CLIIO.print_to_shell('What song do you want to add?')
            cls.get_EVIL([CLIIO.get_input('> ').strip('\'\"')])

        yield ae_log

    @classmethod
    def help(cls, *args):
        return ('useable commands and arguments are:\n\thelp\t--help -h\n\tadd\t--add -a\n\texit\t--exit -e', 1)


# super EVIL object -> data of folders
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


# EVILS object -> data of songs
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
    _track = 4
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
        self._track = TOOLBOX.ignore_exception()(int)(self._tag.track) or self._track
        self._genre = self._tag.genre or self._genre
        super().__init__(self._title, parent)
        self._type = 'file'
        self._trackinfo = f'{{"v":1,"uuid":"{self._uuid}","parent":"{self._parent}","type":"{self._type}","path":"{self._path}","codec":"-","duration":{self._duration},"bitrate":{self._bitrate},"samplerate":{self._samplerate},"filesize":{self._filesize},"filename":"{self._filename}","title":"{self._title}","artist":"{self._artist}","album":"{self._album}","track":{self._track},"genre":"{self._genre}"}}'

    def __repr__(self):
            return f'{self.__class__.__name__}({self._song})'

    def __str__(self):
            return f'{self._uuid}, {self._artist}, {self._title}, {self._album}, {self._trackinfo}, {self._created}, {self._createby}, {self._type}, {self._playcount}, {self._filesize}'

    # props
    def get_song(self):
        return self._song

    def get_path(self):
        return self._path


try:
    if __name__ == '__main__':
        os.sys.exit(CLIIO.run())

except Exception as e:
    CLIIO.print_to_shell(f'Oh no! Something has gone wrong. {e}\n{traceback.format_exc()}')

finally:
    print('cya')
