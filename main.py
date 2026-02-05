import atexit
import signal
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from control import control
import traceback
import json
import os

port = 1337

class cs2bac:
    def __init__(self, config_path="config.json"):
        self.current_volume = None
        self.old = {}
        self.config_path = config_path
        self.load_config()
        self.show_toast = False

        ctrl = control(self.dur_fade, self.log_mus, self.allow_auto_play)
        self.adjust_volume = ctrl.adjust_volume

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.__dict__.update(cfg)
            # If no apps in config — create empty dict
            if not hasattr(self, "apps"):
                self.apps = {}
            if not hasattr(self, "control_all_apps"):
                self.control_all_apps = False
            if not hasattr(self, "allowed_modes"):
                self.allowed_modes = ["competitive", "casual"]
        else:
            # Default values init
            self.allow_auto_play = True
            self.log_vol = False
            self.log_mus = True
            self.log_gsi = False
            self.vol_base = 100
            self.vol_menu = self.vol_base
            self.vol_game = 0
            self.vol_buyp = 30
            self.vol_warm = 40
            self.vol_spec = 40
            self.dur_fade = 1
            self.apps = {}
            self.control_all_apps = False
            self.allowed_modes = ["competitive", "casual"]

    def save_config(self):
        cfg = {
            "allow_auto_play": self.allow_auto_play,
            "log_vol": self.log_vol,
            "log_mus": self.log_mus,
            "log_gsi": self.log_gsi,
            "vol_base": self.vol_base,
            "vol_menu": self.vol_menu,
            "vol_game": self.vol_game,
            "vol_buyp": self.vol_buyp,
            "vol_warm": self.vol_warm,
            "vol_spec": self.vol_spec,
            "dur_fade": self.dur_fade,
            "apps": self.apps,
            "control_all_apps": self.control_all_apps,
            "allowed_modes": self.allowed_modes
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)

    def volume(self, set_volume, why):
        why_dict = {
            "menu": "We're in the menu",
            "spec": "Spectating",
            "buyp": "Game not live yet",
            "dead": "We're dead",
            "game": "We're playing",
            "warm": "We're warming up",
            "play": "We're deciding on or switching a team"
        }

        if set_volume != self.current_volume:
            if self.log_vol:
                print(why_dict[why] + ",", "setting volume to",
                      str(set_volume) + "%")
            self.current_volume = set_volume
            self.adjust_volume(volume=set_volume, fade=self.dur_fade)

    def get_data(self, post_data):
        try:
            return json.loads(post_data.decode('utf-8'))
        except Exception:
            traceback.print_exc()

    def main(self, data):
        try:
            if data["provider"]["appid"] == 730:
                my_id = data["provider"]["steamid"]
                if data["player"]["activity"] == "menu":
                    try:
                        data['player']['state']
                    except KeyError:
                        self.volume(self.vol_menu, "menu")

                game_mode = data.get("map", {}).get("mode")

                if game_mode not in self.allowed_modes:
                    if self.log_gsi:
                        print(f"Ignoring game mode: {game_mode}")
                    return  # exiting without volume adjust

                elif data["player"]["steamid"] != my_id:
                    self.volume(self.vol_spec, "spec")
                elif data["round"]["phase"] != "live":
                    self.volume(self.vol_buyp, "buyp")
                elif data["player"]["state"]["health"] == 0:
                    self.volume(self.vol_spec, "dead")
                else:
                    self.volume(self.vol_game, "game")

                if self.log_gsi:
                    # remove timestamps so it does not spam
                    del data["provider"]
                    if data != self.old:
                        self.old = data
                        print(json.dumps(data, indent=4, sort_keys=True))

            else:
                # ignore data that isn't from cs2
                pass

        except KeyError as e:
            if "'round'" == str(e):
                self.volume(self.vol_warm, "warm")
            elif "'player'" == str(e):
                self.volume(self.vol_warm, "play")
            elif "'state'" == str(e):
                pass

            else:
                print("KeyError:", e)

        except Exception:
            traceback.print_exc()

    def reset_volume(self):
        # if control all apps enabled
        if self.control_all_apps:
            self.adjust_volume(volume=100, fade=self.dur_fade)
        else:
            # apps — list of process names
            for app in self.apps:
                try:
                    # if adjust_volume can handle app name
                    self.adjust_volume(volume=100, fade=self.dur_fade, app=app)
                except TypeError:
                    # if not set overall volume
                    self.adjust_volume(volume=100, fade=self.dur_fade)

mc = cs2bac()
def cleanup():
    print("Resetting volume to 100%...")
    try:
        mc.reset_volume()
    except Exception as e:
        print("Error resetting volume:", e)

atexit.register(cleanup)

# Handle exit to reset volume (working when using Ctrl+C to exit app)
def handle_exit(signum, frame):
    print(f"Caught signal {signum}, cleaning up...")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)   # Ctrl+C
signal.signal(signal.SIGTERM, handle_exit)  # kill, cross gui

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        with open("config.html", "r", encoding="utf-8") as f:
            html = f.read()

        # simple placeholder replacement
        html = html.replace("{{mode_competitive}}", "checked" if "competitive" in mc.allowed_modes else "")
        html = html.replace("{{mode_casual}}", "checked" if "casual" in mc.allowed_modes else "")
        html = html.replace("{{mode_deathmatch}}", "checked" if "deathmatch" in mc.allowed_modes else "")
        html = html.replace("{{mode_survival}}", "checked" if "survival" in mc.allowed_modes else "")
        html = html.replace("{{mode_practice}}", "checked" if "practice" in mc.allowed_modes else "")

        html = html.replace("{{vol_warm}}", str(mc.vol_warm))
        html = html.replace("{{vol_base}}", str(mc.vol_base))
        html = html.replace("{{vol_menu}}", str(mc.vol_menu))
        html = html.replace("{{vol_game}}", str(mc.vol_game))
        html = html.replace("{{vol_buyp}}", str(mc.vol_buyp))
        html = html.replace("{{vol_spec}}", str(mc.vol_spec))
        html = html.replace("{{dur_fade}}", str(mc.dur_fade))

        # checkboxes: if True → set checked
        html = html.replace("{{allow_auto_play}}", "checked" if mc.allow_auto_play else "")
        html = html.replace("{{log_vol}}", "checked" if mc.log_vol else "")
        html = html.replace("{{log_mus}}", "checked" if mc.log_mus else "")
        html = html.replace("{{log_gsi}}", "checked" if mc.log_gsi else "")

        html = html.replace("{{apps_json}}", json.dumps(mc.apps, indent=4))
        html = html.replace("{{control_all_apps}}", "checked" if mc.control_all_apps else "")

        html = html.replace("{{show_toast}}", "true" if mc.show_toast else "false")
        mc.show_toast = False  # reset

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode("utf-8")

        if self.path == "/config":
            import urllib.parse
            params = urllib.parse.parse_qs(post_data)

            # updating config
            new_modes = []
            if "mode_competitive" in params:
                new_modes.append("competitive")
            if "mode_casual" in params:
                new_modes.append("casual")
            if "mode_deathmatch" in params:
                new_modes.append("deathmatch")
            if "mode_survival" in params:
                new_modes.append("survival")
            if "mode_practice" in params:
                new_modes.append("practice")

            mc.allowed_modes = new_modes

            mc.vol_base = int(params.get("vol_base", [mc.vol_base])[0])
            mc.vol_menu = int(params.get("vol_menu", [mc.vol_menu])[0])
            mc.vol_game = int(params.get("vol_game", [mc.vol_game])[0])
            mc.vol_buyp = int(params.get("vol_buyp", [mc.vol_buyp])[0])
            mc.vol_warm = int(params.get("vol_warm", [mc.vol_warm])[0])
            mc.vol_spec = int(params.get("vol_spec", [mc.vol_spec])[0])
            mc.dur_fade = int(params.get("dur_fade", [mc.dur_fade])[0])

            mc.allow_auto_play = "allow_auto_play" in params
            mc.log_vol = "log_vol" in params
            mc.log_mus = "log_mus" in params
            mc.log_gsi = "log_gsi" in params

            apps_raw = params.get("apps_raw", [None])[0]
            if apps_raw:
                try:
                    mc.apps = json.loads(apps_raw)
                except Exception as e:
                    print("Error parsing apps:", e)

            mc.control_all_apps = "control_all_apps" in params

            mc.save_config()

            # redir to main page
            self.send_response(303)
            mc.show_toast = True
            self.send_header('Location', '/')
            self.end_headers()
        else:
            mc.main(mc.get_data(post_data.encode("utf-8")))
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'GSI data processed')


def run_server(server_class=HTTPServer, handler_class=RequestHandler, port=port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stopping server...")
    httpd.server_close()




run_server()
