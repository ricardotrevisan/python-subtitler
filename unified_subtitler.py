from __future__ import annotations

import sys
import argparse
from pathlib import Path


def _import_whisper():
    try:
        import whisper  # type: ignore
    except Exception as e:
        print("Erro: a biblioteca 'whisper' não está instalada ou falhou ao carregar.")
        print("Instale com: pip install openai-whisper")
        raise
    return whisper


def _import_ffmpeg():
    try:
        import ffmpeg  # type: ignore
    except Exception as e:
        print("Erro: a biblioteca 'ffmpeg-python' não está instalada.")
        print("Instale com: pip install ffmpeg-python")
        raise
    return ffmpeg


def extract_audio(video_path: Path, audio_path: Path, overwrite: bool, ac: int = 1, ar: int = 16000) -> None:
    ffmpeg = _import_ffmpeg()
    (
        ffmpeg
        .input(str(video_path))
        .output(str(audio_path), ac=ac, ar=ar)
        .run(overwrite_output=overwrite)
    )


def transcribe_audio_to_srt(
    audio_path: Path,
    srt_path: Path,
    model_name: str = "medium",
    language: str = "pt",
    verbose: bool = True,
    translate: bool = False,
) -> None:
    whisper = _import_whisper()

    print(f"Carregando modelo Whisper: {model_name}…")
    model = whisper.load_model(model_name)

    task = "translate" if translate else "transcribe"
    print(f"Transcrevendo áudio: {audio_path}")
    result = model.transcribe(str(audio_path), verbose=verbose, language=language, task=task)

    print(f"Gravando SRT em: {srt_path}")
    with srt_path.open("w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], start=1):
            start = segment["start"]
            end = segment["end"]
            text = segment["text"].strip()

            def format_time(t: float) -> str:
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t * 1000) % 1000)
                return f"{h:02}:{m:02}:{s:02},{ms:03}"

            f.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")


def transcribe_from_video(
    video_path: Path,
    srt_path: Path | None,
    *,
    model_name: str = "medium",
    language: str = "pt",
    overwrite: bool = False,
    ac: int = 1,
    ar: int = 16000,
    audio_out: Path | None = None,
    keep_audio: bool = False,
    translate: bool = False,
) -> Path:
    if srt_path is None:
        srt_path = video_path.with_suffix(".srt")
    if audio_out is None:
        audio_out = video_path.with_suffix(".mp3")

    print(f"Extraindo áudio → {audio_out}")
    extract_audio(video_path, audio_out, overwrite=overwrite, ac=ac, ar=ar)

    transcribe_audio_to_srt(audio_out, srt_path, model_name=model_name, language=language, translate=translate)

    if not keep_audio and audio_out.exists():
        try:
            audio_out.unlink()
        except Exception:
            # Não falhar se não conseguir remover
            pass

    return srt_path


def burn_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path | None,
    *,
    overwrite: bool = False,
) -> Path:
    if output_path is None:
        output_path = video_path.with_name(f"{video_path.stem}_pt{video_path.suffix}")

    if not srt_path.exists():
        raise FileNotFoundError(f"Arquivo SRT não encontrado: {srt_path}")

    ffmpeg = _import_ffmpeg()
    print(f"Embutindo legendas '{srt_path.name}' em '{video_path.name}' → '{output_path.name}'")
    (
        ffmpeg
        .input(str(video_path))
        .output(str(output_path), vf=f"subtitles={str(srt_path)}")
        .run(overwrite_output=overwrite)
    )
    return output_path


def run_cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Unifica geração de legendas (Whisper) e embutir SRT (ffmpeg).",
    )
    parser.add_argument("video", type=Path, help="Caminho do arquivo de vídeo")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescrever arquivos de saída existentes")

    subparsers = parser.add_subparsers(dest="cmd", required=True)

    # srt: apenas gerar a legenda
    p_srt = subparsers.add_parser("srt", help="Gerar SRT a partir do vídeo")
    p_srt.add_argument("--srt-out", type=Path, default=None, help="Caminho do .srt de saída (padrão: <video>.srt)")
    p_srt.add_argument("--audio-out", type=Path, default=None, help="Caminho do áudio extraído (padrão: <video>.mp3)")
    p_srt.add_argument("--model", default="medium", help="Modelo Whisper (ex.: tiny, base, small, medium, large)")
    p_srt.add_argument("--language", default="pt", help="Idioma para transcrição (ex.: pt, en)")
    p_srt.add_argument("--ar", type=int, default=16000, help="Sample rate do áudio (Hz)")
    p_srt.add_argument("--ac", type=int, default=1, help="Canais de áudio (1=mono, 2=stereo)")
    p_srt.add_argument("--keep-audio", action="store_true", help="Manter arquivo de áudio extraído")
    p_srt.add_argument("--translate", action="store_true", help="Traduzir para inglês (Whisper task=translate)")

    # burn: apenas embutir uma legenda existente
    p_burn = subparsers.add_parser("burn", help="Embutir SRT em um vídeo")
    p_burn.add_argument("--srt", type=Path, default=None, help="Caminho do .srt (padrão: <video>.srt)")
    p_burn.add_argument("--out", type=Path, default=None, help="Vídeo de saída (padrão: <video>_pt<ext>)")

    # both: pipeline gerar srt e embutir
    p_both = subparsers.add_parser("both", help="Gerar SRT e embutir no vídeo")
    p_both.add_argument("--srt-out", type=Path, default=None, help="Caminho do .srt de saída (padrão: <video>.srt)")
    p_both.add_argument("--out", type=Path, default=None, help="Vídeo de saída (padrão: <video>_pt<ext>)")
    p_both.add_argument("--model", default="medium", help="Modelo Whisper (ex.: tiny, base, small, medium, large)")
    p_both.add_argument("--language", default="pt", help="Idioma para transcrição (ex.: pt, en)")
    p_both.add_argument("--ar", type=int, default=16000, help="Sample rate do áudio (Hz)")
    p_both.add_argument("--ac", type=int, default=1, help="Canais de áudio (1=mono, 2=stereo)")
    p_both.add_argument("--keep-audio", action="store_true", help="Manter arquivo de áudio extraído")
    p_both.add_argument("--translate", action="store_true", help="Traduzir para inglês (Whisper task=translate)")

    args = parser.parse_args(argv)

    video_path: Path = args.video
    if not video_path.exists():
        print(f"Erro: vídeo não encontrado: {video_path}")
        return 2

    overwrite: bool = bool(getattr(args, "overwrite", False))

    if args.cmd == "srt":
        srt = transcribe_from_video(
            video_path,
            args.srt_out,
            model_name=args.model,
            language=args.language,
            overwrite=overwrite,
            ac=args.ac,
            ar=args.ar,
            audio_out=args.audio_out,
            keep_audio=args.keep_audio,
            translate=args.translate,
        )
        print(f"✅ Legenda gerada: {srt}")
        return 0

    if args.cmd == "burn":
        srt_path = args.srt or video_path.with_suffix(".srt")
        out_path = burn_subtitles(video_path, srt_path, args.out, overwrite=overwrite)
        print(f"✅ Vídeo gerado: {out_path}")
        return 0

    if args.cmd == "both":
        srt = transcribe_from_video(
            video_path,
            args.srt_out,
            model_name=args.model,
            language=args.language,
            overwrite=overwrite,
            ac=args.ac,
            ar=args.ar,
            keep_audio=args.keep_audio,
            translate=args.translate,
        )
        out_path = burn_subtitles(video_path, srt, args.out, overwrite=overwrite)
        print(f"✅ Vídeo com legenda embutida: {out_path}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(run_cli(sys.argv[1:]))

