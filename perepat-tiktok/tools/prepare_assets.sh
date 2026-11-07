#!/usr/bin/env bash
# Rebuild the (git-ignored) media from the raw iPhone clip.
# Usage: tools/prepare_assets.sh /path/to/source.mov
set -euo pipefail
SRC="$1"; cd "$(dirname "$0")/.."
# portrait 1080x1920 @30fps, keyframe every second (seek-safe), cleaned + loudness-normalised voice (-15 LUFS)
ffmpeg -y -i "$SRC" -map 0:v:0 -map 0:a:0 -vf "scale=1080:1920,fps=30" -c:v libx264 -preset veryfast -crf 20 -g 30 \
  -pix_fmt yuv420p -af "highpass=f=80,acompressor=threshold=-24dB:ratio=3:attack=10:release=150:makeup=4,loudnorm=I=-15:TP=-1.5:LRA=9" \
  -ar 48000 -c:a aac -b:a 192k -movflags +faststart assets/tour.mp4
ffmpeg -y -i assets/tour.mp4 -vn -c:a copy assets/voice.m4a
