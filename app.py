from flask import Flask
from flask import render_template
from flask import send_file
import time
import os
import os.path
import json
import numpy as np
import pandas as pd
import seaborn as sns

import io
from base64 import encodebytes
from PIL import Image
from flask import jsonify

import matplotlib.pyplot as plt
from matplotlib import cm
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from riotwatcher import LolWatcher, ApiError

app = Flask(__name__)
api_key = os.environ.get("RIOT_API")
region = 'euw1'
lol_watcher = LolWatcher(api_key)

def get_response_image(image_path):
    pil_img = Image.open(image_path, mode='r') # reads the PIL image
    byte_arr = io.BytesIO()
    pil_img.save(byte_arr, format='PNG') # convert the PIL image to byte array
    encoded_img = encodebytes(byte_arr.getvalue()).decode('ascii') # encode as base64
    return encoded_img

@app.route("/<name>")
def get_player_map(name):
    player = lol_watcher.summoner.by_name(region, str(name))
    
    #matchNumber = 1
    matchList = lol_watcher.match.matchlist_by_puuid(puuid=player['puuid'], region='EUROPE')
    # one_match = lol_watcher.match.timeline_by_match(match_id=matchList[matchNumber], region='EUROPE')

    # kills = pd.DataFrame()
    # killerIdList = []
    imgPaths = []
    img = plt.imread('./static/images/summoners-rift.jpg')
    
    customPlayerPath = 'static/images/' + name
    
    if os.path.isdir(customPlayerPath) == False:
        os.makedirs(customPlayerPath)
    
    for matchNumber in range(len(matchList)):
        match = lol_watcher.match.timeline_by_match(match_id=matchList[matchNumber], region='EUROPE')
        kills = pd.DataFrame()
        killerIdList = []

        for i in range(len(match.get('info')['frames'])):
            frameEvents = match.get('info')['frames'][i]['events']
            for j in range(len(frameEvents)):
                if 'position' in frameEvents[j]:
                    if frameEvents[j]['type'] == 'CHAMPION_KILL':
                        kills = kills.append(frameEvents[j]['position'], ignore_index=True)
                        killerIdList.append(frameEvents[j]['killerId'])

        kills['killerId'] = killerIdList
        kills.loc[kills['killerId'] <= 5, 'killerId'] = 1
        kills.loc[kills['killerId'] > 5, 'killerId'] = 2

        if ('x' in kills.columns):
            fig, ax = plt.subplots()

            ax.imshow(img, extent=[0, 14000, 0, 14000])
    
            ax.scatter(x=kills.x, y=kills.y, c=kills.killerId, cmap='seismic')

            customMatchPath = customPlayerPath + '/' + str(match.get('metadata')['matchId']) + '.png'
            
            imgPaths.append(customMatchPath)
            
            if os.path.isfile(customMatchPath) == False:
                plt.savefig(customMatchPath)


    encoded_imges = []
    for image_path in imgPaths:
        encoded_imges.append(get_response_image(image_path))
    return jsonify({'result': encoded_imges})