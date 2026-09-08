"""Offline, provenance-bearing attribute postings; missing data is not negative.

The active submission does not load this experimental sidecar. Category and
price handling remain with the existing catalog evidence layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sqlite3


SCHEMA = 'attribute-evidence-v1'
COLORS = ('black white blue red pink green brown gray grey purple yellow orange '
          'navy teal tan beige ivory cream khaki charcoal magenta cyan turquoise '
          'indigo violet maroon burgundy coral lavender olive gold silver clear transparent').split()
MATERIALS = ('cotton polyester nylon leather wool spandex silk rayon fabric suede canvas '
             'linen rubber mesh fleece denim velvet cashmere acrylic microfiber '
             'wood plastic silicone titanium aluminum gemstone').split() + ['stainless steel', 'polyvinyl chloride']
FEATURES = ['waterproof', 'water resistant', 'breathable', 'windproof', 'machine washable', 'rfid blocking']
LEXICON = {('color', x) for x in COLORS} | {('material', x) for x in MATERIALS} | {('feature', x) for x in FEATURES}
_BY_WORD = {}
for _attr, _word in sorted(LEXICON):
    _BY_WORD.setdefault(_word, []).append(_attr)
_MENTION = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(x).replace(r'\ ', r'[ -]')
                       for x in sorted(_BY_WORD, key=len, reverse=True)) + r')(?!\w)', re.I)
_FIELD = {'color': 'color', 'colour': 'color', 'material': 'material', 'fabrictype': 'material',
          'fabric': 'material', 'size': 'size', 'sizemap': 'size', 'brand': 'brand',
          'brandname': 'brand', 'style': 'style', 'specialfeature': 'feature'}
_NEGATIVE_PREFIX = re.compile(r'\b(?:no|not|without|faux|imitation|free of)\s*[-:]?\s*$', re.I)
_NEGATIVE_SUFFIX = re.compile(r'^(?:\s*-\s*free\b|\s+free(?=[.,;]|$))', re.I)
_UNCERTAIN = re.compile(r'\b(?:if|maybe|perhaps|might|instead|replace|no longer|ignore)\b|["“”]', re.I)


def normalize(value: str) -> str:
    return ' '.join('gray' if token == 'grey' else token
                    for token in re.findall(r'\w+', value.casefold()))


def _size(value: str) -> str:
    value = normalize(value)
    return {'small': 's', 'medium': 'm', 'large': 'l', 'extra small': 'xs', 'extra large': 'xl'}.get(value, value)


@dataclass(frozen=True)
class Fact:
    attribute: str
    value: str
    polarity: int
    tier: int  # 1: explicit field, 0: text mention
    source: str
    raw: str


@dataclass(frozen=True)
class QueryAtom:
    attribute: str
    value: str
    polarity: int = 1


def _mentions(text: str, source: str, tier: int, attribute: str | None = None):
    text = text[:4096]
    for match in _MENTION.finditer(text):
        token = match[0].casefold().replace('-', ' ')
        before, after = text[max(0, match.start() - 32):match.start()], text[match.end():match.end() + 16]
        negative_before = bool(_NEGATIVE_PREFIX.search(before))
        negative_after = bool(_NEGATIVE_SUFFIX.search(after))
        if re.search(r'\bnot only\s*$', before, re.I) or (negative_before and negative_after):
            continue
        polarity = -1 if negative_before or negative_after else 1
        for attr in _BY_WORD[token]:
            if attribute is not None and attr != attribute:
                continue
            yield Fact(attr, normalize(token), polarity, tier, source, text[:256])
            if attr == 'material' and polarity == 1 and re.search(r'(?<!\d)100\s*%\s*$', before):
                yield Fact(attr, 'pure:' + normalize(token), polarity, tier, source, text[:256])


def extract_facts(product: dict) -> tuple[Fact, ...]:
    facts = []
    details = product.get('details')
    if isinstance(details, dict):
        for key, raw in details.items():
            attr = _FIELD.get(re.sub(r'\W|_', '', str(key).casefold()))
            if attr is None:
                continue
            values = raw if isinstance(raw, list) else [raw]
            for value in values[:32]:
                if not isinstance(value, (str, int, float)) or isinstance(value, bool):
                    continue
                text = str(value).strip()
                if not text or normalize(text) in {'unknown', 'n a', 'none', 'not available'}:
                    continue
                source = f'details.{key}'
                facts.extend(_mentions(text, source, 1, attr))
                if attr in {'brand', 'style', 'size'} and len(text) <= 128:
                    facts.append(Fact(attr, _size(text) if attr == 'size' else normalize(text), 1, 1, source, text))
    title = product.get('title')
    if isinstance(title, str):
        facts.extend(_mentions(title, 'title', 0))
    features = product.get('features')
    if isinstance(features, str):
        features = [features]
    if isinstance(features, list):
        for i, feature in enumerate(features[:16]):
            if isinstance(feature, str):
                facts.extend(_mentions(feature, f'features[{i}]', 0))
    return tuple(dict.fromkeys(facts))


def query_atoms(state) -> tuple[QueryAtom, ...]:
    atoms = []
    for raw, attr, sign in [(r.value, r.attribute, 1) for r in state.requirements] + [(v, None, -1) for v in state.excluded]:
        if _UNCERTAIN.search(raw):
            continue
        text = re.sub(r'^\s*(?:material|colou?r|fabric|size|brand|style|feature)\s*[:=]\s*', '', raw, flags=re.I)
        if attr in {'brand', 'style', 'size'}:
            atoms.append(QueryAtom(attr, _size(text) if attr == 'size' else normalize(text), sign))
            continue
        facts = tuple(_mentions(text, 'query', 0, attr if attr in {'color', 'material', 'feature'} else None))
        pure = {f.value.removeprefix('pure:') for f in facts if f.value.startswith('pure:')}
        for fact in facts:
            if fact.attribute == 'material' and fact.value in pure:
                continue
            atoms.append(QueryAtom(fact.attribute, fact.value, sign * fact.polarity))
    return tuple(dict.fromkeys(atoms))[:8]


def catalog_digest(catalog: Path) -> str:
    digest = hashlib.sha256()
    with catalog.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def build_attribute_index(catalog: Path, destination: Path, *, omit_details: bool = False) -> dict:
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(destination)
    connection.executescript('''
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE products(ordinal INTEGER PRIMARY KEY, asin TEXT UNIQUE NOT NULL);
        CREATE TABLE facts(ordinal INTEGER, attribute TEXT, value TEXT, polarity INTEGER,
                           tier INTEGER, source TEXT, raw TEXT);
        CREATE INDEX facts_product ON facts(ordinal, attribute, value);
        CREATE TABLE postings(attribute TEXT, value TEXT, field_positive BLOB, field_negative BLOB,
                              text_positive BLOB, text_negative BLOB, PRIMARY KEY(attribute,value));
    ''')
    postings = {}
    count = fact_count = 0
    try:
        with catalog.open() as handle:
            for ordinal, line in enumerate(handle):
                product = json.loads(line)
                connection.execute('INSERT INTO products VALUES (?,?)', (ordinal, product['parent_asin']))
                facts = extract_facts({**product, 'details': {}} if omit_details else product)
                connection.executemany('INSERT INTO facts VALUES (?,?,?,?,?,?,?)',
                    [(ordinal, f.attribute, f.value, f.polarity, f.tier, f.source, f.raw) for f in facts])
                for fact in facts:
                    masks = postings.setdefault((fact.attribute, fact.value), [0, 0, 0, 0])
                    lane = (0 if fact.tier == 1 else 2) + int(fact.polarity < 0)
                    masks[lane] |= 1 << ordinal
                count += 1
                fact_count += len(facts)
        connection.executemany('INSERT INTO postings VALUES (?,?,?,?,?,?)',
            [(attr, val, *(mask.to_bytes((mask.bit_length() + 7) // 8, 'little') for mask in masks))
             for (attr, val), masks in sorted(postings.items())])
        report = {'schema': SCHEMA, 'catalog_sha256': catalog_digest(catalog),
                  'products': count, 'facts': fact_count, 'postings': len(postings),
                  'detail_fields': 'omitted' if omit_details else 'included'}
        connection.executemany('INSERT INTO meta VALUES (?,?)', [(k, str(v)) for k, v in report.items()])
        connection.commit()
        return report
    except Exception:
        connection.close()
        destination.unlink(missing_ok=True)
        raise
    finally:
        connection.close()


class AttributeIndex:
    def __init__(self, path: Path, catalog: Path):
        self.connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
        try:
            meta = dict(self.connection.execute('SELECT key,value FROM meta'))
            if meta.get('schema') != SCHEMA or meta.get('catalog_sha256') != catalog_digest(catalog):
                raise ValueError('attribute index does not match the catalog/schema')
            self.ordinals = {asin: ordinal for ordinal, asin in self.connection.execute('SELECT ordinal,asin FROM products')}
        except Exception:
            self.connection.close()
            raise
        self._postings = lru_cache(maxsize=128)(self._load_postings)

    def _load_postings(self, attr: str, value: str):
        row = self.connection.execute('SELECT field_positive,field_negative,text_positive,text_negative '
                                      'FROM postings WHERE attribute=? AND value=?', (attr, value)).fetchone()
        return tuple(int.from_bytes(v, 'little') for v in row) if row else (0, 0, 0, 0)

    def evidence(self, asin: str, atom: QueryAtom) -> tuple[str, int]:
        ordinal = self.ordinals.get(asin)
        if ordinal is None:
            return 'unknown', 0
        fp, fn, tp, tn = ((mask >> ordinal) & 1 for mask in self._postings(atom.attribute, atom.value))
        positive, negative = fp or tp, fn or tn
        if positive and negative:
            return 'conflict', 0
        if not positive and not negative:
            return 'unknown', 0
        agrees = positive if atom.polarity == 1 else negative
        return ('match' if agrees else 'counterevidence'), int(bool(fp or fn))

    def rerank(self, ids: tuple[str, ...], atoms: tuple[QueryAtom, ...], *, counterevidence_only: bool = False) -> tuple[str, ...]:
        def score(asin):
            field = text = 0
            for atom in atoms:
                status, tier = self.evidence(asin, atom)
                delta = 1 if status == 'match' else -1 if status == 'counterevidence' else 0
                if counterevidence_only and delta > 0:
                    delta = 0
                if tier:
                    field += delta
                else:
                    text += delta
            return field, text
        return tuple(sorted(ids, key=score, reverse=True))

    def explain(self, asin: str, atom: QueryAtom) -> list[dict]:
        rows = self.connection.execute('SELECT polarity,tier,source,raw FROM facts '
            'WHERE ordinal=? AND attribute=? AND value=?',
            (self.ordinals.get(asin, -1), atom.attribute, atom.value)).fetchall()
        return [dict(zip(('polarity', 'tier', 'source', 'raw'), row)) for row in rows]

    def close(self):
        self._postings.cache_clear()
        self.connection.close()
