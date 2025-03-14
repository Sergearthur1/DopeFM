# DopeFM
Streamlit application to listen to Youtube playlist.

## Installation

Requirements:
- python >3.10
- python venv
- git


Linux:
```bash
git clone https://github.com/Sergearthur1/DopeFM.git
cd DopeFM
mkdir songs
mkdir playlists
git submodule update --init --recursive
python3 -m venv venv
source venv/bin/activate
chmod +x DopeFM_launcher.sh
pip install -r requirements.txt
```

Windows:
```bash
git clone https://github.com/Sergearthur1/DopeFM.git
cd DopeFM
mkdir songs
mkdir playlists
git submodule update --init --recursive
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
# Launch the application
Windows: double click on DopeFM_launcher.bat.

Linux: execute DopeFM_launcher.sh with this command:
```bash
.\DopeFM_launcher.sh
```
