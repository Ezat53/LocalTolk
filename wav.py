from pydub import AudioSegment
import os

# Ses dosyalarının bulunduğu klasör
folder_path = r'C:\Users\Ezat Kosif\Desktop\TextToSpech\temp_audio'

# Tüm .wav dosyalarını al
audio_files = [f for f in os.listdir(folder_path) if f.endswith('.wav')]
audio_files.sort()  # Dosyaları sıralı hale getirmek için

# Boş bir AudioSegment oluştur
combined = AudioSegment.empty()

# Her bir ses dosyasını sırayla birleştir
for audio_file in audio_files:
    file_path = os.path.join(folder_path, audio_file)
    audio = AudioSegment.from_wav(file_path)
    combined += audio  # Ses dosyasını ekle

# Çıktı dosyasını kaydet
output_path = os.path.join(folder_path, 'End.wav')
combined.export(output_path, format='wav')

print(f"Ses dosyaları birleştirildi ve {output_path} olarak kaydedildi.")