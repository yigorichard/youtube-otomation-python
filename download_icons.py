import os
import requests

def download_and_save_icon(url, filename):
    try:
        response = requests.get(url)
        
        # icons klasörünü oluştur
        if not os.path.exists('icons'):
            os.makedirs('icons')
        
        # PNG olarak kaydet
        with open(f'icons/{filename}.png', 'wb') as f:
            f.write(response.content)
            
        print(f"İkon indirildi: {filename}")
        return True
    except Exception as e:
        print(f"Hata: {filename} indirilemedi - {str(e)}")
        return False

# Material Design Icons'dan doğrudan PNG URL'leri
ICONS = {
    'upload': 'https://fonts.gstatic.com/s/i/materialicons/upload/v1/24px.png',
    'video': 'https://fonts.gstatic.com/s/i/materialicons/videocam/v1/24px.png',
    'user': 'https://fonts.gstatic.com/s/i/materialicons/person/v1/24px.png',
    'settings': 'https://fonts.gstatic.com/s/i/materialicons/settings/v1/24px.png',
    'menu': 'https://fonts.gstatic.com/s/i/materialicons/menu/v1/24px.png',
    'lock': 'https://fonts.gstatic.com/s/i/materialicons/lock/v1/24px.png',
    'check': 'https://fonts.gstatic.com/s/i/materialicons/check/v1/24px.png',
    'search': 'https://fonts.gstatic.com/s/i/materialicons/search/v1/24px.png',
    'youtube': 'https://fonts.gstatic.com/s/i/materialicons/play_circle_filled/v1/24px.png'
}

def main():
    print("İkonlar indiriliyor...")
    success_count = 0
    
    for name, url in ICONS.items():
        if download_and_save_icon(url, name):
            success_count += 1
    
    print(f"\nToplam {success_count}/{len(ICONS)} ikon indirildi.")

if __name__ == "__main__":
    main() 