# -*- coding: utf-8 -*-
"""Untitled4.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Xo49kJrDi3R1kb92QeN0Osbil2TvSs2M
"""

#!pip install -q git+https://github.com/openai/whisper.git > /dev/null --use-deprecated=legacy-resolver
#!pip install -q git+https://github.com/pyannote/pyannote-audio > /dev/null --use-deprecated=legacy-resolver

#!apt-get update
#!apt-get install -y nvidia-driver-470

#!nvidia-smi

import os
import json
import whisper
import datetime
import subprocess
import torch
import pyannote.audio
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
embedding_model = PretrainedSpeakerEmbedding(
    "speechbrain/spkrec-ecapa-voxceleb",
    device=torch.device("cuda"))
from pyannote.audio import Audio
from pyannote.core import Segment
import wave
import contextlib
from sklearn.cluster import AgglomerativeClustering
import numpy as np
from functools import reduce

#os.makedirs('audioFiles/'+'12345', exist_ok=True)
#os.makedirs('audioFiles/'+'12346', exist_ok=True)
#os.makedirs('audioFiles/'+'12347', exist_ok=True)

def getAllFiles():
    audioFilesDict = {}
    directory = 'audioFiles'
    for root, _, files in os.walk(directory):
          for file in files:
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            audioFilesDict[file_path] = file

    return audioFilesDict

filesDict = getAllFiles()

num_speakers = 2 #@param {type:"integer"}
language = 'English' #@param ['any', 'English']
model_size = 'large' #@param ['tiny', 'base', 'small', 'medium', 'large']
model_name = model_size
if language == 'English' and model_size != 'large':
  model_name += '.en'

for filePath in filesDict.keys():
  if filesDict[filePath][-3:] != 'wav':
    subprocess.call(['ffmpeg', '-i', filesDict[filePath], filesDict[filePath]+'.wav', '-y'])
    filesDict[filePath] = filesDict[filePath]+'.wav'

model = whisper.load_model(model_size)

segments = []
audioFrameRateDict = {}
for filePath in filesDict.keys():
  print(filesDict[filePath])
  result = model.transcribe(filePath)
  result["segments"] = list(map(lambda d:{**d, filePath: filesDict[filePath]},result["segments"]))
  segments.append(result["segments"])
  with contextlib.closing(wave.open(filePath,'r')) as f:
    audioFrameRateDict[filePath] = {'frames':f.getnframes(), 'rate':f.getframerate(), 'duration':f.getnframes() / float(f.getframerate())}

audio = Audio(sample_rate=16000, mono="downmix")
def segment_embedding(segment,duration,path):
  start = segment["start"]
  # Whisper overshoots the end timestamp in the last segment
  end = min(duration, segment["end"])
  clip = Segment(start, end)
  waveform, sample_rate = audio.crop(path, clip)
  return embedding_model(waveform[None])

#segmentList = reduce(lambda x,y : x+y,segments)
embeddingsDict = {}
for segmentList in segments:
  segmentPath = ""
  embeddings = np.zeros(shape=(len(segmentList), 192))
  for i, segment in enumerate(segmentList):
    path,fileName = list(segment.items())[-1]
    duration = audioFrameRateDict[path]["duration"]
    segmentPath = path
    print(path)
    print(embeddings)
    embeddings[i] = segment_embedding(segment,duration,path)
  embeddings = np.nan_to_num(embeddings)
  embeddingsDict[segmentPath] = embeddings

pathSegmentListDict={}
for segmentList in segments:
    for i, segment in enumerate(segmentList):
      pathSegmentListDict[list(segment)[-1]] = segmentList

print(pathSegmentListDict)

for path in embeddingsDict.keys():
  print("*"*20)
  print(len(embeddingsDict[path]))
  if len(embeddingsDict[path]) == 1:
    for i in range(len(pathSegmentListDict[path])):
      print(path)
      last_underscore_index = pathSegmentListDict[path][i][path].rfind("_")
      dot_index = pathSegmentListDict[path][i][path].rfind(".")
      pathSegmentListDict[path][i]["speaker"] = 'SPEAKER 1'
      pathSegmentListDict[path][i]["dateTime"] = pathSegmentListDict[path][i][path][last_underscore_index + 1:dot_index]
  else:
    clustering = AgglomerativeClustering(num_speakers).fit(embeddingsDict[path])
    labels = clustering.labels_
    print(labels)
    for i in range(len(pathSegmentListDict[path])):
      last_underscore_index = pathSegmentListDict[path][i][path].rfind("_")
      dot_index = pathSegmentListDict[path][i][path].rfind(".")
      pathSegmentListDict[path][i]["speaker"] = 'SPEAKER ' + str(labels[i] + 1)
      pathSegmentListDict[path][i]["dateTime"] = pathSegmentListDict[path][i][path][last_underscore_index + 1:dot_index]
print(pathSegmentListDict)

for key in pathSegmentListDict.keys():
  firstIndex = key.rfind("/")
  lastIndex = key.rfind(".")
  os.makedirs('diarizedFiles/'+key.split("/")[2], exist_ok=True)
  file_path = 'diarizedFiles/'+key.split("/")[2]
  dataFile = json.dumps(pathSegmentListDict[key], indent=2)
  with open(file_path+"/"+key[firstIndex + 1 : lastIndex]+".json", "w+") as f:
    json.dump(dataFile, f)