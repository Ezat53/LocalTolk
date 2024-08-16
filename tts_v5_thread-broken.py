import nltk
from TTS.api import TTS
from pydub import AudioSegment
import os
from docx import Document
from transformers import AutoTokenizer
from concurrent.futures import ThreadPoolExecutor

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

def load_progress(progress_file):
    """Progress dosyasından mevcut ilerlemeyi yükle"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = f.read().strip().split(',')
        return set(progress)
    return set()

def save_progress(completed_chunks, progress_file):
    """Progress dosyasına ilerlemeyi kaydet"""
    with open(progress_file, 'w') as f:
        f.write(','.join(completed_chunks))

def split_text_by_sentences(text, max_chars=226, max_tokens=390):
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

def generate_speech(text_chunks, output_dir, completed_chunks, progress_file):
    file_paths = []
    for idx, chunk in enumerate(text_chunks):
        file_name = f"output_{idx}.wav"
        file_path = os.path.join(output_dir, file_name)
        
        if file_name in completed_chunks:
            continue

        try:
            tts.tts_to_file(
                text=chunk,
                file_path=file_path,
                speaker_wav=["C:/Users/Ezat Kosif/Desktop/TextToSpech/speaker.wav"],
                language="tr",
                split_sentences=True
            )
            print(f"Kaydedilen dosya: {file_path}, Cümle: {chunk}")
            file_paths.append(file_path)
            completed_chunks.add(file_name)
            save_progress(completed_chunks, progress_file)
        except Exception as e:
            print(f"Ses dosyası oluşturulurken hata oluştu: {e}")
            break
    
    return file_paths

def merge_audio_files(output_dir, output_file):
    """Tüm ses dosyalarını birleştirir, hem eski hem de yeni dosyalar"""
    all_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
    file_paths = [os.path.join(output_dir, f) for f in all_files]

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
    
    try:
        combined.export(output_file, format="wav")
        print(f"Ses dosyaları başarıyla {output_file} olarak birleştirildi.")
    except Exception as e:
        print(f"Birleştirilmiş dosya oluşturulurken hata oluştu: {e}")

def read_text_from_docx(file_path):
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return '\n'.join(text)

def process_document(docx_file_path):
    # Her dosya için geçici dosya dizini ve progress dosyası
    base_name = os.path.splitext(os.path.basename(docx_file_path))[0]
    output_dir = f"temp_audio_{base_name}"
    progress_file = f"progress_{base_name}.txt"

    os.makedirs(output_dir, exist_ok=True)

    # Word dosyasından metni oku
    text = read_text_from_docx(docx_file_path)

    # Metni cümlelere göre böl
    text_chunks = split_text_by_sentences(text)

    # Kaldığınız ilerlemeyi yükleyin
    completed_chunks = load_progress(progress_file)

    # Ses dosyalarını oluştur
    file_paths = generate_speech(text_chunks, output_dir, completed_chunks, progress_file)

    # Ses dosyalarını birleştir
    merge_audio_files(output_dir, f"{base_name}.wav")

    # Geçici dosyaları temizle
    for file_path in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file_path))

    os.rmdir(output_dir)
    
    # Son olarak progress dosyasını temizle
    if os.path.exists(progress_file):
        os.remove(progress_file)

# İşlenecek Word dosyalarının listesi
docx_files = ["Introduction and Overview.docx", "Managing Items in Inventory.docx", "Managing Storeroom Inventory.docx"]  # Buraya işlemek istediğiniz dosyaların yollarını ekleyin

# Paralel işleme başlat
with ThreadPoolExecutor() as executor:
    executor.map(process_document, docx_files)
