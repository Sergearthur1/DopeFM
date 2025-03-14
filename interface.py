from functions import *
import streamlit as st
import sys
import matplotlib.pyplot as plt
sys.setrecursionlimit(15000)

if "df_playlist" not in st.session_state:
    st.session_state.df_playlist = pd.read_csv("playlist.csv")
    st.session_state.playlist_name = None

playlist_name = st.sidebar.selectbox(
    "choose a playlist", 
     list(st.session_state.df_playlist["title"].unique()) + ["add a new playlist"],
)
st.title("🎧 Dope FM 🎧 ")

if playlist_name:
    if playlist_name == "add a new playlist":
        name = st.text_input("New Playlist Title", "Please enter the Playlist name here")
        url = st.text_input("New Playlist URL", "Please enter the Playlist URL here")
        if (name != "Please enter the Playlist name here") and (url != "Please enter the Playlist URL here"):
            st.session_state.df_playlist = pd.concat(
                [
                    st.session_state.df_playlist,
                    pd.DataFrame(
                        data={
                            "title": [name],
                            "url": [url]
                        }
                    )
                ]
            )
            st.session_state.df_playlist.to_csv("playlist.csv",index=False)
            st.write(" ⌛The Playlist is charging ... ⌛")
            get_playlist_infos(name,url)
            st.write("Playlist Charged. Refresh the page to move your ass on it ! 🔥")
        
    elif playlist_name != st.session_state.playlist_name:
        url = list(st.session_state.df_playlist[st.session_state.df_playlist["title"] == playlist_name]["url"])[0]
        st.session_state.df_songs = get_playlist_infos(playlist_name, url)
        st.session_state.playlist_name = playlist_name
        st.session_state.shuffle = np.arange(len(st.session_state.df_songs.index))
        np.random.shuffle(st.session_state.shuffle)
    lecture_style = st.sidebar.radio("Playlist lecture style", ["In order ➡️", "Random 🔀", "Custom ⚙️", None],index=3)
    st.session_state.lecture_style = lecture_style
    if st.session_state.lecture_style == "Custom ⚙️":
        if "sub_playlist" not in st.session_state:
            st.session_state.num_song = 0
        st.session_state.sub_playlist = st.sidebar.multiselect(
            "select your next songs",
            [col["title"] + " | " + col["channel"] for idx, col in st.session_state.df_songs.iterrows()],
            label_visibility="hidden",
        )
        st.sidebar.write("Next songs:", st.session_state.sub_playlist[st.session_state.num_song:])

if (st.session_state.lecture_style in ["In order ➡️", "Random 🔀"]) or (st.session_state.lecture_style == "Custom ⚙️" and len(st.session_state.sub_playlist) > 0):

    # Stockage de l'état de lecture
    if "is_playing" not in st.session_state:
        st.session_state.is_playing = False
        st.session_state.start_time = 0
        st.session_state.audio_obj = None
        st.session_state.current_position = 0
        st.session_state.loop = False
        st.session_state.num_song = 0
        st.session_state = pass_to_next_song(st.session_state)
        st.session_state.audio_obj.stop()
        st.session_state.is_playing = False

    # Boutons de contrôle
    col1, col2, col3, col4 = st.columns(4)
    with col2:
        if st.button("⏹️ Stop"):
            if st.session_state.is_playing and st.session_state.audio_obj:
                st.session_state.audio_obj.stop()
                st.session_state.is_playing = False
    with col1:
        if st.button("▶️ Play"):
            if not st.session_state.is_playing:
                # Convertir audio en raw
                audio_raw = st.session_state.audio[st.session_state.current_position * 1000:].raw_data
                st.session_state.audio_obj = sa.play_buffer(audio_raw, num_channels=st.session_state.audio.channels,
                                                            bytes_per_sample=st.session_state.audio.sample_width,
                                                            sample_rate=st.session_state.audio.frame_rate)
                st.session_state.is_playing = True
                st.session_state.start_time = time.time() - st.session_state.current_position
    with col3:
        if st.button("Loop 🔁"):
            if not st.session_state.loop:
                st.session_state.loop = True
                st.write("Repeat mode activated")
            else:
                st.session_state.loop = False  
                st.write("Repeat mode deactivated")
    with col4:
        if st.button("Next ➡️"):
            pass_to_next_song(st.session_state)

    st.markdown(f"# {st.session_state.song_title} | {st.session_state.song_interpret}", unsafe_allow_html=True)
    position = st.slider("", 0, st.session_state.duration, int(st.session_state.current_position))
    if st.session_state.loop:
        st.markdown("## Loop Parameters")
        st.session_state.loop_begin = float(st.text_input("Choose the starting time of the loop (in seconds)", "0"))
        st.session_state.loop_end = float(
            st.text_input(
                "Choose the ending time of the loop (in seconds)", 
                st.session_state.duration,
            )
        )
    if position != int(st.session_state.current_position):
        st.session_state.start_time += (st.session_state.current_position - position)
        st.session_state.current_position = position
        if st.session_state.is_playing:
            st.session_state.audio_obj.stop()
        else:
            st.session_state.is_playing = True
        audio_raw = st.session_state.audio[st.session_state.current_position * 1000:].raw_data
        st.session_state.audio_obj = sa.play_buffer(audio_raw, num_channels=st.session_state.audio.channels,
                                                    bytes_per_sample=st.session_state.audio.sample_width,
                                                    sample_rate=st.session_state.audio.frame_rate)
    if st.session_state.is_playing:
        time.sleep(0.2)
        st.session_state.current_position = time.time() - st.session_state.start_time
        if  st.session_state.loop:
            if st.session_state.current_position >= st.session_state.loop_end:
                st.session_state = pass_to_next_song(st.session_state)
        elif st.session_state.current_position >= st.session_state.duration:
            st.session_state = pass_to_next_song(st.session_state)
        st.experimental_rerun()
