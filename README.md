# twitchloader

Download VOD videos and complete collections from Twitch.tv using youtube-dl.

## Requirements

- Python 3.6 or higher
- poetry (pip install poetry)

## Installation

`poetry install`  
This sets up a virtual environment and installs all dependencies.  
This should be done after every update in order to always have all dependencies installed.

### Twitch API Client ID

This program uses the Twitch.tv API. Therefore you have to get your own client id by creating an application on https://dev.twitch.tv/.

## Usage

Activate the virtual environment:  
`poetry shell`  
After that you can run the other commands.  

Run the program:  
`python twitchloader.py`  

Get information about the usage:  
`python twitchloader.py --help`  

Show all VOD collections of a channel:  
`python twitchloader.py -t <your client id> --show-collections -C <channel to search for>`

Download ALL collections of a channel:  
`python twitchloader.py -t <your client id> -C <channel to search for>`

Download a collection (multiple ids can be given):  
`python twitchloader.py -t <your client id> --collection-id  <collection id>`

All other options can be are explained in the help message (`--help`).  

### Download videos that require a subscription to view

On some Twitch Channels you can only watch the VOD videos if you are a subscriber of that channel. For that you have to give the program your Twitch account credentials. This can be either done by specifying username and password in the Youtube-DL settings inside the config file or through the `ydl-options` argument.  

This method however has a drawback. When logging in Twitch sometimes asks you to enter a verification code sent to your E-Mail in order to log in. To avoid this you should use the **prefered method**: Use the `cookiefile` setting in the `ydl-options` to provide a textfile with the cookies for a login session. Look online for ways of exporting browser cookies to a textfile (in the netscape format) and how to use them with youtube-dl or use this extension for [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/?src=search) or this one for [Chrome](https://chrome.google.com/webstore/detail/cookiestxt/njabckikapfpffapmjgojcnbfjonfjfg). Using extensions is not recommended since they can pose a security risk.  

## Configuration

All settings can be configured in the file [config.yaml](config.yaml). The default config path is `config.yaml`, but can the configured using the `-c` argument.  
