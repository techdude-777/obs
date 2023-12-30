"""Modification of the url-text default script in OBS to get events from the Google Calendar API"""
#Reading ical calendar to reade eventzs from ChurchTools and trigger OBS
#2023-12-29, Uli Schnaidt, adapted Google Calendar script

from __future__ import print_function
import httplib2
import os
import pytz
import time

from ics import Calendar

import requests
import obspython as obs
import urllib.request
import urllib.error

from datetime import datetime, timedelta, timezone

resync      = 0
cal_url     = ""
interval    = 60
max_events  = 4


# ------------------------------------------------------------

def update_actions():
    global cal_url
    global interval
    global source_names
    global CLIENT_SECRET_FILE
    global max_events
    global images_path
    global image_sources
    global resync
    global read_cal
    global cal
    global streamstart_offset
    
    resync_secs = 1
    
    #service = discovery.build('calendar', 'v3', http=http)
    
    #https://learnpython.com/blog/working-with-icalendar-with-python/
    
  
    
    #init the calendar
    if read_cal > 0:
        read_cal=0
        cal = Calendar(requests.get(cal_url).text)
        print(cal.events)
        
    # Time objects using datetime
    dt_now = datetime.utcnow()
    
    #print(dt_now)
    
    #Try to resync to 0 seconds
    if (dt_now.second % interval > resync_secs):
        sleep_sec = interval - (dt_now.second % interval)
        resync += 1
        print(resync)
        print("Resyncing by :")
        print(sleep_sec)
        obs.timer_remove(update_actions) 
        obs.timer_add(update_actions, sleep_sec * 1000)
        
    elif (resync > 0):
        resync = 0
        obs.timer_remove(update_actions)
        obs.timer_add(update_actions, interval * 1000)
    
    count = 0
    stream_event_happening = False
    record_event_happening = False
    
    
    
    #print(dt_now)
    #print(cal.events)
    
    for event in cal.events:
        count += 1
        # Streaming
        if (dt_now<=event.begin.naive<=(dt_now+timedelta(minutes=streamstart_offset))):
            print(event.name + " => Streaming")
            print("Start um:")
            print(event.begin)
            print("Also in: ")
            print(event.begin.naive - dt_now)
    
            # Checks for the "Stream" event and starts streaming if not doing so already
            #if text == "Stream":
            #    stream_event_happening = True
            #    if ~obs.obs_frontend_streaming_active():
            #        obs.obs_frontend_streaming_start()
            
            # Likewise, checks for "Record" event
            record_event_happening = True
            if ~obs.obs_frontend_recording_active():
                obs.obs_frontend_recording_start()
                

        for x in range(max_events-1,-1,-1):
            # Scene x
            if ( dt_now-timedelta(seconds = resync_secs+1) <= event.begin.naive <= (dt_now+timedelta(seconds = resync_secs+1, minutes=scene_offsets[x]))):
                print(event.name + " => Scene {} ".format(x))
                print("Start um:")
                print(event.begin)
                print("Also in: ")
                print(event.begin.naive - dt_now)
        
                if (scene_names[x]!= ""):
                   set_current_scene(scene_names[x])
                   
                break
               
               


# ------------------------------------------------------------

def refresh_pressed(props, prop):
    update_actions()

# ------------------------------------------------------------

def script_description():
    return "Triggers actions if a calender entry exists. \n" \
           " - Specify the corresponding offsets to trigger an action\n" \
           " - Note: if a scene offset is matched the other scenes are not processed.\n" \
           "   So make sure that your lowest scene number has the highest time offset.\n" \
           " - Calendar is read once if activated.\n" \
           "That's it."

# ------------------------------------------------------------

def set_current_scene(scene_name):
        scenes = obs.obs_frontend_get_scenes()
        current_scene = obs.obs_frontend_get_current_scene()
        current_scene_name = obs.obs_source_get_name(current_scene)
        print("Da willst du hin:" + scene_name)
        print("Da bist du: " + current_scene_name)
        if (current_scene_name !=scene_name):        
            for scene in scenes:
                name = obs.obs_source_get_name(scene)
                if name == scene_name:
                    obs.obs_frontend_set_current_scene(scene)
            obs.source_list_release(scenes)

# ------------------------------------------------------------


def script_update(settings):
    global cal_url
    global interval
    global scene_names
    global scene_offsets
    global max_events
    global ical_active
    global read_cal
    global streamstart_offset
   
    read_cal = 1 #=> re-read calendar
    ical_active            = obs.obs_data_get_bool(settings, "ical_active")
    cal_url                = obs.obs_data_get_string(settings, "calendar_url")
    interval               = obs.obs_data_get_int(settings, "interval")
    max_events             = obs.obs_data_get_int(settings, "max_events")
    streamstart_offset     = obs.obs_data_get_int(settings, "streamstart_offset")
     
     
    scene_names = [None]*max_events
    scene_offsets = [0]*max_events
    
    for x in range(0, max_events):
       scene_names[x]   = obs.obs_data_get_string(settings, "scene_{}".format(x))
       scene_offsets[x] = obs.obs_data_get_int(settings, "scene_{}_offset".format(x))
           
    obs.timer_remove(update_actions)

    if (cal_url != "" and ical_active):
        obs.timer_add(update_actions, interval * 1000)

# ------------------------------------------------------------

def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "interval", 30)
    obs.obs_data_set_default_int(settings, "max_events", 3)
    obs.obs_data_set_default_int(settings, "streamstart_offset", 25)
    obs.obs_data_set_default_int(settings, "scene_0_offset", 0)
    obs.obs_data_set_default_int(settings, "scene_1_offset", 25)
    obs.obs_data_set_default_int(settings, "scene_2_offset", 29)
    obs.obs_data_set_default_int(settings, "scene_3_offset", 0)
    obs.obs_data_set_default_string(settings, "scene_0", "00_Info_Intro")
    obs.obs_data_set_default_string(settings, "scene_1", "00_Info_Intro + Countdown")
    obs.obs_data_set_default_string(settings, "scene_2", "00_Info_Intro + Countdown 2")
    obs.obs_data_set_default_string(settings, "scene_3", "01_Intro")


# ------------------------------------------------------------

def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_bool(props, "ical_active", "Active")

    obs.obs_properties_add_text(props, "calendar_url", "Calendar URL", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, "interval", "Update Interval (seconds)", 5, 3600, 1)
    obs.obs_properties_add_int(props, "max_events", "Max Number of Scenes", 1, 15, 1)
    
    obs.obs_properties_add_int(props, "streamstart_offset", "Offset to start Streaming (min)", 0, 30, 1)
     
    
    for x in range(0,max_events):
        
        obs.obs_properties_add_int(props, "scene_{}_offset".format(x), "Offset to switch to scene {} (min)".format(x + 1), 0, 30, 1)
        
        p = obs.obs_properties_add_list(props, "scene_{}".format(x), "Scene {}".format(x + 1), 
                                        obs.OBS_COMBO_TYPE_EDITABLE, obs.OBS_COMBO_FORMAT_STRING)

   
        scenes = obs.obs_frontend_get_scene_names()
        if scenes is not None:
            for scene in scenes:                     
                obs.obs_property_list_add_string(p, scene, scene)
                                
            obs.source_list_release(scenes)

    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props