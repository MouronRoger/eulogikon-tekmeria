#!/usr/bin/env python3
"""Generate verified body HTML for philostorgia.html from corpus + DB."""

from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
CORPUS = json.loads((ROOT / "composition_cluster/philostorgia_corpus.json").read_text())
BY_SID = {o["sid"]: o for o in CORPUS["occurrences"]}
EULOGIKON = Path("/Users/james/GitHub/eulogikon")

PAT = re.compile(
    r"φιλοστοργ|φιλόστοργ|ἀφιλόστοργ|φιλοστόργ|Φιλοστοργ|Φιλόστοργ|Ἀφιλόστοργ",
    re.I,
)
APPARATUS = "⟨⟩〈〉†[]"


def resolve_url(wid: str) -> str | None:
    """Resolve canonical work URL from eulogikon DB."""
    try:
        result = subprocess.run(
            [
                str(EULOGIKON / "venv/bin/python"),
                "-c",
                (
                    "from src.core.url_composer import canonical_work_url; "
                    f"print(canonical_work_url('{wid}'))"
                ),
            ],
            env={**dict(__import__("os").environ), "EULOGIKON_STRICT_DB": "1"},
            capture_output=True,
            text=True,
            timeout=20,
            cwd=str(EULOGIKON),
        )
        if result.returncode == 0:
            for line in reversed(result.stdout.strip().split("\n")):
                if line.startswith("http"):
                    return line
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def strip_apparatus(text: str) -> str:
    return "".join(c for c in text if c not in APPARATUS)


def excerpt(text: str, window: int = 140) -> str:
    text = strip_apparatus(text or "")
    match = PAT.search(text)
    if not match:
        return re.sub(r"\s+", " ", text[:280]).strip()
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    out = text[start:end].strip()
    out = re.sub(r"\s+", " ", out)
    if start > 0:
        out = "..." + out
    if end < len(text):
        out = out + "..."
    return out


def fetch_greek(sids: list[int]) -> dict[int, str]:
    conn = psycopg2.connect(dbname="eulogikon", host="localhost", port=5432)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, text_greek FROM eulogikon.units WHERE id = ANY(%s)",
        (sids,),
    )
    rows = {row[0]: row[1] or "" for row in cur.fetchall()}
    cur.close()
    conn.close()
    return rows


def work_link(title: str, wid: str) -> str:
    url = resolve_url(wid)
    t = html.escape(title)
    if url:
        return (
            f'<em><a href="{html.escape(url)}" title="{t} ({wid})">{t}</a></em>'
        )
    return f"<em>{t}</em>"


def witness_ref(author: str, title: str, wid: str, ref: str) -> str:
    return (
        f'<p class="witness-ref">{html.escape(author)}, '
        f"{work_link(title, wid)}, Eulogikon: {html.escape(wid)}, "
        f"ref. {html.escape(ref)}</p>"
    )


def block(
    *,
    label: str | None,
    sublabel: str | None,
    sid: int,
    greek: str,
    translit: str,
    translation: str,
    commentary: str,
) -> str:
    meta = BY_SID[sid]
    parts: list[str] = []
    if label:
        parts.append(f'<p class="entry-label">{html.escape(label)}</p>')
    if sublabel:
        parts.append(f'<p class="entry-sublabel">{html.escape(sublabel)}</p>')
    parts.extend(
        [
            witness_ref(
                meta["author_en"],
                meta["work_en"],
                meta["eul_wid"],
                meta["ref"],
            ),
            f'<blockquote lang="grc" class="grc">{html.escape(greek)}</blockquote>',
            f'<p class="translit"><em>{html.escape(translit)}</em></p>',
            f'<p class="translation">{html.escape(translation)}</p>',
            f"<p>{commentary}</p>",
        ]
    )
    return "\n\n".join(parts)


# Station definitions: (label, sublabel, sid, translit, translation, commentary)
STATIONS: list[tuple[str | None, str | None, int, str, str, str]] = [
    (
        "1. Xenophon of Athens (fl. -400)",
        None,
        2047665,
        "ek tês polylogías ou thrásos diephaíneto, all’ haplótēs kaì philostorgía, hṓst’ epethýmēi án tis éti pleíō autoû akoúein ḗ siōpônti",
        "From his loquacity there appeared no boldness, but simplicity and philostorgia, so that one would desire to hear more of him rather than him being silent.",
        "Direct narrative. The young Cyrus&#x27;s manner of speaking: φιλοστοργία as social charm, warm affectionate candour. Earliest attestation in the corpus.",
    ),
    (
        "2. Aeschylus (fl. -490 to -456)",
        None,
        1924481,
        "philostorgías ... mēdèn hēdù karpoúmenē mēdè chrḗsimon, all’ epipónōs kaì talaipṓrōs anadechoménē",
        "... of philostorgia ... enjoying nothing pleasant nor useful, but taking up [the burden] painfully and laboriously",
        "Fragmentary. Self-sacrificing, laborious devotion: a love that yields no pleasure or utility.",
    ),
    (
        "3. Demades of Paeania (fl. -350 to -320)",
        None,
        1532130,
        "hai thugatéres Erechthéōs tô(i) kalô(i) tês aretês tò thêly tês psychês eníkēsan, kaì tò tês phýseōs asthenès épandron epoíēsen hē pròs tò thrépsan édaphos philostorgía.",
        "The daughters of Erechtheus conquered the feminine of the psychē with the beauty of virtue, and philostorgia toward the nurturing soil made the weakness of physis manly.",
        "Direct oration. φιλοστοργία directed toward one&#x27;s native land: the nurturing bond between a person and their homeland.",
    ),
    (
        "4. Theano of Croton (pseudo-Pythagorean, fl. ca. -350?)",
        None,
        744895,
        "tê(i) dè philostorgía(i) perì tà tékna",
        "... and with philostorgia concerning children",
        "Attributed text. φιλοστοργία as the proper sphere of parental affection for children.",
    ),
    (
        "5. Aresas of Lucania (pseudo-Pythagorean, fl. ca. -300?)",
        None,
        136035,
        "ha dè epithymía philostorgía(i) syngenḕs éassa epharmozei tô(i) nóō(i) ídion peripoiouménā tò hadù",
        "Desire, being akin to philostorgia, fits itself to the nous, procuring for itself what is pleasant as its own.",
        "Attributed text (Doric dialect). ἐπιθυμία is συγγενής (akin/cognate) to φιλοστοργία. In the Pythagorean tripartite psychē, φιλοστοργία is aligned with the desiderative part but works through the νόος.",
    ),
    (
        "6. Hecataeus of Abdera (fl. -320 to -305)",
        None,
        1538679,
        "hetáiras, hês phasi tôn nomarchôn tinas erastàs genoménous dià philostorgían oikodomḗsantas epitelésai koinê(i) tò kataskeúasma",
        "... a courtesan, whom they say some of the nomarchs, having become lovers, through philostorgia jointly completed the construction",
        "Fragment via Diodorus Siculus (transmitting host). φιλοστοργία extended to erotic devotion.",
    ),
    (
        "7. Hermesianax of Cyprus (fl. -290?)",
        None,
        344824,
        "Helikṑn dè dià philostorgían Mousôn endiaítēma",
        "Helicon, through philostorgia of the Muses, [their] dwelling-place",
        "Fragment. The Muses&#x27; love for Mount Helicon.",
    ),
    (
        "8. Polybius of Megalopolis (fl. -160 to -120)",
        None,
        1207876,
        "kaì kathóti téttaraς huiοùς gennḗsasa pròs pántas toúτους anypérblēton diephýlaxe tḕn eúnoian kaì philostorgían méchri tês toû bíou katastrophês",
        "... having borne four sons, she preserved unsurpassed goodwill and philostorgia toward all of them until the end of life",
        "Direct narrative. Polybius describes a mother&#x27;s enduring affection for her sons.",
    ),
    (
        "9. Diodorus Siculus (fl. -60 to -30)",
        None,
        922510,
        "deoménōn dè allḗlōn metà dakrýōn kaì diaphilotimouménōn hypèr eusebeías te kaì philostorgías, sýgkrisín te lambánontos ḗthous philotéknoυ pròs trópon philopátora, synébē toùs lēistàs epiphanéntas amphotérous aneleîn",
        "... as they entreated each other with tears and vied in reverence and philostorgia, a child-loving character set against a father-loving bent, it fell out that the bandits appeared and killed them both",
        "Direct narrative (Posidonius via Diodorus). The Gorgos set-piece: competitive piety and philostorgia between father and son.",
    ),
    (
        "10. Chrysippus of Soli (fl. -240 to -210)",
        "Fragment 292 (sid 2120777) · The definition",
        2120777,
        "agápē dè homónoia àn eíē tôn katà tòn lógon kaì tòn bíon kaì tòn trópon· ḗ synelónti phánai koinōnía bíou· ḗ ekténeia philías kaì philostorgías metà lógou orthoû perì chrêsin hetairōn.",
        "Agapē would be like-mindedness in logos, life, and character; or, to put it concisely, a sharing of life; or an intensity of friendship and philostorgia with right logos concerning the use of companions.",
        "Fragment transmitted by Clement of Alexandria (Stromata 9.41.2). The first philosophical definition of φιλοστοργία in the corpus: a component of ἀγάπη governed by ὀρθὸς λόγος, an ἐκτένεια rather than mere instinct.",
    ),
    (
        None,
        "Fragment 731 (sid 2121102) · Natural only in the virtuous",
        2121102,
        "dokeî dè autoîs kaì goneas sebḗsesthai (scil. toùs spoudaíous) kaì adelphoùs en deutéra(i) moíra(i) metà toùs theoús. phasì dè kaì tḕn pròs tà tékna philostorgían physikḕn eînai autoîs kaì en phaúlois mḕ eînai.",
        "It seems to them that the excellent (σπουδαῖοι) will revere parents and brothers in second honour after the gods. And they say that philostorgia toward children is natural to them and is not present in the base (φαῦλοι).",
        "Doxographical report (transmitted by Stobaeus). φιλοστοργία is natural (φυσική) only in the σπουδαῖοι, not in the φαῦλοι: a moral achievement aligned with correct logos.",
    ),
    (
        "11. Antipater of Tarsus (fl. -180 to -129)",
        "Fragment 62 (sid 1694973) · Excessive philostorgia",
        1694973,
        "eisìn kaì apokeklikótes apò toû symphérontos dià tḕn ágan philostorgían",
        "... some have turned away from the advantageous through excessive philostorgia",
        "Fragment via Stobaeus. Antipater warns that excessive φιλοστοργία can lead one away from what is συμφέρον: the right measure of affection as a function of right logos.",
    ),
    (
        None,
        "Fragment 63 (sid 1694974) · Marriage and blended affection",
        1694974,
        "hai mèn gàr állai philíai ḗ philostorgíai eoíkasi taîs tôn ospíōn ... míxeis, hai d’ andròs kaì gynaikòs ... míxeis di’ holou",
        "... for the other friendships or philostorgiai resemble mixtures set side by side, but those of husband and wife resemble blendings-through-and-through",
        "Fragment via Stobaeus (On Marriage). Antipater distinguishes spousal φιλοστοργία from other bonds: a thorough blending rather than a juxtaposed mixture.",
    ),
    (
        "12. Posidonius of Apameia and Rhodes (fl. -135 to -51)",
        "Fragment 417 (50) (sid 1545691) · Affection for the nurturing land",
        1545691,
        "homōs ouk epilanthánontai tês pròs tḕn thrépsasan gên philostorgías",
        "... nevertheless they do not forget their philostorgia toward the land that nurtured them",
        "Fragment (Const. Exc.). Posidonius on emigrants who retain affection for their homeland despite separation.",
    ),
    (
        None,
        "Customs fragment (sid 1545647) · The Gorgos set-piece",
        1545647,
        "deoménōn dè allḗlōn metà dakrýōn kaì diaphilotimouménōn hypèr eusebeías te kaì philostorgías, sýgkrisín te lambánontos ḗthous philotéknoυ pròs trópon philopátora, synébē toùs lēistàs epiphanéntas amphotérους aneleîn",
        "... as they entreated each other with tears and vied in reverence and philostorgia, a child-loving character set against a father-loving bent, it fell out that the bandits appeared and killed them both",
        "Ethnographic fragment (Stobaeus). Posidonius&#x27;s account of Gorgos of Morgantina: competitive piety and philostorgia between father and son.",
    ),
    (
        "13. Arius Didymus of Alexandria (fl. -50 to 0)",
        None,
        200388,
        "Apò taútēs goûn tês philostorgías kaì diathēkas teleutân mellontas diatíthesthai, kaì tôn éti kyophorouménōn phrontízein",
        "From this philostorgia, indeed, those about to die make wills and take thought for those still in the womb",
        "Doxographical report of Stoic ethics. Arius derives wills and care for the unborn from φιλοστοργία: natural affection grounding social institutions.",
    ),
    (
        "14. Epictetus the Stoic (fl. 90–135)",
        "Discourse 1.11 (sid 1974146) · Natural and reasonable",
        1974146,
        "tò philóstorgon dokeî soi katà phýsin t’ eînai kaì kalón; ... Mḕ toínun máchēn échei tô(i) philostórgō(i) tò eulógiston; ... hó ti àn heurískōmen homoû mèn philóstorgon homoû d’ eulógiston, toûto tharroûntes apophainómetha orthón te eînai kaì kalón",
        "Does the affectionate seem to you to be in accord with physis and good? ... Does the reasonable not conflict with the affectionate? ... whatever we find at once affectionate and at once well-reasoning, this we confidently declare to be right and good",
        "Direct discourse. Epictetus&#x27;s fullest argument: τὸ φιλόστοργον is κατὰ φύσιν and must be εὐλόγιστον; the discourse also uses φιλοστόργως, φιλοστοργέω, and φιλοστοργία in the same unit.",
    ),
    (
        None,
        "Discourse 1.23 (sid 1974158) · Against Epicurus",
        1974158,
        "pôs oûn hyponoētikoí esmen, hoîs mḕ physikḕ ésti pròs tà éngona philostorgía; dià tí aposymbouleúeis tô(i) sophô(i) teknotropheîn;",
        "How then are we suspicious, we who have a natural philostorgia toward offspring? Why do you advise the wise man not to raise children?",
        "Direct discourse. φυσικὴ φιλοστοργία πρὸς τὰ ἔγγονα as a premise against Epicurean withdrawal from family life.",
    ),
    (
        None,
        "Discourse 2.17 (sid 1974182) · The unaffectionate old man",
        1974182,
        "aphilóstorgos gérōn· exerchoménou mou ouk éklausen ... taût’ estì taûta toû philostórgou;",
        "An unaffectionate old man: when I was leaving he did not weep ... are these the marks of the affectionate man?",
        "Direct discourse. ἀφιλόστοργος (privative) marks false φιλοστοργία: sentimental display that conflicts with reason and independence.",
    ),
    (
        None,
        "Discourse 3.17 (sid 1974208) · A man named Philostorgos",
        1974208,
        "kagṑ pot’ eîpon tini aganaktoûnti, hóti Philóstorgos eutycheî, Ḕtheles àn sy metà Soúra koimâsthai;",
        "I once said to someone complaining that Philostorgos is fortunate: Would you want to sleep with Soura?",
        "Direct discourse. Φιλόστοργος here is a personal name (corpus: likely_proper_name), used in an argument about what counts as genuine good fortune.",
    ),
    (
        None,
        "Discourse 3.18 (sid 1974209) · The affectionate father",
        1974209,
        "ésti ti toû patrós sou érgon, hò àn mḕ ekplērṓsē(i), apṓlesen tòn patéra, tòn philóstorgon, tòn hḗmeron",
        "there is some work of your father which, if he does not fulfil it, he loses the father, the affectionate one, the gentle one",
        "Direct discourse. τὸν φιλόστοργον as a moral character-type: affection is part of the role of a father, not an external attachment.",
    ),
    (
        None,
        "Discourse 3.24 (sid 1974215) · The reclamation",
        1974215,
        "gínou philóstorgos hōs taûta tērḗsōn· ei dè dià tḕn philostorgían taútēn ... doûlos mélleis eînai ... eîtá moi kaleîs toûto philostorgían;",
        "Become affectionate as one who will preserve these things. But if through this philostorgia ... you are going to be a slave ... do you call this philostorgia?",
        "Direct discourse. Epictetus reclaims the term: true philostorgia does not enslave; it is compatible with the freedom of προαίρεσις.",
    ),
    (
        "15. Marcus Aurelius (fl. 140–180)",
        "1.9.1 (sid 2070684) · At once passionless and most affectionate",
        2070684,
        "háma mèn apathéstaton eînai, háma dè philostorgótaton",
        "... to be at once most free of passion and at once most affectionate",
        "Direct. Marcus on Sextus of Chaeronea: ἀπαθέστατον and φιλοστοργότατον held together, the Stoic synthesis.",
    ),
    (
        None,
        "1.17.8 (sid 2070701) · An affectionate wife",
        2070701,
        "tò tḕn gynaîka toiaútēn eînai, hoútōsi mèn peithḗnion, hoútō dè philóstorgon, hoútō dè aphelê",
        "... that his wife was such: so obedient, so affectionate, so unaffected",
        "Direct. Marcus gives thanks for a φιλόστοργον wife among the goods of his upbringing.",
    ),
    (
        None,
        "2.5.1 (sid 2070707) · Listed among virtues",
        2070707,
        "... kaì aplástou semnótētos kaì philostorgías kaì eleutherías kaì dikaiotétos prássein",
        "... and to act with unfeigned dignity, and philostorgia, and freedom, and justice",
        "Direct. φιλοστοργία listed among virtues alongside σεμνότης, ἐλευθερία, and δικαιότης.",
    ),
    (
        None,
        "6.30.1 (sid 2070841) · A character to preserve",
        2070841,
        "tḕrēson oûn seautòn ... philóstorgon, errōménen pròs tà préponta érga",
        "... keep yourself ... affectionate, strong for the fitting works",
        "Direct. Marcus exhorts himself to remain φιλόστοργος as part of the philosophical character he must preserve.",
    ),
    (
        None,
        "11.18.4 (sid 2071049) · Affectionately and without gall",
        2071049,
        "allà philostórgōs kaì adḗktōs tê(i) psychê(i)",
        "... but affectionately and without gall in the psychē",
        "Direct. φιλοστόργως paired with ἀδήκτως: affectionate correction of the wrongdoer without bitterness.",
    ),
    (
        "16. Philo of Alexandria (fl. 10–60)",
        None,
        612642,
        "tḕn physikḕn pròs tà tékna philostorgían oîa kritês agathòs eníka tô(i) perì tòn logismòn adekástō(i)",
        "the natural philostorgia toward children, as a good judge, he overcame [bias] through his unwavering reasoning",
        "Direct (Life of Moses). Moses&#x27;s parental φιλοστοργία governed by impartial λογισμός in public affairs.",
    ),
    (
        "17. Nicolaus of Damascus (fl. 60–70)",
        None,
        1709295,
        "autòs hypò philostorgías kaì treîs hetairous pròs toîs doúlois enebíbase",
        "he himself, through philostorgia, brought on board three companions in addition to the five slaves",
        "Historical narrative (Life of Antipater). φιλοστοργία as loyal companionship toward Caesar.",
    ),
    (
        "18. Josephus (fl. 70–90)",
        None,
        1091457,
        "dià tḕn eúnoian kaì tḕn pròs tà oikeía philostorgían",
        "... through goodwill and philostorgia toward kin",
        "Historical narrative (Antiquities). φιλοστοργία toward one&#x27;s own in the manumission law.",
    ),
    (
        "19. Chariton of Aphrodisias (fl. 80–130)",
        None,
        2058609,
        "nikḗsei sōphrosýnēn gynaikòs mētros philostorgía",
        "... a mother&#x27;s philostorgia will overcome [her] chastity",
        "Novelistic (Callirhoe). φιλοστοργία as maternal motive in the romantic plot.",
    ),
    (
        "20. Plutarch of Chaeroneia (fl. 90–120)",
        None,
        1186233,
        "kathólou gàr hē pròs tà éngona philostorgía kaì tà deilà tolmērà poieî kaì philópona tà rháithyma kaì pheidōlà tà gastrímarga",
        "For in general the affection toward offspring makes even the cowardly bold, the lazy hard-working, and the gluttonous sparing.",
        "Philosophical essay (On Affection for Offspring). Plutarch on the power of φιλοστοργία toward offspring across animal nature.",
    ),
    (
        "21. Dio Chrysostom (fl. 70–110)",
        None,
        239782,
        "toùs ge mḕn philostórgous hē synḗtheia",
        "... as for the affectionate, habit [draws them to goodwill]",
        "Rhetorical oration. οἱ φιλόστοργοι as a civic character-type drawn toward εὔνοια.",
    ),
    (
        "22. Lucian of Samosata (fl. 120–180)",
        None,
        529860,
        "kaì tòn nómon élysa tê(i) philostorgía(i)",
        "... and dissolved the law of disinheritance through philostorgia",
        "Satirical (The Renounced). The speaker claims he annulled the law of ἀποκήρυξις through φιλοστοργία, restoring filial duty toward his father.",
    ),
    (
        "23. Athenaeus of Naucratis (fl. 190–210)",
        None,
        1570750,
        "hósēn eléphas tò zôion philostorgían éschen eis paidíon",
        "... how much philostorgia the elephant as an animal had toward a child",
        "Miscellanist (Deipnosophistae, citing Phylarchus). φιλοστοργία extended to animal affection for a human child.",
    ),
    (
        "24. Clement of Alexandria (fl. 180–210)",
        None,
        2124342,
        "hḗ te philanthropía, di’ hḕn kaì hē philostorgía ... hḗ te philostorgía, philotechnía tis oûsa perì stérxin phílōn ḕ oikeíōn",
        "And philanthropia, through which also philostorgia exists ... and philostorgia, being a kind of skill concerning the affection of friends or kin.",
        "Clement quotes and adapts the Chrysippean definition. He redefines φιλοστοργία as φιλοτεχνία τις περὶ στέρξιν: from natural bond to cultivated art of loving.",
    ),
    (
        "25. Iamblichus of Chalcis (fl. 280–325)",
        None,
        1815717,
        "ei deî katháper tàs állas oikeías orexeis, hósai tê(i) philostorgía(i) tê(i) prós ti génos eisin ōnomasménai",
        "If one ought, just as the other proper appetites named after philostorgia toward some class...",
        "Iamblichus uses φιλοστοργία as a template for the philosopher&#x27;s desire for knowledge.",
    ),
    (
        "26. Simplicius of Cilicia (fl. 520–540)",
        None,
        723320,
        "tê(i) tôn goneôn (oîmai) physikê(i) philostorgía(i) tharrḗsantes",
        "... trusting in the natural philostorgia of parents, I think",
        "Commentary. Simplicius reaffirms the Stoic concept of φυσικὴ φιλοστοργία as the ground of filial duty.",
    ),
]


def build_body(greek_by_sid: dict[int, str]) -> str:
    sections: list[str] = [
        "<p>A catalog of every indexed φιλοστοργία attestation in the Eulogikon corpus, arranged chronologically from the classical period through late antiquity. The Stoic core receives full coverage; distribution and absence are noted at the end.</p>",
        "<h2>Earliest attestations (classical period, -400 to -320)</h2>",
        '<p class="chapter-lead">Before any school systematises the term, φιλοστοργία appears in oratory, tragedy, and prose narrative: social warmth, self-sacrificing devotion, and affection for one&#x27;s native land.</p>',
    ]
    section_breaks = {
        744895: ("<h2>Pythagorean uses (4th–3rd c. BCE)</h2>", None),
        1538679: ("<h2>Early Hellenistic and historian uses (-320 to -50)</h2>", None),
        2120777: (
            "<h2>The Stoic core: every citation</h2>",
            '<p class="chapter-lead">Chrysippus defines the term; later Stoics moralise, limit, and reclaim it. The spine runs from definition through natural affection, excess, social institutions, and virtue. Lemma search (form_to_lemma + term_distribution via grc_fold) flags 18 distinct Stoic units across noun, adjective, adverb, verb, and privative forms.</p>',
        ),
        612642: ("<h2>Roman period historians and rhetors (50–200 CE)</h2>", None),
        2124342: ("<h2>Post-Stoic philosophical reception (200–540 CE)</h2>", None),
    }
    stoic_absent = """<h3>Stoic authors confirmed absent</h3>

<p>Zeno of Citium, Cleanthes, Musonius Rufus, and Hierocles the Stoic do not use φιλοστοργία in any indexed text. The term enters Stoicism with Chrysippus and continues through Antipater, Posidonius, Arius Didymus, Epictetus, and Marcus Aurelius.</p>"""

    for station in STATIONS:
        label, sublabel, sid, translit, translation, commentary = station
        if sid in section_breaks:
            heading, lead = section_breaks[sid]
            sections.append(heading)
            if lead:
                sections.append(lead)
        sections.append(
            block(
                label=label,
                sublabel=sublabel,
                sid=sid,
                greek=excerpt(greek_by_sid[sid]),
                translit=translit,
                translation=translation,
                commentary=commentary,
            )
        )
        if sid == 2071049:
            sections.append(stoic_absent)

    sections.extend(
        [
            "<h2>Distribution summary</h2>",
            "<p>The noun φιλοστοργία appears in 20+ authors across 7 centuries (fl. -400 to 540 CE). The adjective φιλόστοργος is well-attested (204 lemma hits across 24 inflected forms). The verb φιλοστοργέω occurs in inflected participial forms (φιλοστοργεῖν, φιλοστοργοῦντες) but not as the dictionary headword. The adverb φιλοστόργως and privative ἀφιλόστοργος appear in the Stoic core (Epictetus, Marcus).</p>",
            "<p>The Stoic contribution is distinctive and consistent across three centuries: φιλοστοργία is natural (φυσική) but only in the virtuous (σπουδαῖοι), not in the base (φαῦλοι), Chrysippus fr. 731. It is governed by ὀρθὸς λόγος (Chrysippus fr. 292), can become excessive and harmful (Antipater), and must be compatible with the freedom of προαίρεσις (Epictetus 3.24). It grounds social institutions (Arius Didymus) and is listed among the virtues (Marcus Aurelius). It is not a mere instinct but a rational affection, a cultivated intensity (ἐκτένεια) of the soul&#x27;s social nature.</p>",
            "<p>The term&#x27;s absence from Aristotle, Plato, and the classical philosophical canon is notable. It emerges in the 4th century BCE and is systematised by the Stoics as a technical ethical term. The Pythagoreans (Theano, Aresas) use it earlier but without the rational-natural framework the Stoics provide.</p>",
            "<p>Closely related terms: στοργή (familial affection), φιλία (friendship), ἀγάπη (love as like-mindedness), and φιλανθρωπία (love of humanity).</p>",
            build_sources_table(),
            '<p style="margin-top: 1em; font-size: 0.9em; color: #718096;"><strong>Note on Eulogikon references.</strong> A work is keyed by its wid; legacy schemes locate text inside a wid. Citation format: Author, <em>Title</em> (Eulogikon: wid, ref), with the title linked to the full text where the work URL resolves from the database.</p>',
        ]
    )
    return "\n\n".join(sections)


def build_sources_table() -> str:
    seen: dict[str, dict[str, Any]] = {}
    for station in STATIONS:
        sid = station[2]
        meta = BY_SID[sid]
        wid = meta["eul_wid"]
        if wid not in seen:
            seen[wid] = {
                "author": meta["author_en"],
                "title": meta["work_en"],
                "wid": wid,
                "refs": [],
            }
        ref = meta["ref"]
        if ref not in seen[wid]["refs"]:
            seen[wid]["refs"].append(ref)

    rows: list[str] = []
    for info in seen.values():
        url = resolve_url(info["wid"])
        title = html.escape(info["title"])
        if url:
            title_cell = f'<em><a href="{html.escape(url)}">{title}</a></em>'
        else:
            title_cell = f"<em>{title}</em>"
        refs = ", ".join(html.escape(r) for r in info["refs"])
        rows.append(
            "<tr>"
            f"<td>{html.escape(info['author'])}</td>"
            f"<td>{title_cell}</td>"
            f"<td>{html.escape(info['wid'])}</td>"
            f"<td>{refs}</td>"
            "</tr>"
        )

    return (
        '<section class="sources-cited">\n'
        "<h2>Sources cited</h2>\n"
        '<div class="table-scroll">\n'
        '<table class="summary sources">\n'
        "<thead><tr><th>Author</th><th>Title</th><th>wid</th>"
        "<th>Passages cited</th></tr></thead>\n"
        f"<tbody>\n{''.join(rows)}\n</tbody>\n"
        "</table>\n</div>\n</section>"
    )


def build_json_ld_citations() -> list[str]:
    wids: list[str] = []
    for station in STATIONS:
        wid = BY_SID[station[2]]["eul_wid"]
        if wid not in wids:
            wids.append(wid)
    urls: list[str] = []
    for wid in wids:
        url = resolve_url(wid)
        if url:
            urls.append(url)
    return urls


def main() -> None:
    sids = [s[2] for s in STATIONS]
    greek_by_sid = fetch_greek(sids)
    body = build_body(greek_by_sid)

    html_path = ROOT / "site_cluster/public/philostorgia.html"
    content = html_path.read_text()
    start = content.index("<p>A catalog of every indexed")
    end = content.index("</section>\n<p style=\"margin-top: 1em")
    new_content = content[:start] + body + content[end + len("</section>") :]

    citations = build_json_ld_citations()
    citation_lines = ",\n    ".join(f'"{u}"' for u in citations)
    new_content = re.sub(
        r'"citation": \[[^\]]*\]',
        f'"citation": [\n    {citation_lines}\n  ]',
        new_content,
        count=1,
    )

    html_path.write_text(new_content)
    print(f"Wrote {html_path} ({len(STATIONS)} stations, {len(citations)} works cited)")


if __name__ == "__main__":
    main()
