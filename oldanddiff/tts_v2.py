import nltk
from TTS.api import TTS
from pydub import AudioSegment
import os
from docx import Document
from transformers import AutoTokenizer

# NLTK'nin yerel veri dizinini ayarla
nltk.data.path.append('C:/Users/Ezat Kosif/Desktop/TextToSpech/nltk_data/')

# Veriyi kontrol et ve doğrula
try:
    nltk.data.find('tokenizers/punkt')
    print("punkt data found")
except LookupError:
    print("punkt data not found. Please ensure it's correctly downloaded.")
    nltk.download('punkt')

# Modeli yükle
model_path = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_path)

# Modeli GPU'ya gönder
tts.to('cuda')
tokenizer = AutoTokenizer.from_pretrained("gpt2")

# Progress dosyasının adı
progress_file = "progress.txt"

def load_progress():
    """Progress dosyasından mevcut ilerlemeyi yükle"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = f.read().strip().split(',')
        return set(progress)
    return set()

def save_progress(completed_chunks):
    """Progress dosyasına ilerlemeyi kaydet"""
    with open(progress_file, 'w') as f:
        f.write(','.join(completed_chunks))

def split_text_by_sentences(text, max_chars=200, max_tokens=300):
    # Metni cümlelere ayır
    try:
        nltk.data.find('tokenizers/punkt')
        sentences = nltk.sent_tokenize(text, language='turkish')
    except LookupError:
        print("NLTK veri dosyası bulunamadı. Lütfen 'punkt' veri dosyasını indirin.")
        return []
    
    chunks = []
    current_chunk = ""
    current_token_count = 0
    
    for sentence in sentences:
        sentence_tokens = tokenizer.tokenize(sentence)
        token_count = len(sentence_tokens)
        
        # Karakter ve token limitini kontrol et
        if (len(current_chunk) + len(sentence) <= max_chars and 
            current_token_count + token_count <= max_tokens):
            current_chunk += sentence + " "
            current_token_count += token_count
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
            current_token_count = token_count
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def generate_speech(text_chunks, output_dir, completed_chunks):
    file_paths = []
    for idx, chunk in enumerate(text_chunks):
        # Eğer chunk zaten tamamlandıysa atla
        if str(idx) in completed_chunks:
            continue

        file_path = os.path.join(output_dir, f"output_{idx}.wav")
        try:
            tts.tts_to_file(
                text=chunk,
                file_path=file_path,
                speaker_wav=["C:/Users/Ezat Kosif/Desktop/TextToSpech/speaker.wav"],
                language="tr",
                split_sentences=True
            )
            # Konsola hangi dosyanın hangi chunk ile eşleştiğini yazdır
            print(f"Kaydedilen dosya: {file_path}, Cümle: {chunk}")
            
            file_paths.append(file_path)
            # Başarıyla tamamlanan chunkları kaydet
            completed_chunks.add(str(idx))
            save_progress(completed_chunks)
        except Exception as e:
            print(f"Ses dosyası oluşturulurken hata oluştu: {e}")
            break
    
    return file_paths

def merge_audio_files(file_paths, output_file):
    if not file_paths:
        print("Ses dosyası bulunamadı.")
        return

    try:
        combined = AudioSegment.from_wav(file_paths[0])
    except Exception as e:
        print(f"İlk dosya yüklenirken hata oluştu: {e}")
        return
    
    for file_path in file_paths[1:]:
        try:
            audio_segment = AudioSegment.from_wav(file_path)
            combined += audio_segment
        except Exception as e:
            print(f"Dosya eklenirken hata oluştu: {file_path}, hata: {e}")
    
    combined.export(output_file, format="wav")

def read_text_from_docx(file_path):
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return '\n'.join(text)

# Word dosyasından metni oku
docx_file_path = "Introduction and Overview.docx"
text = read_text_from_docx(docx_file_path)

# Geçici dosya dizini
output_dir = "temp_audio"
os.makedirs(output_dir, exist_ok=True)

# Metni cümlelere göre böl
text_chunks = split_text_by_sentences(text)

# Kaldığınız ilerlemeyi yükleyin
completed_chunks = load_progress()

# Ses dosyalarını oluştur
file_paths = generate_speech(text_chunks, output_dir, completed_chunks)

# Ses dosyalarını birleştir
merge_audio_files(file_paths, "Introduction_and_Overview.wav")

# Geçici dosyaları temizle
for file_path in file_paths:
    os.remove(file_path)

# Son olarak progress dosyasını temizle
os.remove(progress_file)
os.rmdir(output_dir)
