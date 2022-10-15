# Copyright 2021 - 2022, Martijn Braam and the OpenAtem contributors
# SPDX-License-Identifier: GPL-3.0-only
import gi
from gi.repository import GLib


class Service:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def variant(self):
        return GLib.Variant('a{sv}', {
            'name': GLib.Variant('s', self.name),
            'url': GLib.Variant('s', self.url),
        })


services = {
    "Youtube": [
        Service("Youtube Primary", "rtmp://a.rtmp.youtube.com/live2"),
        Service("Youtube Secondary", "rtmp://b.rtmp.youtube.com/live2?backup=1"),
    ],
    "Facebook": [
        Service("Facebook", "rtmps://live-api-s.facebook.com:443/rtmp"),
    ],
    "Twitch": [
        Service("Twitch auto location", "rtmp://live.twitch.tv/app"),
    ],
    "Twitter / Periscope": [
        Service("Periscope Tokyo", "rtmp://jp.pscp.tv:80/x"),
        Service("Periscope Seoul", "rtmp://kr.pscp.tv:80/x"),
        Service("Periscope Mumbai", "rtmp://in.pscp.tv:80/x"),
        Service("Periscope Singapore", "rtmp://sg.pscp.tv:80/x"),
        Service("Periscope Sydney", "rtmp://au.pscp.tv:80/x"),
        Service("Periscope Canada", "rtmp://va.pscp.tv:80/x"),
        Service("Periscope Frankfurt", "rtmp://de.pscp.tv:80/x"),
        Service("Periscope Ireland", "rtmp://ie.pscp.tv:80/x"),
        Service("Periscope São Paulo", "rtmp://br.pscp.tv:80/x"),
        Service("Periscope N. Virginia", "rtmp://va.pscp.tv:80/x"),
        Service("Periscope Ohio", "rtmp://va.pscp.tv:80/x"),
        Service("Periscope Oregon", "rtmp://or.pscp.tv:80/x"),
        Service("Periscope N. California", "rtmp://ca.pscp.tv:80/x"),
    ],
    "Restream.io": [
        Service("Restream.io auto location", "rtmp://live.restream.io/live")
    ],
}
