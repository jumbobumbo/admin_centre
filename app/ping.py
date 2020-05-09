from os import system
from pathlib import Path

from requests import post

from common.json_reader import JSONReads

# Path to parent DIR
mod_path = Path(__file__).parent

# get json config file
conf_file = JSONReads(Path(mod_path, "data", "ping_conf.json")).data_return()


def server_status(key: str = "servers") -> list:
    """
    returns a list of servers which haven't responded to a ping
    reads values from 'conf_file'
    param: key: - str - key for servers in conf file - defaults to 'servers'
    returns - list
    """
    return_list = []

    # Zero is the only acceptable response to a ping
    for key, value in conf_file[key].items():
        if system(f"ping -c 1 {value}") != 0:
            return_list.append(key)

    return return_list


def post_pi(alert_list: list, repeat_count: int = 2, key_pi: str = "pi", key_alert: str = "alert_conf"):
    """
    Sends alert (post list items and colours) to rasp pi sense hat

    Arguments:
        alert_list {list} -- strings you wish to display on the pi screen

    Keyword Arguments:
        repeat_count {int} -- how many times do you want me to cycle over the alerts? (default: {2})
        key_pi {str} -- required key from conf_file (default: {"pi"})
        key_alert {str} -- required key from conf_file (default: {"alert_conf"})
    """

    # address to post to
    pi_addr = f"http://{conf_file[key_pi]['ip']}:{conf_file[key_pi]['port']}"

    # set the orientation of the display (refer to 'sense_my_pihat' repo)
    post(f"{pi_addr}/post_orientation/", json=conf_file[key_pi]["orientation"])

    for i in range(0, repeat_count):
        for alert in alert_list:  # send alers to pi
            post(f"{pi_addr}/post_display_text/", json={"text_str": f"!! {alert} is offline !!",
                                                        "text_color": conf_file[key_alert]["text_color"],
                                                        "back_color": conf_file[key_alert]["back_color"],
                                                        "scroll": conf_file[key_alert]["scroll"]})


if __name__ == "__main__":
    offline_servers = server_status()
    if offline_servers:
        post_pi(offline_servers)