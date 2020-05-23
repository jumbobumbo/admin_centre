from os import system
from pathlib import Path
from argparse import ArgumentParser

from requests import post

from common.json_reader import JSONReads

# Path to parent DIR
mod_path = Path(__file__).parent

# get json config file
conf_file = JSONReads(Path(mod_path, "data", "ping_conf.json")).data_return()

# cmd line args
parser = ArgumentParser(description="args for ping verification",
                        usage="sync.py uri port\n"
                              "example args:'192.168.1.155' '8082'"
                        )

parser.add_argument("uri",
                    type=str,
                    help="IP or URL of rasp pi (for displaying notification)"
                    )
parser.add_argument("port",
                    type=str,
                    help="port the pi is listening on"
                    )

def server_status(key: str = "servers", re_try_max: int = 3) -> list:
    """
    Returns a list of servers which haven't responding to a ping within the retry limit

    Arguments:
        return_list {list} -- the list to return when finished.
        This allows easy recursion whilst retaining previous values.
        Providing a blank list by default should suit most usage scenarios.

    Keyword Arguments:
        key {str} -- dict key to servers you want to check (default: {"servers"})
        re_try_max {int} -- max number of ping retries till server is marked as down (default: {3})

    Returns:
        list -- list of servers that are not responding to pings
    """
    def _pinger(ip: str, attempt_no: int):
        resp = system(f"ping -c 1 {ip}")
        # Zero is the only acceptable response to a ping
        if resp != 0:
            if attempt_no < re_try_max:
                return _pinger(ip, attempt_no + 1)
            else:
                return "unresponsive"

    # populated if servers dont respond to pings
    return_list = []

    for key, value in conf_file[key].items():
        if _pinger(value, 1) == "unresponsive":
            return_list.append(key)

    return return_list


def post_pi(alert_list: list, uri: str, port: str, repeat_count: int = 2, key_pi: str = "pi", key_alert: str = "alert_conf"):
    """
    Sends alert (post list items and colours) to rasp pi sense hat

    Arguments:
        alert_list {list} -- strings you wish to display on the pi screen
        uri {str} -- IP or URL of rasp pi (for displaying notification)
        port {str} -- port the pi is listening on

    Keyword Arguments:
        repeat_count {int} -- how many times do you want me to cycle over the alerts? (default: {2})
        key_pi {str} -- required key from conf_file, contains default pi info (default: {"pi"})
        key_alert {str} -- required key from conf_file (default: {"alert_conf"})
    """

    # address to post to
    pi_addr = f"http://{uri}:{port}"

    # set the orientation of the display (refer to 'sense_my_pihat' repo)
    post(f"{pi_addr}/post_orientation/", json=conf_file[key_pi]["orientation"])

    for i in range(0, repeat_count):
        for alert in alert_list:  # send alers to pi
            post(f"{pi_addr}/post_display_text/", json={"text_str": f"!! {alert} is offline !!",
                                                        "text_color": conf_file[key_alert]["text_color"],
                                                        "back_color": conf_file[key_alert]["back_color"],
                                                        "scroll": conf_file[key_alert]["scroll"]})


if __name__ == "__main__":
    args = parser.parse_args()

    offline_servers = server_status()
    if offline_servers:
        post_pi(offline_servers, args.uri, args.port)
