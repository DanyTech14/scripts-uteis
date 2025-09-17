# Script para download de músicas e vídeos do Spotify e YouTube
# Requisitos:
# - Crie uma conta de desenvolvedor no Spotify: https://developer.spotify.com/
# - Crie um app e obtenha CLIENT_ID e CLIENT_SECRET
# - Instale as bibliotecas: pip install spotipy yt-dlp
# - Instale o FFmpeg: https://www.gyan.dev/ffmpeg/builds/ (adicione ao PATH ou especifique o caminho abaixo)
# - Este script baixa metadados do Spotify e usa o YouTube como proxy para áudio (não oficial do Spotify)
# - Para Spotify: Suporta playlists, álbuns e faixas individuais (públicas), baixadas como MP3
# - Para YouTube: Suporta playlists e vídeos individuais, com opção de MP3 (música) ou MP4 (vídeo)
# - Downloads salvos na área de trabalho: C:\Users\<SeuUsuário>\Desktop\downloads
# - Pasta de downloads criada antes de iniciar os downloads
# - Arquivos baixados um de cada vez, de forma sequencial
# - Funciona para conteúdos públicos; conteúdos privados precisam de autenticação adicional
# - Use por sua conta e risco; respeite direitos autorais

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import os
import time
import shutil
import re

# Configurações - SUBSTITUA PELOS SEUS VALORES
CLIENT_ID = '15d180df1bc54b8789505890482b3f6e'  # Ex: '123abc456def789ghi'
CLIENT_SECRET = 'da152d433a74400995edac0074516d3e'  # Ex: 'jklmno987pqr654stu'
# Opcional: especifique o caminho do ffmpeg.exe (ex: r'C:\ffmpeg\bin\ffmpeg.exe') se não estiver no PATH
FFMPEG_PATH = r'C:\ffmpeg\ffmpeg-8.0-essentials_build\ffmpeg-8.0-essentials_build\bin'
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Desktop', 'downloads')  # Pasta na área de trabalho

# Cria pasta de download antes de iniciar
def create_download_dir():
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        print(f"Pasta de downloads criada em: {DOWNLOAD_DIR}")
    except Exception as e:
        print(f"Erro ao criar pasta de downloads: {e}")
        exit(1)

# Verifica se o FFmpeg está instalado
def check_ffmpeg():
    if FFMPEG_PATH:
        return os.path.exists(FFMPEG_PATH)
    return shutil.which('ffmpeg') is not None and shutil.which('ffprobe') is not None

# Função para parsear o link e extrair tipo e ID
def parse_link(link):
    if 'spotify.com' in link:
        if '/playlist/' in link:
            type_ = 'playlist'
            id_ = re.search(r'/playlist/([^?]+)', link).group(1)
        elif '/album/' in link:
            type_ = 'album'
            id_ = re.search(r'/album/([^?]+)', link).group(1)
        elif '/track/' in link:
            type_ = 'track'
            id_ = re.search(r'/track/([^?]+)', link).group(1)
        else:
            raise ValueError("Link do Spotify inválido. Suporta playlist, album ou track.")
        return 'spotify', type_, f'spotify:{type_}:{id_}'
    elif 'youtube.com' in link or 'youtu.be' in link:
        if 'playlist?list=' in link:
            type_ = 'playlist'
            id_ = re.search(r'list=([^&]+)', link).group(1)
            uri = f'https://www.youtube.com/playlist?list={id_}'
        elif 'watch?v=' in link:
            type_ = 'video'
            id_ = re.search(r'v=([^&]+)', link).group(1)
            uri = f'https://www.youtube.com/watch?v={id_}'
        elif 'youtu.be/' in link:
            type_ = 'video'
            id_ = re.search(r'youtu.be/([^?]+)', link).group(1)
            uri = f'https://youtu.be/{id_}'
        else:
            raise ValueError("Link do YouTube inválido. Suporta playlist ou vídeo individual.")
        return 'youtube', type_, uri
    else:
        raise ValueError("Link inválido. Deve ser do Spotify ou YouTube.")

# --- Funções do Spotify ---
def init_spotify():
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))
        print("Autenticação com Spotify bem-sucedida.")
        return sp
    except Exception as e:
        print(f"Erro na autenticação com Spotify: {e}")
        exit(1)

def get_spotify_tracks(service_type, uri, sp):
    try:
        if service_type == 'playlist':
            results = sp.playlist_tracks(uri, fields='items(track(name,artists(name)))', market='BR')
            tracks = results.get('items', [])
            while results.get('next'):
                results = sp.next(results)
                tracks.extend(results.get('items', []))
                time.sleep(1)
        elif service_type == 'album':
            results = sp.album_tracks(uri, market='BR')
            tracks = results.get('items', [])
            while results.get('next'):
                results = sp.next(results)
                tracks.extend(results.get('items', []))
                time.sleep(1)
        elif service_type == 'track':
            track = sp.track(uri, market='BR')
            name = track.get('name', 'Unknown')
            artist = track.get('artists', [{}])[0].get('name', 'Unknown')
            return [f"{name} - {artist}"]
        
        track_list = []
        for item in tracks:
            track = item.get('track') if service_type == 'playlist' else item
            if track:
                name = track.get('name', 'Unknown')
                artist = track.get('artists', [{}])[0].get('name', 'Unknown')
                track_list.append(f"{name} - {artist}")
        return track_list
    except spotipy.exceptions.SpotifyException as e:
        print(f"Erro da API do Spotify: HTTP {e.http_status} - {e.msg}")
        if e.http_status == 404:
            print("Recurso não encontrado. Verifique o ID ou se o conteúdo é público.")
        elif e.http_status == 401:
            print("Erro de autenticação. Verifique CLIENT_ID e CLIENT_SECRET.")
        return []
    except Exception as e:
        print(f"Erro inesperado ao buscar faixas do Spotify: {e}")
        return []

# --- Funções do YouTube ---
def download_youtube_content(query_or_url, is_search, format_choice):
    ydl_opts = {
        'format': 'bestaudio/best' if format_choice == 'mp3' else 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'quiet': True,
    }
    
    if format_choice == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    elif format_choice == 'mp4':
        ydl_opts['merge_output_format'] = 'mp4'
    
    if FFMPEG_PATH:
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            if is_search:
                search_query = f"ytsearch1:{query_or_url}"
                print(f"Buscando no YouTube: {query_or_url}")
                ydl.download([search_query])
            else:
                ydl.download([query_or_url])
            print(f"Download concluído: {query_or_url}")
        except Exception as e:
            print(f"Erro ao baixar {query_or_url}: {e}")

# --- Execução Principal ---
if __name__ == "__main__":
    # Cria a pasta de downloads antes de qualquer coisa
    create_download_dir()
    
    # Verifica FFmpeg
    if not check_ffmpeg():
        print("Erro: FFmpeg não encontrado. Instale o FFmpeg e adicione ao PATH ou especifique FFMPEG_PATH no script.")
        print("Instruções: Baixe em https://www.gyan.dev/ffmpeg/builds/, extraia e adicione a pasta 'bin' ao PATH.")
        exit(1)
    
    # Entrada do link
    link = input("Insira o link do Spotify ou YouTube (playlist, album/track para Spotify; playlist/video para YouTube): ").strip()
    
    try:
        service, type_, uri = parse_link(link)
        print(f"Detectado: {service.capitalize()} - {type_.capitalize()}")
        
        if service == 'spotify':
            sp = init_spotify()
            print("Buscando faixas do Spotify...")
            tracks = get_spotify_tracks(type_, uri, sp)
            if not tracks:
                print("Nenhuma faixa encontrada. Verifique o link ou se o conteúdo é público.")
                exit(1)
            print(f"Encontradas {len(tracks)} faixas.")
            for i, track in enumerate(tracks, 1):
                print(f"Processando {i}/{len(tracks)}: {track}")
                download_youtube_content(track, is_search=True, format_choice='mp3')  # Busca no YouTube como MP3
                time.sleep(2)  # Garante download sequencial
        else:  # YouTube
            format_choice = input("Deseja baixar como [1] Música (MP3) ou [2] Vídeo (MP4)? Digite 1 ou 2: ").strip()
            if format_choice not in ['1', '2']:
                print("Opção inválida. Escolha 1 (MP3) ou 2 (MP4).")
                exit(1)
            format_choice = 'mp3' if format_choice == '1' else 'mp4'
            print(f"Baixando como {format_choice.upper()}...")
            download_youtube_content(uri, is_search=False, format_choice=format_choice)
            time.sleep(2)  # Garante download sequencial
        
        print("Download finalizado!")
    except ValueError as ve:
        print(f"Erro no link: {ve}")
    except Exception as e:
        print(f"Erro inesperado: {e}")