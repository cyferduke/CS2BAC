import asyncio
import time
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.media.control import \
    GlobalSystemMediaTransportControlsSessionPlaybackStatus as PlaybackStatus
import traceback
import math


import json, os

class control:
    def __init__(self, fade_duration, log, allow_auto_play, apps, control_all_apps):
        self.fade_duration = fade_duration
        self.log = log
        self.allow_auto_play = allow_auto_play
        self.last_notification = None
        self.old_title = None
        self.stopped_by_us = False
        self.apps = apps
        self.control_all_apps = control_all_apps

    def round_up_to_2_digits(self, number):
        return math.ceil(number * 100) / 100

    def reload_config(self, apps, control_all_apps, allow_auto_play, dur_fade, log_mus):
        self.apps = apps
        self.control_all_apps = control_all_apps
        self.allow_auto_play = allow_auto_play
        self.fade_duration = dur_fade
        self.log = log_mus

    async def get_current_session(self):
        """Return currently playing audio session"""
        sessions = await MediaManager.request_async()
        return sessions.get_current_session()  # return sessions.get_sessions()

    def get_app_volume_controls(self, app_name):
        """Return list of all audiothreads of process"""
        sessions = AudioUtilities.GetAllSessions()
        controls = []
        for session in sessions:
            if not session.Process:
                continue
            proc_name = session.Process.name().lower()

            if self.control_all_apps:
                controls.append(session.SimpleAudioVolume)
            elif proc_name in [x.lower() for x in self.apps]:
                controls.append(session.SimpleAudioVolume)

        return controls

    def normalize_volume(self, value):
        # return vol percentage
        return max(0.0, min(1.0, value / 100.0))

    def fade_volume(self, volume_control, target_volume, duration=None):
        if duration is None:
            duration = self.fade_duration
        target_volume = self.normalize_volume(target_volume)
        if target_volume > 1.0:
            target_volume = target_volume / 100.0

        current_volume = volume_control.GetMasterVolume()
        if current_volume == target_volume:
            if self.last_notification != target_volume:
                if self.log:
                    print(
                        f"Volume is already at {target_volume * 100:.0f}%! Not changing anything.")
            self.last_notification = current_volume
            return

        if duration != 0.0:
            volume_difference = self.round_up_to_2_digits(
                abs(target_volume - current_volume))

            # 100 steps per 1.0 volume difference

            per_step = 2
            steps = int(volume_difference * (100 / per_step))
            if steps == 0:
                steps = 1

            step_duration = self.round_up_to_2_digits(
                duration / steps)  # time per step

            # volume increment per step
            step = self.round_up_to_2_digits(volume_difference / steps)


            for _ in range(steps):
                if target_volume > current_volume:
                    current_volume = current_volume + step
                else:
                    current_volume = current_volume - step
                    # print("curr", current_volume, "step",
                    #   step, "target", target_volume)

                if current_volume <= 1.00 and current_volume >= 0.00:
                    volume_control.SetMasterVolume(current_volume, None)
                    time.sleep(step_duration)

        volume_control.SetMasterVolume(target_volume, None)  # failsafe

    def adjust_volume(self, volume, fade):
        try:
            asyncio.run(self.control_music(volume, fade))
            return True
        except Exception as e:
            traceback.print_exc()
            print(e)
            return False

    async def start(self, current_session):
        await current_session.try_play_async()

    async def pause(self, current_session, volume=None):
        self.stopped_by_us = True
        await current_session.try_pause_async()
        await asyncio.sleep(1)
        if volume:
            self.fade_volume(volume, 1.0, duration=0)

    async def control_music(self, set_volume, fade):
        current_session = await self.get_current_session()
        if current_session:
            info = await current_session.try_get_media_properties_async()
            playback_info = current_session.get_playback_info()

            app_name = current_session.source_app_user_model_id.split('!')[0]
            if ".exe" not in app_name:
                app_name += ".exe"

            # get all audiothreads of process
            volumes = self.get_app_volume_controls(app_name)

            if volumes:
                for vol in volumes:
                    if set_volume == 0:
                        self.fade_volume(vol, set_volume, duration=fade)
                        await self.pause(current_session, vol)
                    else:
                        if playback_info.playback_status != PlaybackStatus.PLAYING:
                            await self.start(current_session)
                        self.fade_volume(vol, set_volume, duration=fade)

            if self.log:
                if self.old_title != (info.title, info.artist):
                    self.old_title = (info.title, info.artist)
                    print(f"Playing {info.title} by {info.artist} on {app_name.split('.exe')[0]}")

        else:
            print("No current media session found.")

