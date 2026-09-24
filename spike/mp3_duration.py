"""Throwaway: estimate MP3 duration by summing frame durations (stdlib only)."""
import sys

BITRATES_V1_L3 = [0,32,40,48,56,64,80,96,112,128,160,192,224,256,320,0]  # kbps
BITRATES_V2_L3 = [0,8,16,24,32,40,48,56,64,80,96,112,128,144,160,0]
SR_V1 = [44100,48000,32000,0]
SR_V2 = [22050,24000,16000,0]
SR_V25 = [11025,12000,8000,0]


def duration_seconds(path):
    data = open(path, "rb").read()
    i = 0
    n = len(data)
    # skip ID3v2 tag if present
    if data[:3] == b"ID3":
        size = ((data[6] & 0x7f) << 21) | ((data[7] & 0x7f) << 14) | ((data[8] & 0x7f) << 7) | (data[9] & 0x7f)
        i = 10 + size
    total = 0.0
    frames = 0
    while i + 4 <= n:
        if data[i] != 0xFF or (data[i+1] & 0xE0) != 0xE0:
            i += 1
            continue
        b1, b2 = data[i+1], data[i+2]
        version_id = (b1 >> 3) & 0x03  # 3=MPEG1,2=MPEG2,0=MPEG2.5
        layer = (b1 >> 1) & 0x03       # 1=Layer III
        bitrate_idx = (b2 >> 4) & 0x0F
        sr_idx = (b2 >> 2) & 0x03
        padding = (b2 >> 1) & 0x01
        if layer != 1 or bitrate_idx in (0, 15) or sr_idx == 3:
            i += 1
            continue
        if version_id == 3:
            bitrate = BITRATES_V1_L3[bitrate_idx] * 1000
            sr = SR_V1[sr_idx]
            samples = 1152
        elif version_id == 2:
            bitrate = BITRATES_V2_L3[bitrate_idx] * 1000
            sr = SR_V2[sr_idx]
            samples = 576
        elif version_id == 0:
            bitrate = BITRATES_V2_L3[bitrate_idx] * 1000
            sr = SR_V25[sr_idx]
            samples = 576
        else:
            i += 1
            continue
        if sr == 0 or bitrate == 0:
            i += 1
            continue
        frame_len = int((samples // 8 * bitrate) / sr) + padding
        if frame_len <= 0:
            i += 1
            continue
        total += samples / sr
        frames += 1
        i += frame_len
    return total, frames


if __name__ == "__main__":
    secs, frames = duration_seconds(sys.argv[1])
    print(f"duration_seconds={secs:.2f} frames={frames}")
