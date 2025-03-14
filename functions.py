from pytubefix import YouTube
from pytubefix import Playlist
import os
import subprocess
import simpleaudio as sa
from pydub import AudioSegment
from pydub.playback import play
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import time
import glob
import unicodedata
import re

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ FFmpeg est bien installé.")
        return True
    except FileNotFoundError:
        print("❌ FFmpeg n'est pas installé ou pas dans le PATH.")
        return False

def convert_audio(input_file, output_file):
    try:
        command = f"ffmpeg -i \"{input_file}\" \"{output_file}\""
        subprocess.run(command, shell=True, check=True)
        command2 = f'rm \"{input_file}\"'
        subprocess.run(command2, shell=True, check=True)
        print(f"✅ Conversion terminée : {output_file}")
    except Exception as e:
        print(f"❌ Erreur lors de la conversion : {e}")

def play_audio(file):
    audio = AudioSegment.from_wav(file)
    print("🎧 Lecture de l'audio...")
    play(audio)
    
def get_video_infos(url):
    try:
        yt = YouTube(url)
        title = yt.title
        channel = yt.author
        views = yt.views
        publish_date = yt.publish_date.strftime("%d-%m-%Y") if yt.publish_date else "N/A"

        return {
            "title": title,
            "url": url,
            "channel": channel,
            "views": views,
            "date": publish_date
        }
    except Exception as e:
        print(f"❌ Erreur sur la vidéo {url} : {e}")
        return None
    
def get_playlist_infos(playlist_name,playlist_url):
    try:
        playlist = Playlist(playlist_url)
        print(f"📌 Playlist : {playlist.title}")
        print(f"Nombre de vidéos : {len(playlist.video_urls)}\n")
        urls = []
        titles = []
        channels = []
        views = []
        dates = []
        if f"{playlist_name}.csv" not in os.listdir(os.path.join(os.getcwd(),"playlists")):
            videos_from_playlist = pd.DataFrame(
                data= {
                    "url": [],
                "title": [],
                "channel": [],
                "view": [],
                "date": [],
                }
            )
        else:
             videos_from_playlist = pd.read_csv(os.path.join(os.getcwd(),"playlists",f"{playlist_name}.csv"))
        previous_urls = list(videos_from_playlist["url"].unique())
        for index, url in enumerate(playlist.video_urls, start=1):
            if url not in previous_urls:
                video = get_video_infos(url)
                if video:
                    urls.append(video["url"])
                    titles.append(video["title"])
                    channels.append(video["channel"])
                    views.append(video["views"])
                    dates.append(video["date"])
        new_videos_from_playlist = pd.DataFrame(
            data = {
                "url": urls,
                "title": titles,
                "channel": channels,
                "view": views,
                "date": dates
            }
        )
        videos_from_playlist = pd.concat([videos_from_playlist, new_videos_from_playlist])
        videos_from_playlist = videos_from_playlist[videos_from_playlist["url"].apply(lambda x: x in [url for index, url in enumerate(playlist.video_urls, start=1)])]
        videos_from_playlist.to_csv(os.path.join(os.getcwd(),"playlists",f"{playlist_name}.csv"),index=False)
        print(f"\n✅ Liste exportée dans **{playlist_name}.csv**")
        return videos_from_playlist

    except Exception as e:
        print(f"❌ Erreur : {e}")
        
        
def clean_text(texte):
    # Supprimer les accents
    texte_sans_accents = ''.join(
        c for c in unicodedata.normalize('NFD', texte) if unicodedata.category(c) != 'Mn'
    )
    # Supprimer les caractères spéciaux (ne garder que lettres et chiffres)
    texte_sans_speciaux = re.sub(r'[^a-zA-Z0-9 ]', '', texte_sans_accents)
    # Option : Tout mettre en minuscule
    return texte_sans_speciaux.lower()

def clean_title(title, channel):
    return clean_text(title) + " | " + clean_text(channel)
        
def download_song(title,url):
    destination = os.path.join(os.getcwd(),"songs")
    if f"{title}.wav" in os.listdir(destination):
        return
    yt = YouTube(url)
    video = yt.streams.filter(only_audio=True).first()
    mp4_file = video.download(output_path=destination,filename=f"{title}.mp4")
    output_file = os.path.join(destination,f"{title}.wav")
    convert_audio(mp4_file, output_file)
    #os.remove(mp4_file)
    

def clean_old_files(folder_path, keep=30):
    """Supprime les fichiers les plus anciens dans un dossier et ne garde que les 'keep' fichiers les plus récents."""
    
    # Vérifier si le dossier existe
    if not os.path.exists(folder_path):
        print(f"❌ Le dossier '{folder_path}' n'existe pas.")
        return
    
    # Récupérer la liste des fichiers triés par date de modification (du plus récent au plus ancien)
    files = sorted(
        glob.glob(os.path.join(folder_path, "*")),  # Récupère tous les fichiers
        key=os.path.getmtime,  # Trie par date de modification
        reverse=True  # Du plus récent au plus ancien
    )
    
    # Fichiers à supprimer (ceux qui dépassent les 30 plus récents)
    files_to_delete = files[keep:]
    
    # Supprimer les fichiers anciens
    for file in files_to_delete:
        try:
            os.remove(file)
        except Exception as e:
            print(f"❌ Erreur en supprimant {file} : {e}")
    
def pass_to_next_song(session_state):
    if session_state.audio_obj:
        session_state.audio_obj.stop()
    if session_state.num_song == len(st.session_state.df_songs.index):
        session_state.is_playing = False
        return session_state
    if not session_state.loop:
        if session_state.num_song % 10 == 9:
            clean_old_files(os.path.join(os.getcwd(),"songs"))
        if session_state.lecture_style == "Random 🔀":
            session_state.song_title = list(st.session_state.df_songs["title"])[session_state.shuffle[session_state.num_song]]
            session_state.song_interpret = list(session_state.df_songs[session_state.df_songs["title"] == session_state.song_title]["channel"])[0]
            url = list(session_state.df_songs[session_state.df_songs["title"] == session_state.song_title]["url"])[0]
            download_song(clean_title(session_state.song_title, session_state.song_interpret),url)
            if clean_title(session_state.song_title, session_state.song_interpret) + ".wav" not in os.listdir(os.path.join(os.getcwd(),"songs")):
                session_state.num_song += 1
                return pass_to_next_song(session_state)
            session_state.audio = AudioSegment.from_wav(os.path.join(os.getcwd(),"songs",clean_title(session_state.song_title, session_state.song_interpret) + ".wav"))
            session_state.duration = len(session_state.audio) // 1000
            session_state.num_song += 1

        elif session_state.lecture_style == "Custom ⚙️":
            if len(session_state.sub_playlist) == session_state.num_song:
                session_state.is_playing = False
                return session_state
            session_state.song_title = session_state.sub_playlist[session_state.num_song].split(" | ")[0]
            session_state.song_interpret  = session_state.sub_playlist[session_state.num_song].split(" | ")[-1]
            url = list(session_state.df_songs[session_state.df_songs["title"] == session_state.song_title]["url"])[0]
            download_song(clean_title(session_state.song_title, session_state.song_interpret),url)
            if clean_title(session_state.song_title, session_state.song_interpret) + ".wav" not in os.listdir(os.path.join(os.getcwd(),"songs")):
                session_state.num_song += 1
                return pass_to_next_song(session_state)
            session_state.audio = AudioSegment.from_wav(os.path.join(os.getcwd(),"songs",clean_title(session_state.song_title, session_state.song_interpret) + ".wav"))
            session_state.duration = len(session_state.audio) // 1000
            session_state.num_song += 1
             
        elif session_state.lecture_style == "In order ➡️":
            session_state.song_title = list(session_state.df_songs["title"])[session_state.num_song]
            session_state.song_interpret = list(session_state.df_songs["channel"])[session_state.num_song]
            url = list(session_state.df_songs[session_state.df_songs["title"] == session_state.song_title]["url"])[0]
            download_song(clean_title(session_state.song_title, session_state.song_interpret),url)
            if clean_title(session_state.song_title, session_state.song_interpret) + ".wav" not in os.listdir(os.path.join(os.getcwd(),"songs")):
                session_state.num_song += 1
                return pass_to_next_song(session_state)
            session_state.audio = AudioSegment.from_wav(os.path.join(os.getcwd(),"songs",clean_title(session_state.song_title, session_state.song_interpret) + ".wav"))
            session_state.duration = len(session_state.audio) // 1000
            session_state.num_song += 1
    
        session_state.current_position = 0
        audio_raw = session_state.audio[0:].raw_data
        session_state.audio_obj = sa.play_buffer(audio_raw, num_channels=session_state.audio.channels,
            bytes_per_sample=session_state.audio.sample_width,
            sample_rate=session_state.audio.frame_rate
        )
        session_state.is_playing = True
        session_state.start_time = time.time() - session_state.current_position
    else:
        session_state.current_position = session_state.loop_begin
        audio_raw = session_state.audio[session_state.loop_begin * 1000:].raw_data
        session_state.audio_obj = sa.play_buffer(audio_raw, num_channels=session_state.audio.channels,
            bytes_per_sample=session_state.audio.sample_width,
            sample_rate=session_state.audio.frame_rate
        )
        session_state.is_playing = True
        session_state.start_time = time.time() - session_state.current_position
    return session_state
        