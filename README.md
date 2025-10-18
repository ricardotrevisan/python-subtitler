# Python Subtitler

Script unificado para:
- Gerar legendas `.srt` a partir de um vídeo usando Whisper
- Embutir um arquivo `.srt` em um vídeo usando ffmpeg
- Rodar o pipeline completo (gerar + embutir) em um único comando

## Requisitos
- Python 3.9+
- ffmpeg instalado no sistema (binário disponível no PATH)
- Pacotes Python: `ffmpeg-python`, `openai-whisper`

Instalação dos pacotes:

```
pip install ffmpeg-python openai-whisper
```

## Uso

O script principal é `unified_subtitler.py` e possui três subcomandos: `srt`, `burn`, `both`.

Formato geral:

```
python unified_subtitler.py <vídeo> <subcomando> [opções]
```

### 1) Gerar SRT
Gera o arquivo `.srt` a partir do áudio extraído do vídeo.

```
python unified_subtitler.py input.mkv srt \
  --model medium \
  --language pt \
  --srt-out input.srt \
  --audio-out input.mp3 \
  --ar 16000 --ac 1 \
  --keep-audio \
  --overwrite
```

- `--srt-out`: caminho do SRT (padrão: `<vídeo>.srt`)
- `--audio-out`: caminho do áudio extraído (padrão: `<vídeo>.mp3`)
- `--model`: modelo Whisper (ex.: `tiny`, `base`, `small`, `medium`, `large`)
- `--language`: idioma (ex.: `pt`, `en`)
- `--ar` / `--ac`: sample rate e canais do áudio extraído
- `--keep-audio`: mantém o arquivo de áudio extraído
- `--overwrite`: sobrescreve arquivos de saída

### 2) Embutir SRT
Embutir um arquivo `.srt` existente em um vídeo.

```
python unified_subtitler.py input.mkv burn \
  --srt input.srt \
  --out input_pt.mkv \
  --overwrite
```

- `--srt`: caminho do SRT (padrão: `<vídeo>.srt`)
- `--out`: caminho do vídeo de saída (padrão: `<vídeo>_pt<ext>`, ex.: `input_pt.mkv`)

### 3) Pipeline (gerar + embutir)
Gera o `.srt` e depois embute no vídeo de saída.

```
python unified_subtitler.py input.mkv both \
  --model medium \
  --language pt \
  --srt-out input.srt \
  --out input_pt.mkv \
  --overwrite
```

## Observações
- O Whisper pode baixar modelos na primeira execução; garanta acesso à internet ou já deixe o cache do modelo no ambiente.
- Verifique se o `ffmpeg` do sistema está instalado (`ffmpeg -version`).
