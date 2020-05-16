from datetime import datetime
from pathlib import Path
from re import findall
from threading import Thread
from threading import enumerate as t_enumerate
from sys import path as syspath
from time import sleep

from dirsync import sync
from requests import post as r_post
from requests import get as r_get

from common.json_reader import JSONReads

# parent DIR to common /app
mod_path = Path(__file__).parent.parent

# default regex
d_reg = r".+\.(log|git|jar)$"


class FileSync:
    def __init__(self, conf_file: str = "backup_conf.json"):
        """
        param: conf_file - config file (json) - must exist in /data DIR
        """
        self.conf_data = JSONReads(
            Path(mod_path, "data", conf_file)).data_return()
        self.sync_complete_no = 0

    def syncer(self, sync_keys: list, regex: str = d_reg):
        """
        loops through nested key (source), value (dest) pairs under 'sync_key' key.
        param: sync_keys - keys from dict - target sync DIRs ["key1", "key2"]
        param: regex - file types to ignore when syncing
        """
        def tsync(*args, **Kwargs):
            sync(*args, **Kwargs)
            # we tally up the number of syncs which don't throw an exception
            # this is so we can do some assertions later
            # this is very lightweight i know, if it needs beefing out then i'll cross that bridge when i come to it...
            self.sync_complete_no += 1

        thread_names = []
        for sk in sync_keys:
            for index, (source, dest) in enumerate(self.conf_data[sk].items()):
                # create thread_name and append it to list
                thread_name = f"sync_{sk}_{index}"
                thread_names.append(thread_name)
                # create sync thread
                th = Thread(target=tsync, args=(Path(source), Path(dest), "sync"), kwargs={
                            "verbose": False, "exclude": (regex,)}, name=thread_name)
                th.daemon = True
                th.start()

        # wait for all threads to finish
        self._wait_for_thread(thread_names)

    @staticmethod
    def _wait_for_thread(thread_names: list):
        """
        will iterate over all started threads and wait for them to end
        param: thread_names - list of active thread names
        """
        for thread_n in thread_names:
            for thread in t_enumerate():  # this is the enumerate from threading module
                if thread.name == thread_n:
                    thread.join()


class FlaskFileSync(FileSync):
    # Syncs files whilst notifying me via flask, a sense hat and my raspberry pi
    def __init__(self, pi_ip_port: str, sync_img: str = "quarters.json", conf_file="backup_conf.json"):
        """
        param: pi_ip_port - ip address and port (if required) of pi running flask (example: port: 192.168.1.155:8082, no port: 192.168.1.155)
        param: sync_img - image to display on hat screen whilst sinking
        param: finished_img - image to display when all has synced
        """
        self.pi_ip_port = pi_ip_port
        self.sync_img = JSONReads(Path("app", "data", sync_img)).data_return()
        super().__init__(conf_file=conf_file)

    def _post_actions(self, img_load_success: bool, sync_complete: bool, sync_keys: list):
        """
        This is what we do when syncing is 'finished' (failure or success)
        If flask is working, we stop the rotation animation during syncing and set the screen red or green
        Otherwise we log what we can
        param: img_load_success - can we talk to flask and load an image on the sense hat
        param: sync_complete - successful syncing or not
        param: sync_keys - keys from dict - target sync DIRs ["key1", "key2"]
        """
        sync_keys = str(sync_keys)  # typecast for possible later logging

        # function for saving failure file
        def write_f(fname): return open(Path(mod_path, "output", fname), "w")

        # function for stipping unwanted chars
        def strip_char(chars): return chars.translate(
            {ord(c): None for c in "'[],"}).translate({ord(c): "_" for c in " :/"}
                                                      )

        # current date time
        dtn = datetime.now().strftime('%d/%m/%Y, %H:%M:%S')

        if img_load_success:
            # stop the spinning animation from during sync
            r_post(f"http://{self.pi_ip_port}/post_rotation/",
                   json={"cmd": "kill"}
                   )

            if sync_complete:  # set green - everything good
                r_post(f"http://{self.pi_ip_port}/post-set-img/",
                       json={"base": [0, 120, 0]}
                       )
                # wait so it catches my eye
                sleep(2)
                # reset display to default temp display
                r_get(f"http://{self.pi_ip_port}/show_temp/"
                       )

            else:  # set red - something went wrong
                r_post(f"http://{self.pi_ip_port}/post-set-img/",
                       json={"base": [200, 0, 0]}
                       )
                # create failure file
                with write_f(f"{strip_char(sync_keys)}_sync_failed_at_{strip_char(dtn)}"): pass

        if sync_complete and not img_load_success:
            print(f"pi may be dead, but the sync completed @ {dtn}")
            with write_f(f"pi_dead_at_{strip_char(dtn)}"): pass

        if not img_load_success and not sync_complete:
            # create failure file
            with write_f(f"{strip_char(sync_keys)}_sync_and_pi_failed_at_{strip_char(dtn)}"): pass
            raise Exception(f"Everything is dead @ {dtn}")

    def notify_sync(self, sync_keys: list, regex: str = d_reg):
        """
        uses FileSync.syncer for the syncing, wraps the pi communication around the outside
        param: sync_keys - keys from dict - target sync DIRs ["key1", "key2"]
        param: regex - file types to ignore when syncing
        """
        try:  # load syncing image - set its rotation
            img_cmds = [
                {"command": "post-set-img", "data": self.sync_img},
                {"command": "post_rotation", "data": {"cmd": "simple", "rotate_vals": [
                    0, 90, 180, 270], "re_draw": True,  "background": True}}
            ]
            for cmd in img_cmds:  # send each command
                post_data = r_post(
                    f"http://{self.pi_ip_port}/{cmd['command']}/", json=cmd['data']
                )
                # verify it was accepted (http response 200)
                if findall(r"\[(.*?)\]", str(post_data))[0] != "200":
                    raise ValueError(f"flask has not accepted one of the following:\ncommand page: {cmd['command']}\n \
                                     or the data input: {cmd['data']}"
                                     )

            img_load_success = True

        except Exception as ex:
            # Either the pi is not responding or we fluffed the flask command, either way, I still want to try and sync my data
            if ex != ValueError:
                print(f"Exception raised when attempting to load notification image:\n{ex}")
            img_load_success = False

        # start the syncing
        self.syncer(sync_keys, regex)

        # did we get any errors from the syncing process
        total_completed_syncs = 0
        for sk in sync_keys:
            total_completed_syncs += len(self.conf_data[sk])

        sync_complete = True if total_completed_syncs == self.sync_complete_no else False

        # post actions for flask
        self._post_actions(img_load_success, sync_complete, sync_keys)
