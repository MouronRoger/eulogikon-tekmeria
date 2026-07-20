"""Build the SQLite composition store for the philostorgia Tekmerion.

Prototype record set for extended-Tekmerion composition. Two layers solve the
single-shot context problem:

* ``idx`` (light): one narrative summary line per station, in trajectory order.
  Small enough that the whole argument arc stays in context at once.
* ``block`` (heavy): Greek + transliteration + translation + commentary per
  evidence block. Pulled only for the current sliding window (current chunk +
  the overlapping prior chunk).

Chronological chunks of ten let composition of station N read the full ``idx``
plus the heavy blocks of the prior chunk, then append a new ``idx`` line.

Re-runnable: drops and rebuilds every table. QUOTE/CATALOG facts are still
re-verified against the live DB at compose time; this store is working state.
"""

from __future__ import annotations

import datetime as _dt
import pathlib
import sqlite3

HERE = pathlib.Path(__file__).resolve().parent
CANDIDATES = HERE / "philostorgia_candidates.tsv"
DB = HERE / "philostorgia.db"

SCHEMA = """
DROP TABLE IF EXISTS essay;
DROP TABLE IF EXISTS candidate;
DROP TABLE IF EXISTS chapter;
DROP TABLE IF EXISTS station;
DROP TABLE IF EXISTS block;
DROP TABLE IF EXISTS idx;
DROP TABLE IF EXISTS claim;

CREATE TABLE essay (
    id                  INTEGER PRIMARY KEY,
    term                TEXT NOT NULL,
    display_string      TEXT,   -- URL/filename display; identity stays eul_wid
    question            TEXT,
    hinge               TEXT,
    coverage_predicate  TEXT,
    trajectory_type     TEXT,
    created_at          TEXT
);

-- Exhaustive candidate set, one row per unit (mirrors the .tsv, from the
-- recorded grounding query). Discovery input; never the source of printed fact.
CREATE TABLE candidate (
    unit_id       INTEGER PRIMARY KEY,
    wid           TEXT,
    ref           TEXT,
    author        TEXT,
    eul_aid       TEXT,
    affiliation   TEXT,
    period        TEXT,
    domain        TEXT,
    format        TEXT,
    fl_from       INTEGER,
    fl_to         INTEGER,
    title         TEXT,
    token_count   INTEGER,
    length        INTEGER,
    lexical_status TEXT,
    headwords     TEXT
);

-- Chapter plan: one row per movement of the essay.
CREATE TABLE chapter (
    section_no  TEXT PRIMARY KEY,
    title       TEXT,
    shows       TEXT,
    seq_from    INTEGER,
    seq_to      INTEGER
);

-- Curated stations: station | secondary | set-aside, one row per unit.
CREATE TABLE station (
    id            INTEGER PRIMARY KEY,
    seq           INTEGER,          -- trajectory position (NULL for set-aside)
    chunk         INTEGER,          -- group of ten (NULL for set-aside)
    section       TEXT,
    unit_id       INTEGER UNIQUE REFERENCES candidate(unit_id),
    wid           TEXT,
    ref           TEXT,
    author        TEXT,
    fl_from       INTEGER,
    station_type  TEXT,
    disposition   TEXT,             -- station | secondary | set-aside
    reason        TEXT,             -- required for set-aside
    verified      TEXT,             -- Q C T H:<src> marks
    status        TEXT              -- pending | drafted | checked
);

-- Heavy layer: evidence blocks. A station may carry several.
CREATE TABLE block (
    id           INTEGER PRIMARY KEY,
    station_id   INTEGER REFERENCES station(id),
    block_seq    INTEGER,
    framing      TEXT,
    greek        TEXT,
    translit     TEXT,
    translation  TEXT,
    commentary   TEXT,
    quote_ok     INTEGER DEFAULT 0,
    trans_ok     INTEGER DEFAULT 0
);

-- Light layer: the running narrative index (whole arc, held in context).
CREATE TABLE idx (
    seq          INTEGER PRIMARY KEY,
    station_id   INTEGER REFERENCES station(id),
    unit_id      INTEGER,
    citation     TEXT,
    key_phrase   TEXT,
    summary      TEXT
);

CREATE TABLE claim (
    n           INTEGER PRIMARY KEY,
    claim       TEXT,
    depends_on  TEXT,
    section     TEXT,
    status      TEXT
);
"""

ESSAY = (
    1,
    "philostorgia",
    "philostorgia",
    "What did phi\u0301lostorge affection mean before the Stoa, what did the "
    "Stoa do with it, and what became of it afterward?",
    "philostorgia enters the corpus as the name for an instinct that animals "
    "and parents simply have; the Stoa's decisive move is to make that "
    "sub-rational instinct the arche\u0304 from which justice and world-"
    "fellowship are grown; and once that derivation is in place the word "
    "becomes a test: Epictetus asks whether an affection can survive the loss "
    "of its object, and only what survives counts as philostorgia.",
    "authors.affiliation = 'stoic'",
    "chronological (with a thematic Stoa block, then afterlife by domain)",
    _dt.date.today().isoformat(),
)

CHAPTERS = [
    ("I", "The shape of the word",
     "glosses the -storg- root as family-affection (philo\u0301storgos = "
     "philo\u0301teknos); isolates it from e\u0301ro\u0304s / phili\u0301a / "
     "aga\u0301pe\u0304", 1, 2),
    ("II", "Before the Stoa: a natural instinct",
     "shows the word describing spontaneous, by-nature affection in a boy, a "
     "king, horses, catfish, jackdaws, and elders", 3, 9),
    ("III", "The archaic mirage (dating traps)",
     "exposes the metadata's earliest hits as a proper name, pseudepigrapha, "
     "and mis-dated Imperial texts; re-dates first attestation to Xenophon",
     10, 16),
    # Prototype scaffold only. Phase 5 clears this chapter's public title and
    # sets trap rows to set-aside; do not replicate as a reader-facing chapter.
    ("IV", "The Stoa: instinct made the root of justice",
     "files the instinct in the love-taxonomy, denies it to the base, grounds "
     "marriage and city on it, derives kin to city to humanity from it, then "
     "tests it against freedom", 17, 32),
    ("V", "Afterlife: dispersal across domains",
     "carries the word into ethical essay, historiography, medicine, and "
     "lexicon; reports the Stoic derivation from outside",
     33, 38),
    ("VI", "The checkable landscape",
     "recounts the arc (instinct to root to test to dispersal) in counts and "
     "caveats; marks the vice aphilo\u0301storgos", None, None),
]

# (seq, section, unit_id, wid, ref, author, fl_from, station_type,
#  disposition, reason, status)
STATIONS = [
    (1, "I", 1771192, "taq-ac", "phi 518", "Hesychius", 500, "lexicon",
     "station", None, "pending"),
    (2, "I", 1672066, "bqs-ah", "72", "Antiphon of Athens", -480,
     "testimonium", "station", None, "pending"),
    (3, "II", 2047647, "ezq-ag", "Cyr.1.3.2", "Xenophon of Athens", -400,
     "historiography", "station", None, "pending"),
    (4, "II", 2047665, "ezq-ag", "Cyr.1.4.2", "Xenophon of Athens", -400,
     "historiography", "secondary", None, "pending"),
    (5, "II", 2045970, "ezq-ai", "Ages.7.7", "Xenophon of Athens", -400,
     "encomium", "station", None, "pending"),
    (6, "II", 897351, "hgw-av", "HA 611a", "Aristotle", -335,
     "treatise", "station", None, "pending"),
    (7, "II", 897371, "hgw-av", "HA 621a", "Aristotle", -335,
     "treatise", "secondary", None, "pending"),
    (8, "II", 910464, "hki-aa", "3", "Clearchus of Soli", -325,
     "fragment-in-later-author", "station", None, "pending"),
    (9, "II", 1691399, "ffk-bm", "Leg.931.b", "Plato of Athens", -390,
     "treatise", "station", None, "pending"),
    (10, "III", 979376, "ajg-aa", "book 194.1", "Greek Anthology", -650,
     "epigram", "set-aside", "proper-name (Philosto\u0301rgios); metadata "
     "'earliest' trap, reported", "pending"),
    (11, "III", 744895, "bhc-aa", "199", "Theano of Croton", -530,
     "letter", "secondary", "dating trap: pseudo-Pythagorean, labelled -530 "
     "but Hellenistic/Roman", "pending"),
    (12, "III", 136035, "dck-aa", "50", "Aresas of Lucania", -450,
     "treatise", "secondary", "dating trap: pseudo-Pythagorean Doric, late",
     "pending"),
    (13, "III", 344155, "bko-aa", "1 4", "Heraclitus (Allegorist)", -504,
     "commentary", "secondary", "dating trap: Homeric Allegorist, really "
     "1st c. AD, mis-dated -504", "pending"),
    (14, "III", 198622, "hgw-bf", "Phgn 809b", "ps.-Aristotle", -335,
     "treatise", "secondary", "dating trap: spurious Physiognomics",
     "pending"),
    (15, "III", 910544, "hki-aa", "73", "Clearchus of Soli", -325,
     "fragment-in-later-author", "secondary", None, "pending"),
    (16, "III", 1924481, "emo-ag", "book 274(?)b.28.2",
     "Aeschylus the Tragedian", -499, "dramatic-fragment", "secondary",
     "bare fragment; poetic token only", "pending"),
    (17, "IV", 2120777, "kms-ae", "292", "Chrysippus of Soli", -240,
     "fragment-in-later-author", "station", None, "pending"),
    (18, "IV", 2121102, "kms-ae", "731", "Chrysippus of Soli", -240,
     "doxography", "station", None, "pending"),
    (19, "IV", 1694974, "lcc-aa", "63", "Antipater of Tarsus", -180,
     "fragment-in-later-author", "station", None, "pending"),
    (20, "IV", 1694973, "lcc-aa", "62", "Antipater of Tarsus", -180,
     "fragment-in-later-author", "secondary", None, "pending"),
    (21, "IV", 1545647, "msa-ac", "1052 003.2a,87,F.108r",
     "Posidonius of Apameia", -110, "fragment-in-later-author", "station",
     None, "pending"),
    (22, "IV", 200388, "nac-aa", "87,2", "Arius Didymus", -53,
     "doxography", "station", None, "pending"),
    (23, "IV", 1974146, "ojw-ac", "1.11", "Epictetus the Stoic", 90,
     "dialogue", "station", None, "pending"),
    (24, "IV", 1974158, "ojw-ac", "1.23", "Epictetus the Stoic", 90,
     "dialogue", "station", None, "pending"),
    (25, "IV", 1974182, "ojw-ac", "2.17", "Epictetus the Stoic", 90,
     "dialogue", "station", None, "pending"),
    (26, "IV", 1974209, "ojw-ac", "3.18", "Epictetus the Stoic", 90,
     "dialogue", "secondary", None, "pending"),
    (27, "IV", 1974215, "ojw-ac", "3.24", "Epictetus the Stoic", 90,
     "dialogue", "station", None, "pending"),
    (28, "IV", 2070684, "qpy-aa", "1.9.1", "Marcus Aurelius", 161,
     "self-address", "station", None, "pending"),
    (29, "IV", 2070841, "qpy-aa", "6.30.1", "Marcus Aurelius", 161,
     "self-address", "station", None, "pending"),
    (30, "IV", 2071049, "qpy-aa", "11.18.4", "Marcus Aurelius", 161,
     "self-address", "station", None, "pending"),
    (31, "IV", 2070701, "qpy-aa", "1.17.8", "Marcus Aurelius", 161,
     "self-address", "secondary", None, "pending"),
    (32, "IV", 2070707, "qpy-aa", "2.5.1", "Marcus Aurelius", 161,
     "self-address", "secondary", None, "pending"),
    (33, "V", 1186233, "okg-cg", "494 C", "Plutarch of Chaeronea", 70,
     "treatise", "station", None, "pending"),
    (34, "V", 1192009, "okg-as", "963 A", "Plutarch of Chaeronea", 70,
     "dialogue", "station", None, "pending"),
    (35, "V", 922500, "nde-ac", "34/35 4 2", "Diodorus of Sicily", -60,
     "historiography", "station", None, "pending"),
    (36, "V", 1094779, "ofq-ad", "AJ.16.11", "Josephus the Historian", 37,
     "historiography", "station", None, "pending"),
    (37, "V", 319182, "qmm-dt", "1 576", "Galen of Pergamon", 129,
     "medical-treatise", "station", None, "pending"),
    (None, "V", 2059443, "qya-ac", "10.94.1", "Clement of Alexandria", 180,
     "protreptic", "set-aside", "theological content (divine paternity); "
     "Clement's ordinary-sense uses remain eligible, this passage is doctrine",
     "pending"),
    # Set-asides inside the complete-coverage set (reported in the piece).
    (None, "IV", 1545691, "msa-ab", "417 (50)", "Posidonius of Apameia",
     -110, "fragment-in-later-author", "set-aside",
     "corrupted-unit (627 KB concatenation); tokens survive via Diodorus",
     "pending"),
    (None, "IV", 2124338, "qya-ah", "9.41.2", "Clement of Alexandria", 180,
     "fragment-in-later-author", "set-aside",
     "duplicate-station of 2120777 (Chrysippus, preserved here)", "pending"),
    (None, "V", 922510, "nde-ac", "34/35 11 1", "Diodorus of Sicily", -60,
     "historiography", "set-aside",
     "duplicate-station of 1545647 (Posidonius Gorgos fragment)", "pending"),
    (None, "IV", 1974208, "ojw-ac", "3.17", "Epictetus the Stoic", 90,
     "dialogue", "set-aside", "proper-name (Philo\u0301storgos, a person)",
     "pending"),
    (None, "V", 2030884, "wus-au", "\u03c6 527", "Suda", 950,
     "lexicon", "set-aside", "proper-name (Philosto\u0301rgios the church "
     "historian)", "pending"),
]

# unit_id -> (key_phrase, summary), in trajectory order via the station seq.
INDEX = {
    1771192: ("\u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03c2\u00b7 \u03c6\u03b9\u03bb\u03cc\u03c4\u03b5\u03ba\u03bd\u03bf\u03c2",
              "glosses the adjective as 'child-loving', fixing the family-"
              "affection core the essay will test"),
    1672066: ("\u03b1\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1, \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1, \u03c3\u03c4\u03bf\u03c1\u03b3\u03ae",
              "sets the noun in the -storg- triad, isolating family-affection "
              "from e\u0301ro\u0304s and phili\u0301a"),
    2047647: ("\u03c6\u03cd\u03c3\u03b5\u03b9 \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03c2 \u1f64\u03bd",
              "earliest secure prose token: the boy Cyrus, affectionate by "
              "physis, greets his grandfather"),
    2047665: ("\u1f01\u03c0\u03bb\u03cc\u03c4\u03b7\u03c2 \u03ba\u03b1\u1f76 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1",
              "reinforces: Cyrus's talk shows guilelessness and affection, "
              "not boldness"),
    2045970: ("\u03c4\u1f78 \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd \u03ba\u03b1\u1f76 \u03b8\u03b5\u03c1\u03b1\u03c0\u03b5\u03c5\u03c4\u03b9\u03ba\u1f78\u03bd \u03c4\u1ff6\u03bd \u03c6\u03af\u03bb\u03c9\u03bd",
              "transfers the warmth from kin to friends: the king's "
              "affectionateness"),
    897351: ("\u03c4\u1f78 \u03c4\u1ff6\u03bd \u1f35\u03c0\u03c0\u03c9\u03bd \u03b3\u03ad\u03bd\u03bf\u03c2 \u03b5\u1f36\u03bd\u03b1\u03b9 \u03c6\u03cd\u03c3\u03b5\u03b9 \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd",
             "makes the affection zoological, by physis: horses as a kind "
             "are affectionate"),
    897371: ("\u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03cc\u03c1\u03b3\u03c9\u03c2 \u03bc\u03ad\u03bd\u03b5\u03b9 \u03c0\u03c1\u1f78\u03c2 \u03c4\u03bf\u1fd6\u03c2 \u1ff7\u03bf\u1fd6\u03c2",
             "extends the instinct to fish: the male catfish guards the spawn "
             "affectionately"),
    910464: ("\u03b4\u03b9\u1f70 \u03c4\u1f74\u03bd \u03c6\u03c5\u03c3\u03b9\u03ba\u1f74\u03bd \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03bd",
             "names it 'natural affection' in jackdaws, the register the Stoa "
             "will inherit"),
    1691399: ("\u03c0\u03b1\u1fd6\u03b4\u03b5\u03c2 \u03c0\u03b1\u03af\u03b4\u03c9\u03bd \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u1fe6\u03bd\u03c4\u03b5\u03c2",
              "gives the one classical legislative use: grandchildren "
              "honouring aged elders"),
    979376: ("\u0393\u03c1\u03ac\u03bc\u03bc\u03b1\u03c4\u03b1 \u03b4\u03ce\u03b4\u03b5\u03ba\u2019 \u1f14\u03c7\u03b5\u03b9 \u03a6\u03b9\u03bb\u03bf\u03c3\u03c4\u03cc\u03c1\u03b3\u03b9\u03bf\u03c2",
             "trap: the '-650' hit is the proper name Philosto\u0301rgios in a "
             "letter-count epigram"),
    744895: ("\u03c4\u1fc7 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u1fb3 \u03c0\u03b5\u03c1\u1f76 \u03c4\u1f70 \u03c4\u03ad\u03ba\u03bd\u03b1",
             "trap: a letter labelled -530 already uses the developed sense, "
             "betraying a late date"),
    136035: ("\u1f10\u03c0\u03b9\u03b8\u03c5\u03bc\u03af\u03b1 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u1fb3 \u03c3\u03c5\u03b3\u03b3\u03b5\u03bd\u1f74\u03c2",
             "trap: pseudo-Pythagorean Doric treatise, Hellenistic under a "
             "-450 name"),
    344155: ("\u1f10\u03bd\u03b7\u03b3\u03ba\u03ac\u03bb\u03b9\u03c3\u03c4\u03b1\u03b9 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03cc\u03c1\u03b3\u03c9\u03c2",
             "trap: the Homeric Allegorist, really 1st c. AD, mis-dated -504"),
    198622: ("\u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd \u03c0\u03c1\u1f78\u03c2 \u1f03 \u1f02\u03bd \u1f41\u03bc\u03b9\u03bb\u03ae\u03c3\u1fc3",
             "trap: the spurious Physiognomics makes the lion affectionate"),
    910544: ("\u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u1ff6\u03c3\u03af \u03c4\u03b5 ... \u03c0\u03c1\u03bf\u03c3\u03af\u03c9\u03c3\u03b9 \u03c4\u03bf\u1fd6\u03c2 \u03b3\u03ac\u03bc\u03bf\u03b9\u03c2",
             "secondary: Spartan custom shames bachelors into affection and "
             "marriage"),
    1924481: ("\u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03c2",
              "secondary: the earliest poetic token, but a bare fragment"),
    2120777: ("\u03c6\u03b9\u03bb\u03bf\u03c4\u03b5\u03c7\u03bd\u03af\u03b1 \u03c4\u03b9\u03c2 \u03bf\u1f56\u03c3\u03b1 \u03c0\u03b5\u03c1\u1f76 \u03c3\u03c4\u03ad\u03c1\u03be\u03b9\u03bd \u03c6\u03af\u03bb\u03c9\u03bd \u1f22 \u03bf\u1f30\u03ba\u03b5\u03af\u03c9\u03bd",
              "files philostorgia into the love-taxonomy beside aga\u0301pe\u0304 "
              "and philanthro\u0304pi\u0301a (preserved by Clement)"),
    2121102: ("\u03c6\u03c5\u03c3\u03b9\u03ba\u1f74\u03bd \u03b5\u1f36\u03bd\u03b1\u03b9 ... \u1f10\u03bd \u03c6\u03b1\u03cd\u03bb\u03bf\u03b9\u03c2 \u03bc\u1f74 \u03b5\u1f36\u03bd\u03b1\u03b9",
              "makes it of physis and moralises it: present in the wise, "
              "absent in the base"),
    1694974: ("\u1f04\u03b3\u03b5\u03c5\u03c3\u03c4\u03bf\u03bd ... \u03c4\u1fc6\u03c2 \u1f00\u03bb\u03b7\u03b8\u03b9\u03bd\u03c9\u03c4\u03ac\u03c4\u03b7\u03c2 \u03b5\u1f50\u03bd\u03bf\u03af\u03b1\u03c2",
              "grounds marriage and city on it: the unmarried man never "
              "tastes truest goodwill"),
    1694973: ("\u03b4\u03b9\u1f70 \u03c4\u1f74\u03bd \u1f04\u03b3\u03b1\u03bd \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03bd",
              "secondary: parents' excess affection can warp judgment; the "
              "instinct needs governance"),
    1545647: ("\u1f51\u03c0\u1f72\u03c1 \u03b5\u1f50\u03c3\u03b5\u03b2\u03b5\u03af\u03b1\u03c2 \u03c4\u03b5 \u03ba\u03b1\u1f76 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03c2",
              "raises it to the heroic bond: father and son die contending "
              "in affection (via Diodorus)"),
    200388: ("\u1f08\u03c0\u1f78 \u03c4\u03b1\u03cd\u03c4\u03b7\u03c2 ... \u03c4\u1fc6\u03c2 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03c2 ... \u03c0\u03c1\u1f78\u03c2 \u03c0\u03ac\u03bd\u03c4\u03b1\u03c2 \u1f00\u03bd\u03b8\u03c1\u03ce\u03c0\u03bf\u03c5\u03c2",
             "KEYSTONE: derives kin to city to humanity from philostorgia as "
             "arche\u0304 (the oikeio\u0304sis ladder)"),
    1974146: ("\u1f21 \u03bc\u03ae\u03c4\u03b7\u03c1 \u03b4\u2019 \u03bf\u1f50 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03b5\u1fd6 \u03c4\u1f78 \u03c0\u03b1\u03b9\u03b4\u03af\u03bf\u03bd;",
              "opens the test: fleeing the sick child is not what the "
              "affection does; instinct and reason must agree"),
    1974158: ("\u03c6\u03c5\u03c3\u03b9\u03ba\u1f74 ... \u03c0\u03c1\u1f78\u03c2 \u03c4\u1f70 \u1f14\u03b3\u03b3\u03bf\u03bd\u03b1 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1",
              "defends the natural bond against Epicurus's 'don't rear "
              "children'"),
    1974182: ("\u1f00\u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03c2 \u03b3\u03ad\u03c1\u03c9\u03bd",
              "unmasks the counterfeit: tears at parting are not what the "
              "affectionate person is"),
    1974209: ("\u03c4\u1f78\u03bd \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd, \u03c4\u1f78\u03bd \u1f25\u03bc\u03b5\u03c1\u03bf\u03bd",
              "secondary: names the affection among goods a father forfeits "
              "by failing his e\u0301rgon"),
    1974215: ("\u03bf\u1f50 \u03bb\u03c5\u03c3\u03b9\u03c4\u03b5\u03bb\u03b5\u1fd6 \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd \u03b5\u1f36\u03bd\u03b1\u03b9",
              "the turn: be affectionate only so as to stay free; love a "
              "person as mortal (ho\u0304s thne\u0304to\u0301n)"),
    2070684: ("\u1f05\u03bc\u03b1 \u1f00\u03c0\u03b1\u03b8\u03ad\u03c3\u03c4\u03b1\u03c4\u03bf\u03bd ... \u1f05\u03bc\u03b1 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03cc\u03c4\u03b1\u03c4\u03bf\u03bd",
              "reconciles the paradox: most passionless and most affectionate "
              "at once"),
    2070841: ("\u03c4\u03ae\u03c1\u03b7\u03c3\u03bf\u03bd ... \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd",
              "issues the self-command to stay affectionate, with Antoninus "
              "as model"),
    2071049: ("\u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03cc\u03c1\u03b3\u03c9\u03c2 \u03ba\u03b1\u1f76 \u1f00\u03b4\u03ae\u03ba\u03c4\u03c9\u03c2",
              "extends it to the wrongdoer (me\u0301, te\u0301knon), closing the "
              "ladder at all humanity"),
    2070701: ("\u03bf\u1f55\u03c4\u03c9 \u03b4\u1f72 \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03bd",
              "secondary: thanks the gods for an affectionate wife"),
    2070707: ("\u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03c2",
              "secondary: lists affection among the dispositions for each "
              "act"),
    1186233: ("\u1f21 \u03c0\u03c1\u1f78\u03c2 \u03c4\u1f70 \u1f14\u03b3\u03b3\u03bf\u03bd\u03b1 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1",
              "titles a whole treatise with the word: phy\u0301sis works the "
              "philo\u0301storgon into mothers; it makes cowards bold"),
    1192009: ("\u1f00\u03c1\u03c7\u1f74\u03bd ... \u03ba\u03bf\u03b9\u03bd\u03c9\u03bd\u03af\u03b1\u03c2 \u03ba\u03b1\u1f76 \u03b4\u03b9\u03ba\u03b1\u03b9\u03bf\u03c3\u03cd\u03bd\u03b7\u03c2",
              "reports the Stoic derivation from outside: they make it the "
              "origin of fellowship and justice"),
    922500: ("\u03c4\u1fc6\u03c2 \u03c0\u03c1\u1f78\u03c2 \u03c4\u1f74\u03bd \u03b8\u03c1\u03ad\u03c8\u03b1\u03c3\u03b1\u03bd \u03b3\u1fc6\u03bd \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u03b1\u03c2",
             "widens it from household to homeland, even in 'barbarian' souls "
             "(Posidonian)"),
    1094779: ("\u03c4\u1fc7 \u03c4\u03bf\u1fe6 \u03b3\u03b5\u03b3\u03b5\u03bd\u03bd\u03b7\u03ba\u03ad\u03bd\u03b1\u03b9 \u03c6\u03b9\u03bb\u03bf\u03c3\u03c4\u03bf\u03c1\u03b3\u03af\u1fb3",
              "moves it into dynastic narrative: Herod's paternal affection"),
    319182: ("\u03b5\u1f54\u03b8\u03c5\u03bc\u03bf\u03c2, \u03c6\u03b9\u03bb\u03cc\u03c3\u03c4\u03bf\u03c1\u03b3\u03bf\u03c2, \u03c6\u03b9\u03bb\u03ac\u03bd\u03b8\u03c1\u03c9\u03c0\u03bf\u03c2",
             "makes it a humoral marker: the best-tempered body yields the "
             "affectionate character"),
}

CLAIMS = [
    (1, "-storg- names family-affection specifically",
     "1771192,1672066", "I", "verified"),
    (2, "earliest real attestation is Xenophon, not the archaic labels",
     "2047647,979376,744895,136035,344155,198622", "II/III", "verified"),
    (3, "pre-Stoic sense is a zoological instinct by physis",
     "2047647,897351,897371,910464", "II", "verified"),
    (4, "Chrysippus files it in the love-taxonomy; natural but absent in the "
        "base", "2120777,2121102", "IV", "verified"),
    (5, "Antipater grounds household and city on it",
     "1694974,1694973", "IV", "verified"),
    (6, "Posidonius: the bond unto death",
     "1545647", "IV", "verified"),
    (7, "Arius Didymus derives the social/cosmopolitan order from it as "
        "arche\u0304 (keystone)", "200388", "IV", "verified"),
    (8, "Plutarch reports that Stoic derivation from outside",
     "1192009", "V", "verified"),
    (9, "Epictetus turns the word into a test: affection that enslaves is "
        "not philostorgia", "1974215,1974146,1974158,1974182,1974209", "IV",
     "verified"),
    (10, "Marcus makes it a virtue of character, reconciled with apatheia, "
         "extended to the wrongdoer",
     "2070684,2070841,2071049,2070707,2070701", "IV", "verified"),
    (11, "afterlife dispersion across domains",
     "922500,1094779,319182,1771192,2059443", "V", "verified"),
    (12, "aphilo\u0301storgos marks the vice (in-corpus Epictetus 2.17; "
         "NT Rom 1:31 / 2 Tim 3:3 as HAND parallel)",
     "1974182", "V/VI", "verified"),
]


def load_candidates(cur: sqlite3.Cursor) -> int:
    """Load the exhaustive candidate rows from the recorded .tsv."""
    rows: list[tuple[object, ...]] = []
    with CANDIDATES.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            if line.startswith("unit_id\t"):
                continue
            parts = line.split("\t")
            if len(parts) < 16:
                parts += [""] * (16 - len(parts))
            uid = int(parts[0])
            fl_from = int(parts[9]) if parts[9] not in ("", "None") else None
            fl_to = int(parts[10]) if parts[10] not in ("", "None") else None
            tok = int(parts[12]) if parts[12] not in ("", "None") else None
            length = int(parts[13]) if parts[13] not in ("", "None") else None
            aff = None if parts[5] in ("", "None") else parts[5]
            rows.append((uid, parts[1], parts[2], parts[3], parts[4], aff,
                         parts[6], parts[7], parts[8], fl_from, fl_to,
                         parts[11], tok, length, parts[14], parts[15]))
    cur.executemany(
        "INSERT INTO candidate VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    return len(rows)


def main() -> None:
    """Create the schema and populate every table except heavy blocks."""
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    cur.executescript(SCHEMA)

    cur.execute(
        "INSERT INTO essay VALUES (?,?,?,?,?,?,?,?)", ESSAY
    )
    cur.executemany(
        "INSERT INTO chapter VALUES (?,?,?,?,?)", CHAPTERS
    )
    n_cand = load_candidates(cur)

    station_id: dict[int, int] = {}
    for st in STATIONS:
        (seq, section, unit_id, wid, ref, author, fl_from, stype,
         disp, reason, status) = st
        chunk = None if seq is None else ((seq - 1) // 10) + 1
        cur.execute(
            "INSERT INTO station (seq, chunk, section, unit_id, wid, ref, "
            "author, fl_from, station_type, disposition, reason, verified, "
            "status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (seq, chunk, section, unit_id, wid, ref, author, fl_from, stype,
             disp, reason, "", status),
        )
        station_id[unit_id] = cur.lastrowid

    for st in STATIONS:
        seq, _, unit_id = st[0], st[1], st[2]
        if seq is None or unit_id not in INDEX:
            continue
        key_phrase, summary = INDEX[unit_id]
        wid, ref, author = st[3], st[4], st[5]
        citation = f"{author}, {ref} ({wid})"
        cur.execute(
            "INSERT INTO idx (seq, station_id, unit_id, citation, key_phrase, "
            "summary) VALUES (?,?,?,?,?,?)",
            (seq, station_id[unit_id], unit_id, citation, key_phrase, summary),
        )

    cur.executemany(
        "INSERT INTO claim VALUES (?,?,?,?,?)", CLAIMS
    )

    con.commit()

    counts = {
        "candidates": n_cand,
        "stations_total": len(STATIONS),
        "stations_block": cur.execute(
            "SELECT COUNT(*) FROM station WHERE disposition='station'"
        ).fetchone()[0],
        "secondary": cur.execute(
            "SELECT COUNT(*) FROM station WHERE disposition='secondary'"
        ).fetchone()[0],
        "set_aside": cur.execute(
            "SELECT COUNT(*) FROM station WHERE disposition='set-aside'"
        ).fetchone()[0],
        "index_lines": cur.execute("SELECT COUNT(*) FROM idx").fetchone()[0],
        "chapters": len(CHAPTERS),
        "claims": len(CLAIMS),
    }
    con.close()
    print(f"built {DB}")
    for key, val in counts.items():
        print(f"  {key}: {val}")


if __name__ == "__main__":
    main()
