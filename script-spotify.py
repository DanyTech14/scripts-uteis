# Script para baixar vídeos ou músicas do YouTube

import yt_dlp
import os
import shutil
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configurações
FFMPEG_PATH = r'C:\ffmpeg\ffmpeg-8.0-essentials_build\ffmpeg-8.0-essentials_build\bin'
DOWNLOAD_DIR = os.path.join(os.path.expanduser('~'), 'Desktop', 'downloads')

def create_download_dir():
    if os.path.exists(DOWNLOAD_DIR):
        print(f"Pasta de downloads já existe: {DOWNLOAD_DIR}")
    else:
        try:
            os.makedirs(DOWNLOAD_DIR)
            print(f"Pasta de downloads criada: {DOWNLOAD_DIR}")
        except Exception as e:
            raise RuntimeError(f"Erro ao criar pasta: {e}")

def check_ffmpeg():
    if FFMPEG_PATH:
        return os.path.exists(FFMPEG_PATH)
    return shutil.which('ffmpeg') and shutil.which('ffprobe')

def parse_youtube_link(link):
    if 'youtube.com' in link or 'youtu.be' in link:
        if 'playlist?list=' in link:
            id_ = re.search(r'list=([^&]+)', link)
            if not id_:
                raise ValueError("Link de playlist inválido.")
            uri = f'https://www.youtube.com/playlist?list={id_.group(1)}'
            type_ = 'playlist'
        elif 'watch?v=' in link:
            id_ = re.search(r'v=([^&]+)', link)
            if not id_:
                raise ValueError("Link de vídeo inválido.")
            uri = f'https://www.youtube.com/watch?v={id_.group(1)}'
            type_ = 'video'
        elif 'youtu.be/' in link:
            id_ = re.search(r'youtu.be/([^?]+)', link)
            if not id_:
                raise ValueError("Link de vídeo inválido.")
            uri = f'https://youtu.be/{id_.group(1)}'
            type_ = 'video'
        else:
            raise ValueError("Link do YouTube inválido.")
        return type_, uri
    else:
        raise ValueError("Link inválido.")

def get_playlist_videos(playlist_url):
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
    }
    video_urls = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry and 'url' in entry:
                        video_urls.append(f"https://www.youtube.com/watch?v={entry['url']}")
    except Exception as e:
        print(f"Erro ao extrair vídeos da playlist: {e}")
    return video_urls

def download_youtube_content(url, format_choice, idx=None, total=None):
    # Opções para obter informações do vídeo
    info_opts = {
        'quiet': True,
        'nocache': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Desconhecido')
    except Exception:
        title = 'Desconhecido'

    if format_choice == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'nocache': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'EmbedThumbnail',  # Embute a capa no MP3
                },
                {
                    'key': 'FFmpegMetadata',  # Mantém os metadados
                }
            ],
        }
        ext = 'mp3'
    elif format_choice == 'mp4':
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'quiet': True,
            'nocache': True,
            'merge_output_format': 'mp4',
        }
        ext = 'mp4'
    if FFMPEG_PATH:
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH

    print(f"({idx}/{total}) Baixando: {title}.{ext} [{ext.upper()}]")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"({idx}/{total}) Download concluído: {title}.{ext}")
    except Exception as e:
        print(f"Erro ao baixar: {url} - {e}")

if __name__ == "__main__":
    try:
        create_download_dir()
        if not check_ffmpeg():
            raise RuntimeError("FFmpeg não encontrado. Instale e configure corretamente.")
        while True:
            print("Insira os links do YouTube (um por linha). Digite uma linha vazia para finalizar:")
            links = []
            while True:
                link = input()
                if not link.strip():
                    break
                links.append(link.strip())
            if not links:
                print("Nenhum link informado.")
                continue
            # Remove duplicados
            links = list(dict.fromkeys(links))
            format_choice = input("Baixar como [1] MP3 ou [2] MP4? ").strip()
            if format_choice not in ['1', '2']:
                print("Opção inválida.")
                continue
            format_choice = 'mp3' if format_choice == '1' else 'mp4'
            # Expande playlists para vídeos individuais
            all_video_links = []
            for link in links:
                try:
                    type_, uri = parse_youtube_link(link)
                    if type_ == 'playlist':
                        print(f"Extraindo vídeos da playlist: {uri}")
                        videos = get_playlist_videos(uri)
                        if videos:
                            all_video_links.extend(videos)
                        else:
                            print(f"Nenhum vídeo encontrado na playlist: {uri}")
                    else:
                        all_video_links.append(uri)
                except Exception as e:
                    print(f"Link ignorado: {link} - {e}")
            # Remove duplicados finais
            all_video_links = list(dict.fromkeys(all_video_links))
            total = len(all_video_links)
            if total == 0:
                print("Nenhum vídeo válido para download.")
                continue
            print(f"Iniciando downloads simultâneos ({min(20, total)} por vez)...")
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                for idx, url in enumerate(all_video_links, 1):
                    futures.append(executor.submit(download_youtube_content, url, format_choice, idx, total))
                for future in as_completed(futures):
                    pass
            print("Todos os downloads finalizados!")
            # Menu ao final
            print("\nO que deseja fazer agora?")
            print("[1] Fazer mais downloads")
            print("[2] Sair")
            escolha = input("Escolha uma opção: ").strip()
            if escolha == '2':
                print("Saindo...")
                break
    except Exception as e:
        print(f"Erro: {e}")