# Metin Okuma ve Ses Üretim Uygulaması

Bu Python uygulaması, Word belgelerinden metin okuyarak, bu metni ses dosyalarına dönüştürür ve ardından bu ses dosyalarını birleştirir. Bu süreçte Cogui `TTS` (Text-to-Speech) kütüphanesi ve `pydub` kütüphanesi kullanılır. Projenin temel amacı ücretli seslendirme uygulamalarına ek bir açık kaynak alternatifi sunmaktır.

## Gereksinimler

- Python 3.11.9
- `nltk`
- `TTS`
- `pydub`
- `python-docx`
- `transformers`
- `torch` (CUDA destekli GPU için)

## Kurulum

Gerekli Python paketlerini yüklemek için:

```bash
pip install nltk TTS pydub python-docx transformers torch
```

## Kullanım

Program, NLTK'nin punkt veri dosyasını kullanır. Bu dosya mevcut değilse, program bu dosyayı indirir:

```python
import nltk

nltk.data.path.append('C:/Users/Ezat Kosif/Desktop/TextToSpech/nltk_data/')

try:
    nltk.data.find('tokenizers/punkt')
    print("punkt data found")
except LookupError:
    print("punkt data not found. Please ensure it's correctly downloaded.")
    nltk.download('punkt')
```

Text-to-Speech modelini yükler ve GPU'ya taşır:

```python
from TTS.api import TTS

model_path = "tts_models/multilingual/multi-dataset/xtts_v2"
tts = TTS(model_path)
tts.to('cuda')
```

Metin, cümlelere bölünür ve karakter ile token limitlerine göre parçalanır:

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("gpt2")

def split_text_by_sentences(text, max_chars=226, max_tokens=390):
    try:
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
```

Her bir metin parçası için ses dosyaları oluşturulur ve ilerleme kaydedilir:

```python
from pydub import AudioSegment
import os

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
```

Oluşturulan ses dosyalarını birleştirir:

```python
def merge_audio_files(output_dir, output_file):
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
```

Word belgelerinden metinleri okur:

```python
from docx import Document

def read_text_from_docx(file_path):
    doc = Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return '\n'.join(text)
```

İşlenecek Word dosyalarını listeleyin ve kodu çalıştırın:

```python
docx_files = ["Managing Storeroom Inventory.docx", "Maximo 7.6 New Features.docx", "Multi-Organization and Site Setup.docx", "Workforce Management.docx"]

for docx_file_path in docx_files:
    base_name = os.path.splitext(os.path.basename(docx_file_path))[0]
    output_dir = f"temp_audio_{base_name}"
    progress_file = f"progress_{base_name}.txt"

    os.makedirs(output_dir, exist_ok=True)

    text = read_text_from_docx(docx_file_path)
    text_chunks = split_text_by_sentences(text)
    completed_chunks = load_progress(progress_file)
    file_paths = generate_speech(text_chunks, output_dir, completed_chunks, progress_file)
    merge_audio_files(output_dir, f"{base_name}.wav")

    for file_path in os.listdir(output_dir):
        os.remove(os.path.join(output_dir, file_path))

    os.rmdir(output_dir)
    
    if os.path.exists(progress_file):
        os.remove(progress_file)
```

## Dosya Yapısı

- `tts_models/`: Text-to-Speech modellerinin bulunduğu dizin.
- `temp_audio_<base_name>/`: Geçici ses dosyalarının depolandığı dizin.
- `progress_<base_name>.txt`: İlerleme dosyası.

## Sorun Giderme

- Eğer NLTK veri dosyaları ile ilgili bir hata alırsanız, punkt veri dosyasının yüklendiğinden emin olun.
- Ses dosyalarını birleştirirken hata alırsanız, ses dosyalarının geçerli formatta olduğundan emin olun.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için LICENSE dosyasına bakabilirsiniz.
