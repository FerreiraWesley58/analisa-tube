import os
import sys
import json
import time
from flask import Flask, request, jsonify
import pytubefix
import ffmpeg
import openai
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar a API do OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inicializar a aplicação Flask
app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "URL do vídeo não fornecida"}), 400
        
        # Obter informações do vídeo
        video_info = get_video_info(url)
        
        # Extrair e transcrever o áudio
        audio_file = extract_audio(url)
        
        # Transcrever o áudio
        transcript = transcribe_audio(audio_file)
        
        # Gerar resumo
        summary = generate_summary(transcript, video_info)
        
        # Limpar arquivos temporários
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        return jsonify({
            "video_info": video_info,
            "summary": summary
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_video_info(url):
    """Extrai informações do vídeo do YouTube."""
    try:
        yt = pytubefix.YouTube(url)
        
        # Formatação da contagem de visualizações
        views = yt.views
        if views >= 1000000:
            views_str = f"{views/1000000:.1f}M"
        elif views >= 1000:
            views_str = f"{views/1000:.1f}K"
        else:
            views_str = str(views)
            
        # Formatação da duração
        seconds = yt.length
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            duration = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            duration = f"{minutes}:{seconds:02d}"
        
        return {
            "id": yt.video_id,
            "title": yt.title,
            "channel": yt.author,
            "views": views_str,
            "likes": "N/A",  # PyTube não fornece contagem de likes diretamente
            "comments": "N/A",  # PyTube não fornece contagem de comentários diretamente
            "publishDate": yt.publish_date.strftime("%d de %B de %Y") if yt.publish_date else "N/A",
            "duration": duration,
            "thumbnail": yt.thumbnail_url
        }
    except Exception as e:
        print(f"Erro ao obter informações do vídeo: {e}")
        raise Exception(f"Não foi possível obter informações do vídeo: {str(e)}")

def extract_audio(url):
    """Extrai o áudio do vídeo do YouTube."""
    try:
        print("Extraindo áudio do vídeo...")
        filename = f"audio_{int(time.time())}.wav"
        yt = pytubefix.YouTube(url)
        
        # Obter o stream de áudio
        audio_stream = yt.streams.filter(only_audio=True).first()
        
        if not audio_stream:
            raise Exception("Não foi possível encontrar uma stream de áudio para este vídeo")
# Baixar o arquivo de áudio
        temp_file = audio_stream.download(filename=f"temp_{yt.video_id}")
        
        # Converter para WAV usando ffmpeg
        try:
            ffmpeg.input(temp_file).output(
                filename,
                format='wav',
                acodec='pcm_s16le',
                ac=1,
                ar='16k',
                loglevel='error'
            ).run(overwrite_output=True)
            
            # Remover o arquivo temporário
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return filename
        except ffmpeg.Error as e:
            print(f"Erro no FFmpeg: {e.stderr.decode() if e.stderr else 'Erro desconhecido'}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise Exception("Erro ao processar o áudio do vídeo")
            
    except Exception as e:
        print(f"Erro ao extrair áudio: {e}")
        raise Exception(f"Não foi possível extrair o áudio: {str(e)}")

def transcribe_audio(audio_file):
    """Transcreve o áudio usando o modelo Whisper da OpenAI."""
    try:
        print("Transcrevendo áudio...")
        with open(audio_file, "rb") as file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=file
            ).text
        return transcript
    except Exception as e:
        print(f"Erro ao transcrever áudio: {e}")
        raise Exception(f"Falha na transcrição: {str(e)}")

def generate_summary(transcript, video_info):
    """Gera um resumo do vídeo usando a API GPT."""
    try:
        print("Gerando resumo...")
        system_prompt = """
        Você é um assistente especializado em resumir vídeos. 
        Crie um resumo detalhado, organizado e informativo usando formatação Markdown.
        
        Inclua:
        1. Um título principal com o nome do vídeo
        2. Uma introdução que descreva o tema geral
        3. Seções e subseções organizadas por tópicos principais
        4. Pontos-chave, informações importantes e dados mencionados
        5. Uma conclusão que sintetize as ideias principais
        
        Use formatação Markdown com:
        - Títulos e subtítulos (#, ##, ###)
        - Listas com marcadores (-)
        - Texto em negrito para enfatizar pontos importantes
        - Parágrafos separados para melhor legibilidade
        
        O resumo deve ser conciso mas completo, capturando a essência do conteúdo em formato fácil de ler.
        """
        
        user_prompt = f"""
        Título do vídeo: {video_info['title']}
        Canal: {video_info['channel']}
        
        Transcrição do vídeo:
        {transcript}
        
        Baseado nesta transcrição, crie um resumo detalhado do vídeo em formato Markdown.
        """
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Ou outro modelo apropriado
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        summary = completion.choices[0].message.content
        return summary
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        raise Exception(f"Falha ao gerar o resumo: {str(e)}")

@app.route('/api/video-info', methods=['POST'])
def get_video_metadata():
    """Endpoint para obter apenas as informações do vídeo sem processá-lo."""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({"error": "URL do vídeo não fornecida"}), 400
        
        video_info = get_video_info(url)
        return jsonify({"video_info": video_info})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Função para verificar status do processamento (simulado)
@app.route('/api/status/<job_id>', methods=['GET'])
def check_status(job_id):
    # Em uma implementação real, isso verificaria o status de um job em andamento
    # Para o exemplo, usamos uma simulação simples
    statuses = {
        "pending": "Aguardando processamento",
        "extracting": "Extraindo áudio do vídeo",
        "transcribing": "Transcrevendo o conteúdo",
        "analyzing": "Analisando e gerando resumo",
        "completed": "Análise concluída"
    }
    
    # Simular progresso com base no job_id
    job_id_num = int(job_id) % 100
    
    if job_id_num < 20:
        current_status = "extracting"
        progress = job_id_num * 5
    elif job_id_num < 50:
        current_status = "transcribing"
        progress = job_id_num * 2
    elif job_id_num < 80:
        current_status = "analyzing"
        progress = job_id_num + 20
    else:
        current_status = "completed"
        progress = 100
        
    return jsonify({
        "job_id": job_id,
        "status": current_status,
        "message": statuses[current_status],
        "progress": progress
    })

# Endpoint para salvar o resumo como arquivo markdown
@app.route('/api/save-summary', methods=['POST'])
def save_summary():
    try:
        data = request.json
        summary = data.get('summary')
        video_id = data.get('video_id')
        
        if not summary or not video_id:
            return jsonify({"error": "Resumo ou ID do vídeo não fornecido"}), 400
        
        # Criar pasta para resumos se não existir
        os.makedirs("resumos", exist_ok=True)
        
        # Salvar o arquivo
        filename = f"resumos/resumo_{video_id}.md"
        with open(filename, "w", encoding="utf-8") as file:
            file.write(summary)
            
        return jsonify({
            "success": True,
            "filename": filename
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Verificar se a API key foi configurada
    if not os.getenv("OPENAI_API_KEY"):
        print("ERRO: A chave de API do OpenAI não foi configurada.")
        print("Por favor, crie um arquivo .env com OPENAI_API_KEY=sua_chave_api")
        sys.exit(1)
        
    # Iniciar o servidor Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)        