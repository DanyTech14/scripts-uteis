import instaloader
import concurrent.futures
import os
from urllib.parse import urlparse

# Função para baixar um único vídeo


def download_video(url, output_dir="downloads"):
    try:
        L = instaloader.Instaloader(
            download_pictures=False, download_videos=True, download_comments=False, save_metadata=False)
        shortcode = urlparse(url).path.split('/')[2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        filename = f"{output_dir}/{shortcode}.mp4"
        L.download_post(post, target=output_dir)
        for file in os.listdir(output_dir):
            if file.startswith(shortcode) and file.endswith('.mp4'):
                os.rename(os.path.join(output_dir, file), filename)
        print(f"Vídeo baixado: {filename}")
        return filename
    except Exception as e:
        print(f"Erro ao baixar {url}: {str(e)}")
        return None

# Função para baixar vídeos em paralelo


def download_videos_concurrently(video_urls):
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(download_video, url) for url in video_urls]
        results = [f.result()
                   for f in concurrent.futures.as_completed(futures)]
    return results

# Função principal


def main():
    print("=== Downloader de Reels do Instagram ===")
    print("Digite as URLs dos reels (ex.: https://www.instagram.com/reel/DKnwjT5M5YZ/?utm_source=ig_web_copy_link).")
    print("Pressione Enter duas vezes para finalizar:")

    video_urls = []
    while True:
        url = input()
        if url == "":
            break
        if url.startswith("https://www.instagram.com/reel/") and url.endswith("?utm_source=ig_web_copy_link"):
            video_urls.append(url)
        else:
            print("URL inválida. Deve ser no formato 'https://www.instagram.com/reel/SHORTCODE/?utm_source=ig_web_copy_link'.")

    if not video_urls:
        print("Nenhuma URL válida fornecida. Encerrando.")
        return

    print("\nIniciando downloads (máximo 4 simultâneos)...")
    downloaded_files = download_videos_concurrently(video_urls)
    print("\nDownloads concluídos!")
    for file in downloaded_files:
        if file:
            print(f"Sucesso: {file}")
        else:
            print("Falha em um ou mais downloads. Verifique os erros acima.")


if __name__ == "__main__":
    main()
