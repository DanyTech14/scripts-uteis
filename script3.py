import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from tqdm import tqdm
from pathlib import Path

# Configurações
CONCURRENCY = 60  # número máximo de downloads simultâneos
RETRIES = 3       # número de tentativas por vídeo


def get_download_folder():
    """
    Detecta automaticamente a pasta 'Downloads' do sistema.
    """
    home = Path.home()
    downloads = home / "Downloads"
    downloads.mkdir(exist_ok=True)
    return downloads


def fetch_playlist_entries(playlist_url):
    """
    Obtém os vídeos da playlist (sem baixar ainda).
    """
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
    if not info:
        return []
    return info.get('entries', [info])


def build_video_url(entry):
    """
    Extrai URL utilizável do item da playlist.
    """
    for key in ('webpage_url', 'url', 'id'):
        if key in entry and entry[key]:
            val = entry[key]
            if key == 'id':
                return f"https://www.youtube.com/watch?v={val}"
            return val
    return None


def download_video(video_url, outdir, index, total):
    """
    Faz o download de um único vídeo com áudio e vídeo combinados (via ffmpeg).
    """
    outtmpl = os.path.join(outdir, f"{index:03d} - %(title).100s.%(ext)s")

    ydl_opts = {
        # Garante o melhor vídeo + melhor áudio e faz merge automático
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',   # saída final com áudio + vídeo juntos
        'outtmpl': outtmpl,
        'quiet': True,
        'noplaylist': True,
        'continuedl': True,
        'no_warnings': True,
        'retries': RETRIES,
        # parâmetros de pós-processamento (ffmpeg faz o merge)
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return {'status': 'ok', 'url': video_url}
    except Exception as e:
        return {'status': 'error', 'url': video_url, 'error': str(e)}


def main():
    print("=== Downloader de Playlist Autorizada ===")
    print("⚠️  Usa este script apenas para vídeos teus ou livres de direitos.\n")

    # Solicitar link ao usuário
    playlist_url = input("➡️  Insere o link da playlist: ").strip()
    if not playlist_url:
        print("Erro: Nenhum link fornecido.")
        sys.exit(1)

    # Detectar pasta de downloads
    outdir = get_download_folder()
    print(f"\n📁 Os vídeos serão guardados em: {outdir}\n")

    # Obter entradas
    print("🔍 A verificar a playlist...")
    entries = fetch_playlist_entries(playlist_url)
    if not entries:
        print("❌ Não foi possível extrair a playlist. Confirma a URL.")
        sys.exit(1)

    total = len(entries)
    print(f"✅ Playlist com {total} vídeos encontrada.\n")

    # Baixar vídeos em paralelo
    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = []
        for i, entry in enumerate(entries, 1):
            video_url = build_video_url(entry)
            if not video_url:
                continue
            futures.append(executor.submit(
                download_video, video_url, str(outdir), i, total))

        for f in tqdm(as_completed(futures), total=len(futures), desc="⬇️  A descarregar"):
            results.append(f.result())

    elapsed = time.time() - start_time
    ok = sum(1 for r in results if r.get('status') == 'ok')
    err = sum(1 for r in results if r.get('status') != 'ok')

    print(
        f"\n✅ Concluído em {elapsed:.1f}s — {ok} vídeos baixados / {err} falhas.\n")
    if err:
        print("❗ Erros detectados:")
        for r in results:
            if r['status'] == 'error':
                print("-", r['url'], "→", r['error'])


if __name__ == "__main__":
    main()
