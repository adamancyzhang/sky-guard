#!/usr/bin/env python3
"""
Sky Guard — Chiptune BGM Asset Generator

Generates Contra-style looping chiptune tracks using NES-like synthesis
(pulse waves, triangle, noise) and saves them as .wav files.
"""

import struct
import math
import os
import wave

SAMPLE_RATE = 44100

# ── Helper: note → frequency ────────────────────────────────────────

NOTES = {
    'C0': 16.35, 'C#0': 17.32, 'D0': 18.35, 'D#0': 19.45,
    'E0': 20.60, 'F0': 21.83, 'F#0': 23.12, 'G0': 24.50,
    'G#0': 25.96, 'A0': 27.50, 'A#0': 29.14, 'B0': 30.87,
    'C1': 32.70, 'C#1': 34.65, 'D1': 36.71, 'D#1': 38.89,
    'E1': 41.20, 'F1': 43.65, 'F#1': 46.25, 'G1': 49.00,
    'G#1': 51.91, 'A1': 55.00, 'A#1': 58.27, 'B1': 61.74,
    'C2': 65.41, 'C#2': 69.30, 'D2': 73.42, 'D#2': 77.78,
    'E2': 82.41, 'F2': 87.31, 'F#2': 92.50, 'G2': 98.00,
    'G#2': 103.83, 'A2': 110.00, 'A#2': 116.54, 'B2': 123.47,
    'C3': 130.81, 'C#3': 138.59, 'D3': 146.83, 'D#3': 155.56,
    'E3': 164.81, 'F3': 174.61, 'F#3': 185.00, 'G3': 196.00,
    'G#3': 207.65, 'A3': 220.00, 'A#3': 233.08, 'B3': 246.94,
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25,
    'E5': 659.25, 'F5': 698.46, 'F#5': 739.99, 'G5': 783.99,
    'G#5': 830.61, 'A5': 880.00, 'A#5': 932.33, 'B5': 987.77,
    'C6': 1046.50, 'C#6': 1108.73, 'D6': 1174.66, 'D#6': 1244.51,
    'E6': 1318.51, 'F6': 1396.91, 'F#6': 1479.98, 'G6': 1567.98,
    'G#6': 1661.22, 'A6': 1760.00, 'A#6': 1864.66, 'B6': 1975.53,
    'C7': 2093.00, 'C#7': 2217.46, 'D7': 2349.32, 'D#7': 2489.02,
    'E7': 2637.02, 'F7': 2793.83, 'F#7': 2959.96, 'G7': 3135.96,
    'G#7': 3322.44, 'A7': 3520.00, 'A#7': 3729.31, 'B7': 3951.07,
    'C8': 4186.01,
}
REST = None  # sentinel for rests


def note(name):
    """Convert note name to frequency. 'C4', 'Eb3', 'F#5', or None/REST for rest."""
    if name is None or name == 'R':
        return REST
    return NOTES[name]


# ── Pulse/Square Wave Generator ─────────────────────────────────────

def pulse_wave(freq, duty=0.5, phase=0.0):
    """Generate a single sample of a pulse wave with given duty cycle."""
    p = (phase % 1.0)
    return 1.0 if p < duty else -1.0


def triangle_wave(freq, duty=0.5, phase=0.0):
    """Generate a single sample of a triangle wave (duty ignored)."""
    p = (phase % 1.0)
    if p < 0.25:
        return 4.0 * p
    elif p < 0.75:
        return 2.0 - 4.0 * p
    else:
        return 4.0 * p - 4.0


def noise_sample(prev, mode=False, feedback=0):
    """16-bit LFSR noise, returns -1..1."""
    # Simple noise - white noise
    import random
    return random.uniform(-1, 1)


# ── Note Sequencer ───────────────────────────────────────────────────

def seq_to_samples(notes, bpm, samples_per_beat, wave_func, duty=0.5, volume=0.3, slide=False):
    """
    Convert a list of (note_name, beats) into audio samples.
    Each note has a small envelope (quick attack, slight decay).
    If slide=True, pitch slides between consecutive notes.
    """
    total_samples = int(samples_per_beat * sum(b for _, b in notes))
    samples = [0.0] * total_samples
    spb = samples_per_beat

    idx = 0
    prev_freq = None
    for i, (n, beats) in enumerate(notes):
        if n is None or n == 'R':
            idx += int(spb * beats)
            prev_freq = None
            continue

        freq = note(n)
        if freq is None:
            idx += int(spb * beats)
            continue

        length = int(spb * beats)
        env_end = min(length, int(spb * 0.08))  # 80ms attack
        env_tail = max(0, length - int(spb * 0.6))  # sustain level after decay

        next_freq = None
        if slide and i + 1 < len(notes):
            n2 = notes[i + 1][0]
            if n2 and n2 != 'R':
                next_freq = note(n2)

        for j in range(length):
            t_global = (idx + j) / SAMPLE_RATE
            phase = freq * t_global

            # Envelope: quick attack, slight decay to sustain
            if j < env_end:
                env = 0.7 + 0.3 * (j / env_end)
            elif j < env_tail:
                env = 1.0 - 0.3 * ((j - env_end) / (env_tail - env_end))
            else:
                env = 0.7  # sustain

            # Frequency slide between notes
            if slide and next_freq and j < length:
                t = j / length
                slide_freq = freq + (next_freq - freq) * (t ** 2)
            else:
                slide_freq = freq

            val = wave_func(slide_freq, duty, phase)
            samples[idx + j] += val * volume * env

        idx += length

    return samples


def render_track(notes, bpm, samples_per_beat, track_type='pulse1', volume=0.3, duty=0.5):
    """Render a track using the specified type."""
    if track_type == 'pulse1':
        return seq_to_samples(notes, bpm, samples_per_beat, pulse_wave, duty=0.125, volume=volume)
    elif track_type == 'pulse2':
        return seq_to_samples(notes, bpm, samples_per_beat, pulse_wave, duty=0.25, volume=volume)
    elif track_type == 'triangle':
        return seq_to_samples(notes, bpm, samples_per_beat, triangle_wave, volume=volume)
    elif track_type == 'noise':
        # Noise channel uses seq only for timing
        total_samples = int(samples_per_beat * sum(b for _, b in notes))
        samples = [0.0] * total_samples
        spb = samples_per_beat
        idx = 0
        for n, beats in notes:
            length = int(spb * beats)
            if n is not None and n != 'R':
                for j in range(length):
                    env = 1.0 - 0.3 * (j / max(1, length))
                    samples[idx + j] = noise_sample(0) * volume * env
            idx += length
        return samples
    return [0.0]  # fallback


def mix_tracks(tracks, num_samples):
    """Mix multiple sample arrays together, normalizing to avoid clipping."""
    result = [0.0] * num_samples
    for t in tracks:
        for i in range(min(len(t), num_samples)):
            result[i] += t[i]

    # Soft limit (tanh clipper)
    for i in range(num_samples):
        result[i] = math.tanh(result[i] * 0.7)

    return result


def save_wav(path, samples, sample_rate=SAMPLE_RATE, volume=0.7):
    """Save samples as a 16-bit mono WAV file."""
    max_amp = 32767 * volume
    samples_16bit = []
    for s in samples:
        s = max(-1.0, min(1.0, s))
        samples_16bit.append(int(s * max_amp))

    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f'<{len(samples_16bit)}h', *samples_16bit))


def ensure_loop(samples, sample_rate, loop_duration):
    """Ensure the samples loop seamlessly using a small crossfade."""
    loop_len = int(sample_rate * loop_duration)
    if loop_len > len(samples):
        return samples

    fade = int(sample_rate * 0.02)  # 20ms crossfade
    result = list(samples)

    for i in range(fade):
        t = i / fade
        # Crossfade beginning into end
        result[i] = result[i] * (1 - t) + result[len(samples) - fade + i] * t
        result[len(samples) - fade + i] = result[i]  # symmetric

    return result


# ══════════════════════════════════════════════════════════════════════
#  MENU BGM — "Sky Guard Theme"  Contra-style heroic overture
#  Key: Dm, Tempo: 130 BPM
#  Feel: Epic fanfare → driving action (like Contra title screen)
# ══════════════════════════════════════════════════════════════════════

def gen_menu_bgm():
    """Menu BGM: Heroic chiptune fanfare, ~16s loop."""
    SAMPLE_RATE = 44100
    bpm = 130
    spb = int(SAMPLE_RATE * 60 / bpm)  # samples per beat
    loop_bars = 8  # 8 bars → 32 beats
    loop_samples = spb * 4 * loop_bars  # 32 beats × 4 beats/bar

    # ── Melody (Pulse 1, duty 12.5% — piercing lead) ──
    melody = [
        # Bar 1-2 — Heroic fanfare
        ('D5', 1.5), ('F5', 0.5),
        ('A5', 1.0), ('D6', 1.0),
        ('C6', 0.5), ('A5', 0.5),
        ('F5', 0.5), ('E5', 0.5),
        # Bar 3-4 — Descending
        ('D5', 1.0), ('F5', 0.5), ('G5', 0.5),
        ('A5', 1.0), ('C6', 0.5), ('A5', 0.5),
        ('G5', 0.5), ('F5', 0.5), ('E5', 0.5), ('D5', 0.5),
        # Bar 5-6 — Ascending action
        ('F5', 0.5), ('G5', 0.5), ('A5', 0.5), ('A#5', 0.5),
        ('C6', 1.0), ('D6', 0.5), ('C6', 0.5),
        ('A5', 0.5), ('G5', 0.5), ('F5', 0.5), ('E5', 0.5),
        # Bar 7-8 — Cadence
        ('D5', 0.5), ('F5', 0.5), ('A5', 0.5), ('D6', 0.5),
        ('C6', 1.0), ('A5', 1.0),
        ('G5', 1.0), ('F5', 0.5), ('E5', 0.5),
        # Loop back transition
        ('D5', 0.5), ('F5', 0.5), ('A5', 0.5), ('D6', 0.5),
        ('C6', 1.0), ('A#5', 0.5), ('A5', 0.5),
        ('G5', 1.0), ('A5', 0.5), ('G5', 0.5),
    ]
    melody_samples = render_track(melody, bpm, spb, 'pulse1', volume=0.25, duty=0.125)

    # ── Harmony/Countermelody (Pulse 2, duty 50%) ──
    harmony = [
        ('A4', 1.0), ('R', 1.0), ('C5', 0.5), ('D5', 0.5), ('C5', 0.5), ('A4', 0.5),
        ('G4', 0.5), ('F4', 0.5), ('G4', 0.5), ('A4', 0.5),
        ('A4', 1.0), ('C5', 1.0),
        ('D5', 0.5), ('C5', 0.5), ('A#4', 0.5), ('A4', 0.5),
        ('G4', 1.0), ('F4', 1.0),
        # Bars 5-8
        ('C5', 0.5), ('D5', 0.5), ('E5', 0.5), ('F5', 0.5),
        ('E5', 1.0), ('D5', 0.5), ('C5', 0.5),
        ('D5', 0.5), ('C5', 0.5), ('A#4', 0.5), ('A4', 0.5),
        ('G4', 0.5), ('A4', 0.5), ('A#4', 0.5), ('C5', 0.5),
        # Cadence
        ('A4', 1.0), ('D5', 1.0),
        ('C5', 1.0), ('A4', 0.5), ('G4', 0.5),
        ('F4', 1.0), ('E4', 1.0),
        ('D4', 1.0), ('R', 1.0),
    ]
    harmony_samples = render_track(harmony, bpm, spb, 'pulse2', volume=0.15, duty=0.5)

    # ── Bass (Triangle wave) ──
    bass = [
        ('D3', 2.0), ('A2', 1.0), ('A#2', 1.0),
        ('C3', 2.0), ('G2', 1.0), ('A2', 1.0),
        ('D3', 2.0), ('F3', 1.0), ('E3', 1.0),
        ('A2', 2.0), ('E2', 1.0), ('F2', 1.0),
        # Loop
        ('D3', 2.0), ('A2', 1.0), ('A#2', 1.0),
        ('C3', 2.0), ('G2', 1.0), ('A2', 1.0),
        ('D3', 2.0), ('F3', 1.0), ('E3', 1.0),
        ('A2', 2.0), ('A2', 1.0), ('D3', 1.0),
    ]
    bass_samples = render_track(bass, bpm, spb, 'triangle', volume=0.35)

    # ── Percussion (Noise channel — kick & snare) ──
    perc = []
    for beat in range(32):
        if beat % 4 == 0:
            # Kick drum on beats 1, 5, 9, 13...
            perc.append(('X', 0.15))
            perc.append(('R', 0.85))
        elif beat % 4 == 2:
            # Snare on beats 3, 7, 11, 15...
            perc.append(('X', 0.10))
            perc.append(('R', 0.90))
        else:
            perc.append(('R', 1.0))
    # Compress into 32 beats worth
    perc_notes = []
    for beat in range(32):
        if beat % 4 == 0:
            perc_notes.append(('X', 0.15))
            perc_notes.append(('R', 0.85))
        elif beat % 4 == 2:
            perc_notes.append(('X', 0.10))
            perc_notes.append(('R', 0.90))
        else:
            perc_notes.append(('R', 1.0))

    # Hi-hat every 8th note
    hihat = []
    for beat in range(32):
        for eighth in range(2):
            if eighth == 0:
                hihat.append(('X', 0.06))
            else:
                hihat.append(('X', 0.04))
            hihat.append(('R', 0.44))

    perc_samples = render_track(perc_notes, bpm, spb, 'noise', volume=0.15)
    hihat_samples = render_track(hihat, bpm, spb, 'noise', volume=0.05)

    # Mix & trim to loop length
    tracks = [melody_samples, harmony_samples, bass_samples, perc_samples, hihat_samples]
    mixed = mix_tracks(tracks, loop_samples)

    # Ensure seamless loop
    mixed = ensure_loop(mixed, SAMPLE_RATE, 0.02)

    return mixed


# ══════════════════════════════════════════════════════════════════════
#  PLAY BGM — "Jungle Assault"  High-energy action
#  Key: Em, Tempo: 150 BPM
#  Feel: Like Contra Jungle Stage — relentless, driving
# ══════════════════════════════════════════════════════════════════════

def gen_play_bgm():
    """Play BGM: High-energy action loop, ~13s."""
    SAMPLE_RATE = 44100
    bpm = 150
    spb = int(SAMPLE_RATE * 60 / bpm)
    loop_bars = 8  # 32 beats
    loop_samples = spb * 4 * loop_bars

    # ── Main Lead (Pulse 1, duty 25% — aggressive) ──
    melody = [
        # Riff A (bars 1-2)
        ('E5', 0.25), ('G5', 0.25), ('A5', 0.25), ('B5', 0.25),
        ('C6', 0.25), ('B5', 0.25), ('A5', 0.25), ('G5', 0.25),
        ('A5', 0.25), ('G5', 0.25), ('F#5', 0.25), ('E5', 0.25),
        ('D5', 0.25), ('E5', 0.25), ('F#5', 0.25), ('G5', 0.25),
        # Riff B (bars 3-4)
        ('A5', 0.25), ('C6', 0.25), ('B5', 0.25), ('A5', 0.25),
        ('G5', 0.25), ('F#5', 0.25), ('E5', 0.25), ('D5', 0.25),
        ('E5', 0.25), ('F#5', 0.25), ('G5', 0.25), ('A5', 0.25),
        ('B5', 0.25), ('A5', 0.25), ('G5', 0.25), ('F#5', 0.25),
        # Riff C (bars 5-6)
        ('E5', 0.25), ('G5', 0.25), ('A5', 0.25), ('B5', 0.25),
        ('C6', 0.5), ('B5', 0.25), ('A5', 0.25),
        ('G5', 0.25), ('F#5', 0.25), ('E5', 0.25), ('D5', 0.25),
        ('C5', 0.5), ('D5', 0.5),
        # Riff D (bars 7-8)
        ('E5', 0.25), ('F#5', 0.25), ('G5', 0.25), ('A5', 0.25),
        ('G5', 0.5), ('E5', 0.5),
        ('F#5', 0.25), ('G5', 0.25), ('A5', 0.25), ('B5', 0.25),
        ('A5', 0.5), ('G5', 0.25), ('F#5', 0.25),
    ]
    melody_samples = render_track(melody, bpm, spb, 'pulse1', volume=0.22, duty=0.25)

    # ── Countermelody (Pulse 2, duty 50% — rounder) ──
    counter = [
        ('E4', 1.0), ('R', 1.0), ('A4', 1.0), ('B4', 0.5), ('C5', 0.5),
        ('D5', 0.5), ('C5', 0.5), ('B4', 1.0), ('A4', 1.0),
        ('C5', 1.0), ('B4', 0.5), ('A4', 0.5),
        ('G4', 1.0), ('E4', 0.5), ('F#4', 0.5),
        ('G4', 1.0), ('A4', 1.0),
        ('E5', 1.0), ('D5', 0.5), ('C5', 0.5),
        ('D5', 1.0), ('C5', 0.5), ('B4', 0.5),
        ('B4', 0.5), ('A4', 0.5), ('G4', 1.0), ('A4', 1.0),
    ]
    counter_samples = render_track(counter, bpm, spb, 'pulse2', volume=0.12, duty=0.5)

    # ── Arpeggio (Pulse 1, rapid ascending arpeggios) ──
    arp = []
    # Explicit arpeggio pattern: Em → Cmaj → Dm → Bdim
    arp_patterns = [
        ['E4', 'G4', 'B4', 'E5'],
        ['C4', 'E4', 'G4', 'C5'],
        ['D4', 'F4', 'A4', 'D5'],
        ['B3', 'D4', 'F4', 'B4'],
    ]
    for beat in range(32):
        pat = arp_patterns[beat // 8 % 4]
        for note_name in pat:
            arp.append((note_name, 0.25))
    arp_samples = render_track(arp, bpm, spb, 'pulse1', volume=0.08, duty=0.125)

    # ── Bass (Triangle) ──
    bass = []
    for beat in range(32):
        if beat < 8:
            bass.append(('E2', 1.0))
        elif beat < 16:
            bass.append(('C2', 1.0))
        elif beat < 24:
            bass.append(('D2', 1.0))
        else:
            bass.append(('B1', 1.0))
    bass_samples = render_track(bass, bpm, spb, 'triangle', volume=0.4)

    # ── Percussion (driving kick + snare) ──
    perc = []
    hihat = []
    for beat in range(32):
        # Kick on every quarter note
        perc.append(('X', 0.08))
        perc.append(('R', 0.92))
        # Snare on beats 2 & 4
        if beat % 4 in (1, 3):
            pass  # handled above
        # Hi-hat 8th notes
        hihat.append(('X', 0.04))
        hihat.append(('R', 0.46))
    # Actually build proper perc sequence
    kick = []
    snare = []
    hihat = []
    for beat in range(32):
        # Kick on 1 & 3
        if beat % 2 == 0:
            kick.append(('X', 0.10))
        kick.append(('R', 0.90))
        # Snare on 2 & 4
        if beat % 4 in (1, 3):
            snare.append(('X', 0.08))
        snare.append(('R', 0.92))
        # Hi-hat every 8th
        hihat.append(('X', 0.04))
        hihat.append(('R', 0.46))

    kick_samples = render_track(kick, bpm, spb, 'noise', volume=0.18)
    snare_samples = render_track(snare, bpm, spb, 'noise', volume=0.12)
    hihat_samples = render_track(hihat, bpm, spb, 'noise', volume=0.04)

    tracks = [melody_samples, counter_samples, arp_samples, bass_samples,
              kick_samples, snare_samples, hihat_samples]
    mixed = mix_tracks(tracks, loop_samples)
    mixed = ensure_loop(mixed, SAMPLE_RATE, 0.02)
    return mixed


# ══════════════════════════════════════════════════════════════════════
#  BOSS BGM — "Final Stand"  Intense boss fight
#  Key: F#m, Tempo: 165 BPM
#  Feel: Urgent, menacing, relentless
# ══════════════════════════════════════════════════════════════════════

def gen_boss_bgm():
    """Boss BGM: Intense boss fight loop, ~12s."""
    SAMPLE_RATE = 44100
    bpm = 165
    spb = int(SAMPLE_RATE * 60 / bpm)
    loop_bars = 8  # 32 beats
    loop_samples = spb * 4 * loop_bars

    # ── Menacing Lead (Pulse 1, duty 12.5% — piercing, urgent) ──
    melody = [
        # Bar 1-2
        ('F#5', 0.25), ('A5', 0.25), ('C#6', 0.25), ('E6', 0.25),
        ('D6', 0.5), ('C#6', 0.25), ('B5', 0.25),
        ('A5', 0.25), ('G#5', 0.25), ('F#5', 0.25), ('E5', 0.25),
        ('F#5', 0.5), ('G#5', 0.5),
        # Bar 3-4
        ('A5', 0.25), ('C#6', 0.25), ('E6', 0.25), ('D6', 0.25),
        ('C#6', 0.5), ('B5', 0.25), ('A5', 0.25),
        ('G#5', 0.25), ('F#5', 0.25), ('E5', 0.25), ('D5', 0.25),
        ('E5', 0.5), ('F#5', 0.5),
        # Bar 5-6
        ('C#6', 0.25), ('D6', 0.25), ('E6', 0.25), ('F#6', 0.25),
        ('E6', 0.5), ('D6', 0.25), ('C#6', 0.25),
        ('B5', 0.25), ('A5', 0.25), ('G#5', 0.25), ('F#5', 0.25),
        ('E5', 0.5), ('D5', 0.5),
        # Bar 7-8 — Climax
        ('F#5', 0.25), ('G#5', 0.25), ('A5', 0.25), ('B5', 0.25),
        ('C#6', 0.5), ('B5', 0.25), ('A5', 0.25),
        ('G#5', 0.5), ('F#5', 0.25), ('E5', 0.25),
        ('D5', 2.0),  # Hold, then loop
    ]
    melody_samples = render_track(melody, bpm, spb, 'pulse1', volume=0.22, duty=0.125)

    # ── Second Voice (Pulse 2, duty 25% — darker) ──
    voice2 = [
        # Staccato chords
        ('F#4', 1.5), ('G#4', 0.5),
        ('A4', 1.0), ('C#5', 0.5), ('B4', 0.5),
        ('A4', 0.5), ('G#4', 0.5), ('F#4', 1.0),
        ('E4', 1.0), ('D4', 1.0),
        # Repeat
        ('F#4', 1.5), ('G#4', 0.5),
        ('A4', 1.0), ('C#5', 0.5), ('B4', 0.5),
        ('A4', 0.5), ('G#4', 0.5), ('F#4', 1.0),
        ('E4', 1.0), ('D4', 1.0),
    ]
    voice2_samples = render_track(voice2, bpm, spb, 'pulse2', volume=0.10, duty=0.25)

    # ── Rapid arpeggios (for tension) ──
    arp = []
    boss_arp_patterns = [
        ['F#4', 'A4', 'C#5', 'F#5'],
        ['A4', 'C#5', 'E5', 'A5'],
        ['C#5', 'F#5', 'A5', 'C#6'],
        ['E4', 'G#4', 'B4', 'E5'],
    ]
    for beat in range(32):
        pat = boss_arp_patterns[beat // 8 % 4]
        for note_name in pat * 2:  # play pattern twice per beat for 16th notes
            arp.append((note_name, 0.125))
    arp_samples = render_track(arp, bpm, spb, 'pulse1', volume=0.06, duty=0.125)

    # ── Bass (Triangle, driving 8th notes) ──
    bass = []
    for beat in range(32):
        if beat < 8:
            bass.append(('F#2', 0.5)), bass.append(('F#2', 0.5))
        elif beat < 16:
            bass.append(('A2', 0.5)), bass.append(('A2', 0.5))
        elif beat < 24:
            bass.append(('C#3', 0.5)), bass.append(('C#3', 0.5))
        else:
            bass.append(('E2', 0.5)), bass.append(('E2', 0.5))
    bass_samples = render_track(bass, bpm, spb, 'triangle', volume=0.45)

    # ── Percussion (fast, aggressive double-time feel) ──
    kick = []
    snare = []
    hihat = []
    for beat in range(32):
        # Kick on every beat
        kick.append(('X', 0.07))
        kick.append(('R', 0.93))
        # Snare on 2 & 4 (even beats = 1-indexed 2 & 4)
        if beat % 4 in (1, 3):
            snare.append(('X', 0.10))
        else:
            snare.append(('R', 1.0))
        # Hi-hat 16th notes
        hihat.append(('X', 0.03))
        hihat.append(('R', 0.22))
        hihat.append(('X', 0.02))
        hihat.append(('R', 0.23))

    kick_samples = render_track(kick, bpm, spb, 'noise', volume=0.20)
    snare_samples = render_track(snare, bpm, spb, 'noise', volume=0.15)
    hihat_samples = render_track(hihat, bpm, spb, 'noise', volume=0.05)

    tracks = [melody_samples, voice2_samples, arp_samples, bass_samples,
              kick_samples, snare_samples, hihat_samples]
    mixed = mix_tracks(tracks, loop_samples)
    mixed = ensure_loop(mixed, SAMPLE_RATE, 0.02)
    return mixed


# ══════════════════════════════════════════════════════════════════════
#  Main entry point
# ══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'audio')
    os.makedirs(assets_dir, exist_ok=True)

    print("🎵 Generating Menu BGM (heroic overture)...")
    menu = gen_menu_bgm()
    menu_path = os.path.join(assets_dir, 'bgm_menu.wav')
    save_wav(menu_path, menu)
    print(f"   ✓ {menu_path}  ({len(menu)/44100:.1f}s, {len(menu)} samples)")

    print("🎵 Generating Play BGM (jungle assault)...")
    play = gen_play_bgm()
    play_path = os.path.join(assets_dir, 'bgm_play.wav')
    save_wav(play_path, play)
    print(f"   ✓ {play_path}  ({len(play)/44100:.1f}s, {len(play)} samples)")

    print("🎵 Generating Boss BGM (final stand)...")
    boss = gen_boss_bgm()
    boss_path = os.path.join(assets_dir, 'bgm_boss.wav')
    save_wav(boss_path, boss)
    print(f"   ✓ {boss_path}  ({len(boss)/44100:.1f}s, {len(boss)} samples)")

    print("\n✔ All BGM assets generated!")