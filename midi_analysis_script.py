"""
midi_analysis_script.py

用法示例:
  python midi_analysis_script.py /path/to/melancholy_piano.mid /path/to/output_1.mid /path/to/output_2.mid

输出:
  - analysis_summary.csv    : 汇总比较表（每个 MIDI 文件一行）
  - <basename>_notes.csv    : 每个文件的逐音符表（note, start, end, pitch, velocity, instrument, track）
  - <basename>_pianoroll.png : 钢琴卷帘图（每个文件）
  - <basename>_velocity_hist.png : 力度直方图（每个文件）

依赖（推荐安装）:
  pip install pretty_midi mido pandas matplotlib numpy

脚本特点：
  - 首选 pretty_midi 解析（更高层次，提取 note start/end/velocity/program）
  - 若 pretty_midi 不可用，退回到 mido（更底层）解析（但对 note 聚合会更复杂）
  - 计算并比较：时长、轨道/乐器数量、音符数、独特音高数、平均力度、平均音符时长、速度/力度分布、节拍/速度变化
  - 导出 CSV 和图像以便检查差异

注意：如果你使用的是 Windows 并在命令行出现中文乱码，请使用 PowerShell 或在 CMD 中设置 chcp 65001。

"""

import sys
import os
import argparse
from collections import defaultdict
import math

# optional imports
try:
    import pretty_midi
except Exception:
    pretty_midi = None

try:
    import mido
except Exception:
    mido = None

try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
except Exception as e:
    print("缺少依赖：", e)
    print("请安装：pip install pretty_midi mido pandas matplotlib numpy")
    sys.exit(1)


def analyze_with_pretty(path):
    pm = pretty_midi.PrettyMIDI(path)
    instruments = []
    notes_rows = []
    for inst_idx, inst in enumerate(pm.instruments):
        inst_name = inst.name if hasattr(inst, 'name') else f'instr_{inst_idx}'
        for note in inst.notes:
            notes_rows.append({
                'track_or_instrument': inst_idx,
                'instrument_name': inst_name,
                'is_drum': inst.is_drum,
                'pitch': note.pitch,
                'velocity': note.velocity,
                'start': round(note.start, 6),
                'end': round(note.end, 6),
                'duration': round(note.end - note.start, 6),
            })
        instruments.append({'index': inst_idx, 'program': inst.program, 'is_drum': inst.is_drum})

    # tempo map
    try:
        tempo_times, tempi = pm.get_tempo_changes()
    except Exception:
        # fallback
        tempo_times, tempi = [], []

    stats = {
        'instruments_count': len(pm.instruments),
        'tempo_changes_count': len(tempi),
        'avg_tempo': float(np.mean(tempi)) if len(tempi) > 0 else None,
        'total_duration_sec': float(round(pm.get_end_time(), 6)),
    }

    notes_df = pd.DataFrame(notes_rows)
    if not notes_df.empty:
        stats.update({
            'note_count': int(len(notes_df)),
            'unique_pitches': int(notes_df['pitch'].nunique()),
            'avg_velocity': float(round(notes_df['velocity'].mean(), 2)),
            'median_velocity': float(round(notes_df['velocity'].median(), 2)),
            'avg_note_duration': float(round(notes_df['duration'].mean(), 6)),
        })
    else:
        stats.update({
            'note_count': 0,
            'unique_pitches': 0,
            'avg_velocity': 0,
            'median_velocity': 0,
            'avg_note_duration': 0,
        })

    stats['notes_df'] = notes_df
    stats['tempo_times'] = tempo_times
    stats['tempi'] = tempi
    stats['instruments'] = instruments
    return stats


def analyze_with_mido(path):
    # This is a lower-level fallback. We'll approximate note on/off pairing per channel+note.
    mid = mido.MidiFile(path)
    ticks_per_beat = mid.ticks_per_beat

    time = 0.0
    tempo = 500000  # default us per beat
    ticks_to_seconds = lambda t: mido.tick2second(t, ticks_per_beat, tempo)

    # data structures
    ongoing = {}  # (channel, note) -> (start_time, velocity)
    rows = []

    for i, track in enumerate(mid.tracks):
        cur_time = 0
        for msg in track:
            cur_time += msg.time
            if msg.type == 'set_tempo':
                tempo = msg.tempo
            if msg.type == 'note_on' or msg.type == 'note_off':
                # note_on with velocity 0 is note_off
                velocity = getattr(msg, 'velocity', 0)
                note = getattr(msg, 'note', None)
                channel = getattr(msg, 'channel', None) if hasattr(msg, 'channel') else None
                sec_time = mido.tick2second(cur_time, ticks_per_beat, tempo)
                key = (channel, note)
                if msg.type == 'note_on' and velocity > 0:
                    ongoing[key] = (sec_time, velocity, i)
                else:
                    if key in ongoing:
                        start, v, track_idx = ongoing.pop(key)
                        rows.append({
                            'track': track_idx,
                            'channel': channel,
                            'note': note,
                            'velocity': v,
                            'start': round(start, 6),
                            'end': round(sec_time, 6),
                            'duration': round(sec_time - start, 6),
                        })
    notes_df = pd.DataFrame(rows)
    stats = {
        'instruments_count': None,
        'tempo_changes_count': None,
        'avg_tempo': None,
        'total_duration_sec': float(round(mid.length, 6)) if hasattr(mid, 'length') else None,
    }

    if not notes_df.empty:
        stats.update({
            'note_count': int(len(notes_df)),
            'unique_pitches': int(notes_df['note'].nunique()),
            'avg_velocity': float(round(notes_df['velocity'].mean(), 2)),
            'median_velocity': float(round(notes_df['velocity'].median(), 2)),
            'avg_note_duration': float(round(notes_df['duration'].mean(), 6)),
        })
    else:
        stats.update({
            'note_count': 0,
            'unique_pitches': 0,
            'avg_velocity': 0,
            'median_velocity': 0,
            'avg_note_duration': 0,
        })

    stats['notes_df'] = notes_df
    return stats


def make_pianoroll(notes_df, out_png, title=None, fs=100):
    # Simple piano roll: y=pitch, x=time, line segments for each note
    if notes_df is None or notes_df.empty:
        print(f"跳过 pianoroll（{out_png}）——没有音符数据")
        return

    fig, ax = plt.subplots(figsize=(12, 4))
    for _, r in notes_df.iterrows():
        ax.plot([r['start'], r['end']], [r['pitch'], r['pitch']], linewidth=max(1, math.log1p(r.get('velocity', 1)+1)))
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('MIDI pitch')
    if title:
        ax.set_title(title)
    ax.grid(True, linestyle=':', linewidth=0.3)
    plt.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def make_velocity_hist(notes_df, out_png, title=None, bins=32):
    if notes_df is None or notes_df.empty:
        print(f"跳过 velocity hist（{out_png}）——没有音符数据")
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(notes_df['velocity'], bins=bins)
    ax.set_xlabel('Velocity')
    ax.set_ylabel('Count')
    if title:
        ax.set_title(title)
    plt.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def save_notes_csv(notes_df, out_csv):
    if notes_df is None:
        return
    notes_df.to_csv(out_csv, index=False, encoding='utf-8')


def main(paths, outdir='./midi_analysis_output'):
    os.makedirs(outdir, exist_ok=True)

    summaries = []
    for path in paths:
        base = os.path.splitext(os.path.basename(path))[0]
        print(f"分析: {path}")
        if pretty_midi is not None:
            stats = analyze_with_pretty(path)
        elif mido is not None:
            stats = analyze_with_mido(path)
        else:
            raise RuntimeError('没有可用的 MIDI 解析库 (pretty_midi 或 mido)')

        notes_df = stats.pop('notes_df')
        tempo_times = stats.pop('tempo_times', None)
        tempi = stats.pop('tempi', None)

        # 保存逐音符表
        notes_csv = os.path.join(outdir, f'{base}_notes.csv')
        save_notes_csv(notes_df, notes_csv)

        # 画图
        pianoroll_png = os.path.join(outdir, f'{base}_pianoroll.png')
        vel_png = os.path.join(outdir, f'{base}_velocity_hist.png')
        make_pianoroll(notes_df, pianoroll_png, title=f'Piano roll: {base}')
        make_velocity_hist(notes_df, vel_png, title=f'Velocity histogram: {base}')

        # 生成简明统计
        summary = {
            'file': os.path.basename(path),
            'base': base,
            'notes_csv': notes_csv,
            'pianoroll': pianoroll_png,
            'velocity_hist': vel_png,
        }
        summary.update(stats)
        summaries.append(summary)

    # 保存汇总
    summary_df = pd.DataFrame(summaries)
    summary_csv = os.path.join(outdir, 'analysis_summary.csv')
    summary_df.to_csv(summary_csv, index=False, encoding='utf-8')
    print('\n分析完成。输出文件夹：', os.path.abspath(outdir))
    print('汇总文件：', summary_csv)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='比较多个 MIDI 文件并生成统计/图像输出')
    parser.add_argument('midi_files', nargs='+', help='要分析的 MIDI 文件（至少 1 个）')
    parser.add_argument('--outdir', '-o', default='./midi_analysis_output', help='输出目录')
    args = parser.parse_args()
    main(args.midi_files, outdir=args.outdir)
