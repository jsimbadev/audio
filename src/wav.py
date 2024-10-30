import sys
import struct

from argparse import ArgumentParser
from dataclasses import dataclass, fields
from ctypes import c_uint32, c_ushort, c_byte, c_char_p

DUAL_CHANNEL = 2
IEEE_FLOAT = 3
PCM = 1
DEFAULT_BITS_PER_SAMPLE = 16
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_BLOCK_ID=b"RIFF"
DEFAULT_FILE_FORMAT_ID=b"WAVE"
DEFAULT_FORMAT_BLOCK_ID=b"fmt "
DEFAULT_DATA_BLOCK_ID=b"data"
ENDIANNESS = "<" if 'little' in sys.byteorder else ">"


@dataclass
class Wav:
    # Inspiration from 
    # https://en.wikipedia.org/wiki/WAV
    # https://docs.fileformat.com/audio/wav/

    # Master RIFF chunk
    file_type_block_id: c_char_p  # 4 bytes/chars
    file_size: c_uint32  # 4 bytes ..  Overall file size minus 8 bytes
    file_format_id: c_char_p # 4 bytes

    # Chunk describing data format
    format_block_id: c_char_p # 4 bytes/ chars .. add whitespace if necessary
    block_size: c_uint32 # 4 bytes
    audio_format: c_ushort # 2 bytes (1: PCM integer, 3: IEEE 754 float)
    num_channels: c_ushort # 2 bytes
    sample_rate: c_uint32 # 4 byes (32 bits)
    bytes_per_second: c_uint32 # 4 bytes .. Number of bytes to read per second (Frequence * BytePerBloc).
    bytes_per_block: c_ushort # 2 bytes .. Number of bytes per block (NbrChannels * BitsPerSample / 8)
    bits_per_sample: c_ushort # 2 bytes .. 

    # chunk containing sample data
    data_block_id: c_byte # 4 bytes/chars
    data_size: c_uint32 # 4 bytes
    sample_data: c_char_p

    def to_bytes(self,):
        b = bytearray()
        for field in fields(self):
            value = getattr(self, field.name)
            field_type = field.type
            if not isinstance(value, bytes):
                value = bytes(field_type(value))
            b.extend(value)

        return b


def default_wav() -> Wav:
    block_align = int(DUAL_CHANNEL * ( DEFAULT_BITS_PER_SAMPLE / 8))
    bytes_per_second = block_align * DEFAULT_SAMPLE_RATE
    return Wav(
        file_type_block_id=DEFAULT_BLOCK_ID,
        file_size=0,
        file_format_id=DEFAULT_FILE_FORMAT_ID,

        format_block_id=DEFAULT_FORMAT_BLOCK_ID,
        block_size=16,
        audio_format=PCM,  # 1 integer
        num_channels=DUAL_CHANNEL,
        sample_rate=DEFAULT_SAMPLE_RATE,
        bytes_per_second=bytes_per_second,
        bytes_per_block=block_align,
        bits_per_sample=DEFAULT_BITS_PER_SAMPLE,

        data_block_id=DEFAULT_DATA_BLOCK_ID,
        data_size=0,
        sample_data=b''
    )


def write_wav(data: bytes, output_f: str):
    wav = default_wav()
    wav.sample_data = data
    wav.data_size = len(data)
    bytes_to_write = wav.to_bytes()

    # update file size in bytes...
    wav.file_size = len(bytes_to_write) - 8 

    with open(output_f, 'wb') as audio_file:
        audio_file.write(wav.to_bytes())
    
    return
    

def header_parser(wav_bytes: bytes):
    wav_header_info = struct.unpack(f"{ENDIANNESS}4sI4s4sIHHIIHH4sI", wav_bytes[:44])
    print(wav_header_info)
    return


def main():
    parser = ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--mode", default='header', required=False)
    args = parser.parse_args()

    if args.mode == 'header':
        input_bytes = open(args.input, 'rb').read()
        header_parser(input_bytes)

    if args.mode == 'generate':
        assert args.output, "Must specify output file to generate wav for."
        import math
        from array import array
        frequency = 250
        max_amplitude = 32_700
        duration = 5 # 5 seconds
        audio = []
        for i in range(DEFAULT_SAMPLE_RATE * duration):
            amplitude = (i / DEFAULT_SAMPLE_RATE  ) * max_amplitude
            signal = 1 #math.sin((2 * math.pi * i * frequency) / DEFAULT_SAMPLE_RATE)

            channel_1 = amplitude * signal / 2
            channel_2 = (max_amplitude - amplitude) * signal
            # https://docs.python.org/3/library/struct.html
            # little endian float16
            audio.extend([struct.pack("<f", channel_1), struct.pack("<f", channel_2)])

        write_wav(b"".join(audio), args.output)


if __name__ == "__main__":
    main()
    