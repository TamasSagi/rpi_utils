import json
from pathlib import Path
from typing import Dict, List, TypedDict

from deluge_client import LocalDelugeRPCClient


class TorrentInfo(TypedDict):
    queued: int
    seeding: int
    downloading: int
    upload_speed_bps: float
    download_speed_bps: float


class TorrentStats(TypedDict):
    name: str
    state: str
    is_finished: bool
    seeding_time: int
    download_payload_rate: int
    upload_payload_rate: int
    progress: float
    ratio: float


class DelugeHandler:
    REQUIRED_RATIO = 1.05
    REQUIRED_SEED_TIME = 48.5*60*60  # 48.5 hours
    TORRENT_STATS_TO_QUERY = ['name', 'is_finished', 'progress', 'ratio', 'seeding_time', 'state',
                              'download_payload_rate', 'upload_payload_rate']

    def __init__(self) -> None:
        self.client = LocalDelugeRPCClient()
        self.client.connect()

    def get_torrent_list(self, stats_to_query: List['str'] = None) -> Dict[str, TorrentStats]:
        stats_to_query = stats_to_query if stats_to_query else DelugeHandler.TORRENT_STATS_TO_QUERY

        return self.client.call('core.get_torrents_status', {}, stats_to_query)

    def get_stats(self) -> TorrentInfo:
        torrents = self.get_torrent_list()
        queued = seeding = downloading = upload_speed_bps = download_speed_bps = 0

        for torrent_values in torrents.values():
            if torrent_values['state'].lower() == 'queued':
                queued += 1
            elif torrent_values['is_finished']:  # If not queued AND "is_finished"
                seeding += 1
            else:
                downloading += 1

            upload_speed_bps += torrent_values['upload_payload_rate']
            download_speed_bps += torrent_values['download_payload_rate']

        return {'queued': queued, 'seeding': seeding, 'downloading': downloading,
                'upload_speed_bps': upload_speed_bps, 'download_speed_bps': download_speed_bps}

    def remove_completed_torrents(self) -> None:
        torrents = self.get_torrent_list()

        for torrent_hash, torrent_values in dict(torrents).items():
            if (torrent_values['seeding_time'] > DelugeHandler.REQUIRED_SEED_TIME or
                torrent_values['ratio'] >= DelugeHandler.REQUIRED_RATIO):
                self.client.call('core.remove_torrent', torrent_hash, False)
                torrents.pop(torrent_hash)

                print(f'{torrent_values["name"]} is removed!')

    def _get_client_method_list(self) -> List[str]:
        return self.client.daemon.get_method_list()

    def _dump_torrents_to_json(self) -> None:
        torrents = self.get_torrent_list()
        json.dump(torrents, Path('torrent_list.json').open('w', encoding='utf8'), indent=4)
