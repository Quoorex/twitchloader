import os
import sys
import pathlib
import datetime

import configargparse
import yaml
from pyfiglet import Figlet
import colorama
from twitch import TwitchClient
import requests
import youtube_dl


__version__ = '0.1'
__url__ = 'https://github.com/Quoorex/twitchloader'


# TODO Add threading or multiprocessing


class Twitchloader():
    def __init__(self):
        self.conf = self.init_parser()
        client_id = self.conf.client_id
        self.client = TwitchClient(client_id=client_id)

        self.video_url_base = "https://www.twitch.tv/videos/"
        self.api_base = "https://api.twitch.tv/kraken/"
        self.headers = {"Accept": "application/vnd.twitchtv.v5+json", "Client-ID": client_id}

    def init_parser(self):
        ydl_options_default = {
            "format": "best",
            "outtmpl": '%(download_dir)s/%(uploader)s/%(collection_name)s/%(video_index)s - %(title)s.%(ext)s',
            "urls_outtmpl": '%(download_dir)s/%(uploader)s/%(title)s.%(ext)s',
        }
        self.parser = configargparse.ArgParser(
            config_file_parser_class=configargparse.YAMLConfigFileParser,
            default_config_files=["config.yaml"],
            description='Download VODs and complete video collections from Twitch.tv using youtube-dl.'
        )
        self.parser.add_argument("-c", "--config-path", is_config_file=True, dest="config-path", help="path to the config file")
        self.parser.add_argument("-C", "--channels", dest="channels", nargs="+", help="names of the channels to get the collections of")
        self.parser.add_argument("-t", "--client-id", dest="client_id", help="Twitch client ID needed to access the API (get one on https://dev.twitch.tv/)")
        self.parser.add_argument("--collection-ids", dest="collection_ids", nargs="+", help="ids of the collections to process")
        self.parser.add_argument("--show-collections", action="store_true", dest="show_collections", help="show the collections of the channels")
        self.parser.add_argument("--save-urls", action="store_true", dest="save_urls", help="save the urls of the videos in separated folders instead of downloading them (for manual use with the '-a' youtube-dl option")
        self.parser.add_argument("-o", "--output-dir", dest="output_dir", default="downloads", type=str, help="Path to where the files will be saved")
        self.parser.add_argument("-y", "--ydl-options", dest="ydl_options", type=yaml.safe_load, default=ydl_options_default, help="Youtube-DL options (https://github.com/ytdl-org/youtube-dl/blob/3e4cedf9e8cd3157df2457df7274d0c842421945/youtube_dl/YoutubeDL.py#L137-L312)")
        self.parser.add_argument("-u", "--urls", dest="urls", type=yaml.safe_load, nargs="+", help="URLs of the videos to download")
        return self.parser.parse()

    def print_banner(self):
        colorama.init()
        figlet = Figlet(font="speed")
        print(colorama.Fore.MAGENTA + colorama.Back.BLACK + figlet.renderText("Twitchloader"))
        print(colorama.Back.RESET + "Download Twitch videos with ease")
        print(colorama.Style.RESET_ALL)

    def print_figlet(self, font, text):
        figlet = Figlet(font=font)
        print(colorama.Fore.MAGENTA + figlet.renderText(text))
        print(colorama.Style.RESET_ALL)

    def channel_search(self, query):
        result = self.client.search.channels(query, 1)[0]
        result_name = result["name"]
        print(f"Found channel '{result_name}' for query '{query}'")
        return result

    def get_collections(self, channel_id):
        params = {"limit": 100}
        request_url = self.api_base + f"channels/{channel_id}/collections"

        collections_response = requests.get(request_url, headers=self.headers, params=params).json()
        collections = collections_response["collections"]

        if collections_response["_cursor"] is not None:  # Not all collections could be fetched with one request
            params["cursor"] = collections_response["_cursor"]
            while params["cursor"] is not None:
                r = requests.get(request_url, headers=self.headers, params=params).json()
                collections.extend(r["collections"])
                params["cursor"] = r["_cursor"]

        return collections

    def gather_links(self, collections):
        collections_dict = {}
        video_count = 0

        for collection in collections:
            videos = self.client.collections.get(collection["_id"], include_all_items=True)
            video_urls = []

            for video in videos:
                video_url = self.video_url_base + video['item_id']
                video_urls.append(video_url)
            collections_dict[collection["_id"]] = [collection, video_urls]
            video_count += collection["items_count"]
        print(f"Found a total of {video_count} videos")
        return collections_dict

    def save_urls(self, collections_dict):
        self.print_figlet("standard", "Saving all urls")

        download_dir = self.conf.output_dir

        for collection_id in collections_dict.keys():
            collection_item, video_urls = collections_dict[collection_id]
            collection_name = collection_item["title"]
            uploader = collection_item["owner"]["name"]

            # Declare the download path and create it if necessary
            download_path = os.path.abspath(f"{download_dir}/{uploader}/{collection_name}/")
            pathlib.Path(download_path).mkdir(parents=True, exist_ok=True)

            with open(os.path.join(download_path, "urls.txt"), "w") as f:
                for video_url in video_urls:
                    f.write(video_url + "\n")

    def download_collection(self, collections_dict):
        """
        Downloads a complete collection of videos
        """
        ydl_options = self.conf.ydl_options
        self.print_figlet("standard", "Starting the collection downloads")

        download_dir = self.conf.output_dir

        for collection_id in collections_dict.keys():
            collection_item, video_urls = collections_dict[collection_id]
            collection_name = collection_item["title"]

            for video_url in video_urls:
                video_index = video_urls.index(video_url) + 1  # Add 1 because lists start at 0
                ydl_options["outtmpl"] = ydl_options["outtmpl"].replace("%(download_dir)s", download_dir).replace("%(collection_name)s", collection_name).replace("%(video_index)s", str(video_index))
                with youtube_dl.YoutubeDL(ydl_options) as ydl:
                    try:
                        ydl.download([video_url])
                    except KeyboardInterrupt:
                        print("\nUser interrupted the program, stopping ...")
                        sys.exit(1)

    def download(self, video_urls):
        """
        Downloads individual videos from a list of URLs
        """
        ydl_options = self.conf.ydl_options
        self.print_figlet("standard", "Starting the video downloads")

        download_dir = self.conf.output_dir
        ydl_options["outtmpl"] = ydl_options["urls_outtmpl"].replace("%(download_dir)s", download_dir)

        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            try:
                ydl.download(video_urls)
            except KeyboardInterrupt:
                print("\nUser interrupted the program, stopping ...")
                sys.exit(1)

    def run(self):
        self.print_banner()
        collection_ids = self.conf.collection_ids
        collections_dict = dict()
        if collection_ids is not None:
            self.print_figlet("standard", f"Processing collection IDs")
            collections = []
            for c_id in collection_ids:
                # Get additonal information about that collection
                request_url = self.api_base + f"collections/{c_id}"
                collection_item = requests.get(request_url, headers=self.headers).json()
                collections.append(collection_item)
            collections_dict = self.gather_links(collections)
        elif self.conf.channels:  # Only channel names are supplied
            for channel_name in self.conf.channels:
                self.print_figlet("standard", f"Processing: {channel_name}")
                channel_query_result = self.channel_search(channel_name)
                channel = self.client.channels.get_by_id(channel_query_result["id"])

                collections = self.get_collections(channel["id"])

                if self.conf.show_collections is True:
                    # Only show available collections
                    for collection in collections:
                        print(f"{collection['title']} - {collection['_id']}")
                    sys.exit(1)
                else:
                    # download the collections
                    collections_dict = self.gather_links(collections)

        # Single URLs are given
        if self.conf.urls:
            self.download(self.conf.urls)

        # Collection IDs are given
        if self.conf.save_urls is True:
            self.save_urls(collections_dict)
        elif len(collections_dict) > 0:
            self.download_collection(collections_dict)


def main():
    twitchloader = Twitchloader()
    twitchloader.run()


if __name__ == "__main__":
    main()
