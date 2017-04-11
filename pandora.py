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

# other libs
from tinytag import TinyTag


# CLI
class CLI:

    # meths
    @staticmethod
    def main():
        box = BOX()
        argv = os.sys.argv[1:]

        if len(argv) > 0:
            counter = 0
            while argv[counter:]:
                re_value = box.commands(argv[counter].strip('-')[0])(*argv[counter:])
                print(re_value[0] + '\n')
                counter += re_value[1]
        else:
            box.commands('help')
            for cmd in CLI.get_cmd('>> '):
                # cmd = cmd.split(' \'')
                cmd = cmd.split(' ', 1)
                print(box.commands(cmd[0][0])(*cmd)[0])

        print(box.exit()[0])

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


# DB
class DB:
    # meths
    @staticmethod
    def to_db(box):
        dbe_log = None
        db_conn = None
        try:
            root_dir = '/opt/ts3soundboard'
            # db_conn = sqlite3.connect('C:\\Users\\Toko\\Music\\4dd88ac7-e609-4ae5-a5f3-5fd260f6f483.sqlite')
            db_conn = sqlite3.connect(f'{root_dir}/data/db/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483.sqlite')
            db_cursor = db_conn.cursor()
            # db_conn.execute("CREATE TABLE files ( uuid STRING PRIMARY KEY ON CONFLICT IGNORE, artist STRING NOT NULL, title STRING NOT NULL, album STRING NOT NULL, trackinfo STRING NOT NULL, created DATETIME NOT NULL, createdby STRING NOT NULL , type STRING NOT NULL DEFAULT('file'), playcount INT NOT NULL DEFAULT(0), size INT NOT NULL DEFAULT(0));")
            # print('db created')

            for evils in box:
                try:
                    values_for_db = evils.for_db()
                    db_cursor.execute(f"INSERT INTO files (uuid, artist, title, album, trackinfo, created, createdby, type, playcount, size) VALUES ('{values_for_db['uuid']}', '{values_for_db['artist']}', '{values_for_db['title']}', '{values_for_db['album']}', '{values_for_db['trackinfo']}', '{values_for_db['created']}', '{values_for_db['createby']}', '{values_for_db['type']}', '{values_for_db['playcount']}', '{values_for_db['size']}');")
                    # db_conn.execute(f"INSERT INTO files (uuid) VALUES ('{values_for_db['uuid']}');")
                    db_conn.commit()
                    os.symlink(evils.get_song(), f'{root_dir}/data/store/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483/{evils.get_path()}')
                    CLI.print_to_shell(values_for_db['uuid'])

                except Exception as e:
                    if not dbe_log:
                        dbe_log = open('dbe_log.txt', 'w')
                        dbe_log.write(f'INSERT_Error: {str(evils)} {e}\n')
                    continue

            # db_cursor.execute("DELETE FROM files WHERE type='file';")
            # db_conn.commit()

        except Exception as e:
            CLI.print_to_shell(f'Error to_db {e}')
            exit()

        finally:
            if dbe_log:
                dbe_log.close()
                CLI.print_to_shell('database errorlog closed')

            if db_conn:
                db_conn.close()
                CLI.print_to_shell('database closed')

    @staticmethod
    def del_db():
        try:
            db_conn = sqlite3.connect('/home/archer/py/4dd88ac7-e609-4ae5-a5f3-5fd260f6f483.sqlite')
            db_cursor = db_conn.cursor()

            db_cursor.execute("DELETE FROM files WHERE type='file';")
            db_conn.commit()

        except Exception as e:
            CLI.print_to_shell(f'Error to_db {e}')
            exit()

        finally:
            if db_conn:
                db_conn.close()
                CLI.print_to_shell('database closed')


# TOOLBOX
class TOOLBOX:
    # meths
    @staticmethod
    def get_files(root_dir):
        for path, subdirs, files in os.walk(root_dir):
            for name in files:
                yield os.path.join(path, name)

    @staticmethod
    def get_hash(path, hash_type='sha256'):
        f = None
        try:
            func = getattr(hashlib, hash_type)()
            f = os.open(path, (os.O_RDONLY))
            for block in iter(lambda: os.read(f, 2048*func.block_size), b''):
                func.update(block)

        except Exception as e:
            CLI.print_to_shell(f'ERRER get_hash {e}')
            exit()

        finally:
            if f:
                os.close(f)
                CLI.print_to_shell('file closed')

        return str(func.hexdigest())

    @staticmethod
    def get_time():
        return datetime.datetime.now()


# BOX
class BOX:
    # fields
    __box = []

    # ctor
    def __init__(self, box=[]):
        self.__box = box

    # meths
    def commands(self, cmd):
        return{
            'a': lambda: self.add_song,
            'l': lambda: self.list_songs,
            'h': lambda: self.help,
            'e': lambda: self.exit
        }.get(cmd, lambda: self.help)()

    def add_song(self, *args):
        ae_log = None

        if not args[1:]:
            print('shit')
            args = (args[0], 'noarg')

        # supp_formats = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.wma', '.opus', '.mp4')
        supp_formats = ('.flac', '.mp3', '.m4a', '.ogg', '.wav', '.wma', '.opus')
        arg_counter = 1

        try:
            for index, arg in enumerate(args[1:]):
                arg = arg.strip('\'\"')
                if os.path.isdir(arg):
                    for song in TOOLBOX.get_files(arg):
                        try:
                            if song.endswith(supp_formats):
                                CLI.print_to_shell(song)
                                evils = EVILS(song)
                                self.__box.append(evils)
                                CLI.print_to_shell(str(evils) + '\n')
                        except Exception as e:
                            if not ae_log:
                                ae_log = open('ae_log.txt', 'w')
                                ae_log.write(f'ADD_Error: {song}: {e}\n')
                            continue

                elif arg.endswith(supp_formats):
                    CLI.print_to_shell(arg)
                    evils = EVILS(arg)
                    self.__box.append(evils)
                    CLI.print_to_shell(evils)
                else:
                    if index == 0:
                        CLI.print_to_shell('What song do you want to add?')
                        self.add_song([CLI.get_input('> ').strip('\'\"')])
                    break

                arg_counter += 1

        finally:
            if ae_log:
                ae_log.close()
                CLI.print_to_shell('adding errorlog closed')

            DB.to_db(self.__box)
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

    def exit(self, *args):
        return (exit(), 1)


# object
class EVILS:
    # fields
    __song = ''
    __tag = ''
    __path = ''
    __uuid = ''
    __artist = ''
    __title = ''
    __album = ''
    __trackinfo = ''
    __parent = ''
    __created = ''
    __createby = 'fd3591e0-97e0-4a5f-ad08-697c37f0e2bc'
    __type = 'file'
    __playcount = 0
    __duration = 0
    __bitrate = 0
    __samplerate = 0
    __filesize = 0
    __filename = ''
    __track = ''
    __genre = ''
    __size = 0

    # ctor
    def __init__(self, song):
        self.__song = song
        self.__tag = TinyTag.get(song)
        self.__path = TOOLBOX.get_hash(song)
        self.__uuid = str(uuid.uuid4())
        self.__artist = self.__tag.artist or self.__artist
        self.__title = self.__tag.title or self.__title
        self.__album = self.__tag.album or self.__album
        self.__created = TOOLBOX.get_time()
        self.__createby = self.__createby
        self.__type = self.__type
        self.__playcount = self.__playcount
        self.__duration = int(self.__tag.duration * 1000)
        self.__bitrate = int(self.__tag.bitrate * 1000)
        self.__samplerate = int(self.__tag.samplerate)
        self.__filesize = self.__tag.filesize
        self.__filename = self.__tag.title or self.__filename
        self.__track = self.__tag.track or self.__track
        self.__genre = self.__tag.genre or self.__genre
        self.__size = self.__size
        self.__parent = ''
        self.__trackinfo = f'{{"v":1,"uuid":"{self.__uuid}","parent":"{self.__parent}","type":"{self.__type}","path":"{self.__path}","codec":"-","duration":{self.__duration},"bitrate":{self.__bitrate},"samplerate":{self.__samplerate},"filesize":{self.__filesize},"filename":"{self.__filename}","title":"{self.__title}","artist":"{self.__artist}","album":"{self.__album}","track":{self.__track},"genre":"{self.__genre}"}}'

    def __repr__(self):
            return f'{self.__class__.__name__}({self.__song})'

    def __str__(self):
            return f'{self.__uuid}, {self.__artist}, {self.__title}, {self.__album}, {self.__trackinfo}, {self.__created}, {self.__createby}, {self.__type}, {self.__playcount}, {self.__filesize}'

    # props
    def get_uuid(self):
        return self.__uuid

    def get_artist(self):
        return self.__artist

    def get_title(self):
        return self.__title

    def get_path(self):
        return self.__path

    def get_song(self):
        return self.__song

    def for_db(self):
        return {
            'uuid': self.__uuid,
            'artist': self.__artist.replace('\'', '\'\''),
            'title': self.__title.replace('\'', '\'\''),
            'album': self.__album.replace('\'', '\'\''),
            'trackinfo': self.__trackinfo.replace('\'', '\'\''),
            'created': self.__created,
            'createby': self.__createby,
            'type': self.__type,
            'playcount': self.__playcount,
            'size': self.__size
        }


try:
    if __name__ == '__main__':
        CLI.main()

except Exception as e:
    CLI.print_to_shell(f'Oh no! Something has gone wrong. {e}')

finally:
    print('cya')
    exit()
