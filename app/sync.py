from argparse import ArgumentParser
from pathlib import Path
from common.file_syncer import FlaskFileSync as FFS

# cmd line args
parser = ArgumentParser(description="args for syncing with notification pi enabled",
                        usage="sync.py ip_port sync_img conf_file sync_keys\n"
                              "example args:'192.168.1.155:8082' 'quarters.json' "
                              "'testing.json' 'local'"
                        )

parser.add_argument("ip_port",
                    type=str,
                    help="ip addr and port of pi: 192.168.1.XX:XXXX"
                    )
parser.add_argument("sync_img",
                    type=str,
                    help="the image displayed on the sense hat during sync",
                    default="quarters.json"
                    )
parser.add_argument("conf_file",
                    type=str,
                    help="json file name (with extension), must be in app/data DIR",
                    default="testing.json"
                    )
parser.add_argument("sync_keys",
                    type=str,
                    help="the relevant DIR keys from the json file:\n"
                    "comma space seperated strings: just, like, this "
                    )

# start sync
args = parser.parse_args()
args.sync_keys = args.sync_keys.split(", ")
FFS(args.ip_port, args.sync_img, args.conf_file).notify_sync(args.sync_keys)
