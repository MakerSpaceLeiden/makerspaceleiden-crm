# Contains a bit over 64(16bit) words:
DICT = "/usr/share/dict/web2a"
cache = []


def b16toWord(b16):
    if (b16 < 0) or (b16 >= 256 * 256):
        raise Exception("Not a 16 bit number")
    if not cache:
        with open(DICT) as f:
            for i in range(256 * 256):
                w = f.readline().strip()
                if not w:
                    raise Exception("Dictionary too small")
                cache.append(w)

    if not cache:
        raise Exception("No dictionary")

    return cache[b16]


def sha256toWords(sha256):
    out = []
    for i in range(16):
        b16 = (sha256[1] << 8) + sha256[0]

        out.append(b16toWord(b16))

        sha256 = sha256[2:]
    return out


def sha256toFull(sha256):
    return " ".join(sha256toWords(sha256))


def sha256toBabble(sha256):
    words = sha256toWords(sha256)
    return " ".join(words[3:5])


print(
    sha256toBabble(
        bytes.fromhex(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
    )
)
