from argparse import ArgumentParser

from tqdm import tqdm

# Load dsdlib
from pydsdaudio import dsdlib


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("input_dsf")
    parser.add_argument("output_raw")
    return parser.parse_args()


# revbits
# Reverse bits if needed for DSF
def revbits(x):
    # Reverses each pair of bits
    x = ((x & 0x55) << 1) | ((x & 0xaa) >> 1)
    # Reverses each pair of double-bits
    x = ((x & 0x33) << 2) | ((x & 0xcc) >> 2)
    # Reverses the nibbles
    x = ((x & 0x0f) << 4) | ((x & 0xf0) >> 4)
    return x

# dsfxmos
# Convert input DSF DSD data to correct order for XMOS native DSD playback
def dsfxmos(size, indata, lsbfirst):

    # DSD is either 8 bits per sample, in which case it's BE
    # Or 1 bit per sample, so LE
    # See spec: https://dsd-guide.com/sites/default/files/white-papers/DSFFileFormatSpec_E.pdf
    # ALSA's DSD_U32_BE format sends frames of (32 bits * num channels)
    outdata = bytearray(size)

    # Channel 0
    j = 0
    for i in range(0, size, 8):
        outdata[i+0x00] = indata[j+0x00]
        outdata[i+0x01] = indata[j+0x01]
        outdata[i+0x02] = indata[j+0x02]
        outdata[i+0x03] = indata[j+0x03]
        j += 4
    # Channel 1
    j = 0
    for i in range(0, size, 8):
        outdata[i+0x04] = indata[j+4096+0x00]
        outdata[i+0x05] = indata[j+4096+0x01]
        outdata[i+0x06] = indata[j+4096+0x02]
        outdata[i+0x07] = indata[j+4096+0x03]
        j += 4

    if lsbfirst == 1:
        for i in range(size):
            outdata[i] = revbits(outdata[i])

    outdata = bytes(outdata)

    return outdata


def main():
    args = parse_arguments()

    dsdinfo = dsdlib.DSDFile()
    ret = dsdlib.checkdsdfile(args.input_dsf, dsdinfo)

    if dsdinfo.valid == 2:
        print(dsdinfo)
        print("Input is not a valid DSF file")
        sys.exit(1)

    with open(args.input_dsf, 'rb') as f:
        # Seek to start of DSD data
        f.seek(dsdinfo.datastart)
        remain = dsdinfo.datasize
        rdsize = 8192

        with open(args.output_raw, 'wb') as f_out:
            # Convert to RAW
            for i in tqdm(range(0, dsdinfo.datasize, rdsize)):
                dsfdata = f.read(rdsize)
                rawdata = dsfxmos(rdsize, dsfdata, dsdinfo.lsbfirst)
                f_out.write(rawdata)


if __name__ == "__main__":
    main()
