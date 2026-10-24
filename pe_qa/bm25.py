"""Small dependency-free Okapi BM25."""
import math
import re
from collections import Counter

STOP = set("a an and are as at be by for from has have how in is it its of on or that the this to was what when which who with within".split())


def tokenize(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())
    return [t for t in toks if t not in STOP]


class BM25:
    def __init__(self, docs: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tokens = [tokenize(d) for d in docs]
        self.tf = [Counter(t) for t in self.tokens]
        self.dl = [len(t) for t in self.tokens]
        self.avgdl = sum(self.dl) / max(len(self.dl), 1)
        df = Counter()
        for t in self.tf:
            df.update(t.keys())
        n = len(docs)
        self.idf = {w: math.log(1 + (n - c + 0.5) / (c + 0.5)) for w, c in df.items()}

    def score(self, query: str) -> list[float]:
        q = tokenize(query)
        out = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for w in q:
                if w not in tf:
                    continue
                f = tf[w]
                s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
            out.append(s)
        return out
