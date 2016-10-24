import os
import datetime
import time

from slackclient import SlackClient
import tvdb_api

from settings import *

HOUR = 0
MIN = 0

slack_client = SlackClient(BOT_TOKEN)
t = tvdb_api.Tvdb()


def get_latest_episode():
    show = t[SHOW]
    last_aired = None
    now = datetime.datetime.now()
    for s in show:
        season = show[s]
        for e in season:
            episode = season[e]
            aired = datetime.datetime.strptime(episode['firstaired'] + ' ' + show['airs_time'], '%Y-%m-%d %I:%M %p')
            if aired < now:
                last_aired = episode
            else:
                return last_aired

def parse_episode_title(episode):
    return "Latest Episode: " + episode['firstaired'] + " " + episode['seasonnumber'] + "x" + episode['episodenumber'] + " " + episode['episodename']

def get_channel_topic(channel):
    info = slack_client.api_call('channels.info', channel=channel)
    return info['channel']['topic']['value']

def update_channel_topic(channel, topic):
    print slack_client.api_call('channels.setTopic', channel=channel, topic=topic)

def get_channel_list():
    return slack_client.api_call('channels.list')['channels']

def get_my_channels():
    all_channels = get_channel_list()
    my_channels = []
    for channel in all_channels:
        if channel['is_member']:
            if DEBUG:
              print channel
            my_channels.append(channel['id'])
    return my_channels

def timed_commands():
    now = datetime.datetime.now()
    global HOUR
    global MIN
    if now.hour != HOUR:
        if DEBUG:
            print "New Hour: " + str(now.hour)
        run_hourly_commands()
        HOUR = now.hour
    if now.minute != MIN:
        if DEBUG:
            print "New Minute: " + str(now.minute)
        run_minute_commands()
        MIN = now.minute

def run_hourly_commands():
    topic = parse_episode_title(get_latest_episode())
    if DEBUG:
        print topic
    my_channels = get_my_channels()
    for channel in my_channels:
        channel_topic = get_channel_topic(channel)
        if channel_topic != topic:
            update_channel_topic(channel, topic)

def run_minute_commands():
    return True

def handle_command(command, channel, user):
    response = "NERD"
    if command.startswith(SUP_COMMAND):
        print slack_client.api_call('channels.kick', channel=channel, user=user)
    if command.startswith(CURRENT_COMMAND):
        current = get_latest_episode()
        response = parse_episode_title(get_latest_episode())
        topic = get_channel_topic(channel)
        if topic != response:
            update_channel_topic(channel, response)

    print slack_client.api_call('chat.postMessage', channel=channel, text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                        output['channel'], \
                        output['user']
    return None, None, None

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1
    if slack_client.rtm_connect():
        print("Westbot connected and running")
        HOUR = datetime.datetime.now().hour
        if DEBUG:
            print "Cur Hour: " + str(HOUR)
        MIN = datetime.datetime.now().minute
        if DEBUG:
            print "Cur Min: " + str(MIN)
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
            timed_commands()
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print('Connection failed. Invalid slack token or bot id?')
