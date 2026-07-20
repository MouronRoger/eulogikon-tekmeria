"""Phase 4 writer for the philostorgia Tekmerion composition store.

Holds the per-witness evidence blocks (the heavy layer) as data and writes
them into ``philostorgia.db``. Runs *after* ``composition_build_store.py`` has
laid the scaffold (essay, chapters, candidates, stations, idx, claims); this
module fills the ``block`` table and flips ``station.status`` and records the
``station.verified`` marks per Phase 4.8 of the tekmerion skill.

The ``.db`` itself is gitignored working state, so this committed module is the
durable, rebuildable record of the composition's judgment work. It is
idempotent and chunk-incremental: it manages exactly the ``unit_id`` keys that
appear in ``BLOCKS`` / ``STATION_MARKS`` / ``IDX_FIXES`` below, deleting and
re-inserting their blocks on each run, so re-running after adding a chunk never
duplicates rows.

Provenance discipline (tekmerion skill):

* Every ``greek`` field is an *exact substring* of ``eulogikon.units.text_greek``
  fetched fresh by ``unit_id`` at compose time (QUOTE). Where the stored unit
  carries a digitisation artifact (a split trailing letter, e.g. the Hesychius
  and Antiphon lexicon/testimonium units), the artifact is preserved verbatim
  in the Greek so the substring match stays honest, and disclosed in the
  eventual corpus-boundaries section.
* Titles, wids, refs, and URLs are CATALOG: resolved by query this session
  (recorded in the verification report), never from the survey JSON.
* English-field formatting: ``STYLE.md`` § Formatting cross-check.
  Composition-only boundaries: ``composition_cluster/prose_rules.md``.
  The ``blacklist_physis_nature`` rule forbids English "nature" / "by nature";
  use *physis* / by *physis* in commentary and translations (transliteration
  lines may keep case forms that mirror the Greek, e.g. ``phýsei`` for φύσει).
"""

from __future__ import annotations

import pathlib
import sqlite3
from typing import NamedTuple

HERE = pathlib.Path(__file__).resolve().parent
DB = HERE / "philostorgia.db"


class Block(NamedTuple):
    """One evidence block: framing plus the four record fields of the heavy layer.

    Attributes:
        framing: Local frame above the citation (author, station kind, hook).
        greek: Verbatim excerpt, an exact substring of the unit's text_greek.
        translit: ALA-LC transliteration (references/transliteration.md).
        translation: English, warrant-checked against the Greek excerpt.
        commentary: What the line does on the page, in doing-verbs.
    """

    framing: str
    greek: str
    translit: str
    translation: str
    commentary: str


class Mark(NamedTuple):
    """Per-station verification marks and status, set at draft time.

    Attributes:
        verified: Space-joined marks (Q quote, C catalog, T translation
            warrant, H:<src> hand-supplied).
        status: Station state (``pending`` | ``drafted`` | ``checked``).
    """

    verified: str
    status: str


# unit_id -> ordered evidence blocks. Only station-disposition units carry
# blocks; secondaries are projected inline from their idx line, set-asides are
# reported in prose (both get verification marks below but no block row).
BLOCKS: dict[int, list[Block]] = {
    # seq 1 - Hesychius, phi 518 (taq-ac), lexicon. Split-sigma artifact kept.
    1771192: [
        Block(
            framing="",
            greek="φιλόστοργο ς· φιλότεκνος.",
            translit="philóstorgos· philóteknos",
            translation="affectionate: child-loving.",
            commentary=(
                "Late lexicography does not elaborate: affectionate means "
                "child-loving, as if that were the whole story. Whatever else "
                "the word will come to mean, it starts in the nursery."
            ),
        )
    ],
    # seq 2 - Antiphon, fr. 72 (bqs-ah), testimonium via Ammonius.
    1672066: [
        Block(
            framing="",
            greek="ἀστοργί α , φιλοστοργί α , στοργ ή· Ἀ.",
            translit="astorgía, philostorgía, storgḗ· A.",
            translation=(
                "want of affection, philostorgia, family-love: so Antiphon."
            ),
            commentary=(
                "Three words from one root, offered as near-synonyms: the "
                "lack, the affection, the family-love itself. Greek keeps "
                "-storg- as its own affective household beside desire and "
                "friendship."
            ),
        )
    ],
    # seq 3 - Xenophon, Cyropaedia 1.3.2 (ezq-ag), historiography.
    2047647: [
        Block(
            framing="",
            greek=(
                "εὐθὺς οἷα δὴ παῖς φύσει φιλόστοργος ὢν ἠσπάζετό τε αὐτὸν "
                "ὥσπερ ἂν εἴ τις πάλαι συντεθραμμένος καὶ πάλαι φιλῶν "
                "ἀσπάζοιτο"
            ),
            translit=(
                "euthùs hoîa dḕ paîs phýsei philóstorgos ṑn ēspázetó te autòn "
                "hṓsper àn eí tis pálai syntethramménos kaì pálai philôn "
                "aspázoito"
            ),
            translation=(
                "at once, being just the sort of child who is affectionate by "
                "physis, he greeted him as one long brought up with him and "
                "long loving would greet."
            ),
            commentary=(
                "The earliest secure prose witness is a boy's greeting, not a "
                "definition: affectionate by physis, shown in how Cyrus greets "
                "his grandfather as one long loved would greet. No school "
                "doctrine attaches to the word yet."
            ),
        )
    ],
    # seq 5 - Xenophon, Agesilaus 7.7 (ezq-ai), encomium.
    2045970: [
        Block(
            framing="",
            greek=(
                "τὸ μὲν μεγάλαυχον οὐκ εἶδέ τις, τὸ δὲ φιλόστοργον καὶ "
                "θεραπευτικὸν τῶν φίλων καὶ μὴ ζητῶν κατενόησεν ἄν."
            ),
            translit=(
                "tò mèn megálauchon ouk eîdé tis, tò dè philóstorgon kaì "
                "therapeutikòn tôn phílōn kaì mḕ zētôn katenóēsen án."
            ),
            translation=(
                "no one saw the boastful in him, but even without looking one "
                "would have marked the affectionate and friend-tending toward "
                "his friends."
            ),
            commentary=(
                "The same writer praises a Spartan king for what anyone could "
                "see without looking: not boastfulness, but warmth toward "
                "friends carried over from the household. Affection becomes a "
                "mark of good rule."
            ),
        )
    ],
    # seq 6 - Aristotle, History of Animals 611a (hgw-av), treatise.
    897351: [
        Block(
            framing="",
            greek=(
                "Καὶ ὅλως γε δοκεῖ τὸ τῶν ἵππων γένος εἶναι φύσει "
                "φιλόστοργον. Σημεῖον δέ· πολλάκις γὰρ αἱ στέριφαι "
                "ἀφαιρούμεναι τὰς μητέρας τὰ πωλία αὐταὶ στέργουσι, διὰ δὲ τὸ "
                "μὴ ἔχειν γάλα διαφθείρουσιν."
            ),
            translit=(
                "Kaì hólōs ge dokeî tò tôn híppōn génos eînai phýsei "
                "philóstorgon. Sēmeîon dé· pollákis gàr hai stériphai "
                "aphairoúmenai tàs mētéras tà pōlía autaì stérgousi, dià dè tò "
                "mḕ échein gála diaphtheírousin."
            ),
            translation=(
                "And in general the horse kind seems to be affectionate by "
                "physis. A sign of it: often the barren mares, taking the "
                "foals from their mothers, love them themselves, but through "
                "not having milk destroy them."
            ),
            commentary=(
                "Aristotle widens the register from court to stable: horses are "
                "affectionate by physis. Barren mares adopt foals and love "
                "them, even when lack of milk destroys what they cherish. The "
                "word names observed instinct, not yet a virtue."
            ),
        )
    ],
    # seq 8 - Clearchus of Soli, fr. 3 (hki-aa), fragment via Athenaeus.
    910464: [
        Block(
            framing="",
            greek=(
                "καὶ τοῖς κολοιοῖς δὲ διὰ τὴν φυσικὴν φιλοστοργίαν, καίπερ "
                "τοσοῦτον πανουργίᾳ διαφέρουσιν, ὅμως ὅταν ἐλαίου κρατὴρ τεθῇ "
                "πλήρης, οἱ στάντες αὐτῶν ἐπὶ τὸ χεῖλος καὶ καταβλέψαντες ἐπὶ "
                "τὸν ἐμφαινόμενον καταράττουσιν."
            ),
            translit=(
                "kaì toîs koloioîs dè dià tḕn physikḕn philostorgían, kaíper "
                "tosoûton panourgía(i) diaphérousin, hómōs hótan elaíou kratḕr "
                "tethê(i) plḗrēs, hoi stántes autôn epì tò cheîlos kaì "
                "katablépsantes epì tòn emphainómenon kataráttousin."
            ),
            translation=(
                "and the jackdaws too, because of their affection by physis, "
                "clever as they are, still, when a bowl full of oil is set out, "
                "those of them that stand on the rim and look down at what "
                "appears plunge down."
            ),
            commentary=(
                "Clearchus adds jackdaws: clever birds undone by affection when "
                "they dive at a companion reflected in oil. The trait is "
                "sociable instinct, not merely parental, and the Stoa will "
                "inherit that language of affection by physis."
            ),
        )
    ],
    1691399: [
        Block(
            framing="",
            greek=(
                "ὅπουπερ πόλις εὐνομοῦσα εὐδαιμονεῖ, τούτους οἱ παῖδες παίδων "
                "φιλοστοργοῦντες ζῶσι μεθ’ ἡδονῆς"
            ),
            translit=(
                "hópouper pólis eunomoûsa eudaimoneî, toútous hoi paîdes "
                "paídōn philostorgoûntes zôsi meth᾽ hēdonês"
            ),
            translation=(
                "wherever a well-lawed city flourishes, these, with their "
                "children's children affectionate toward them, live with "
                "pleasure."
            ),
            commentary=(
                "Plato ties the word to legislation: where law and happiness "
                "hold, grandchildren live affectionately toward their elders. "
                "Household warmth already has a civic face before the Stoa "
                "names it the root of justice."
            ),
        )
    ],
    # seq 17 - Chrysippus, Moral Fragments fr. 292 (kms-ae), preserved by
    # Clement (parallel unit qya-ah). The love-taxonomy under agápē.
    2120777: [
        Block(
            framing="",
            greek=(
                "παράκειται δὲ τῇ ἀγάπῃ ἥ τε φιλοξενία ... ἥ τε φιλοστοργία "
                "φιλοτεχνία τις οὖσα περὶ στέρξιν φίλων ἢ οἰκείων."
            ),
            translit=(
                "parákeitai dè tê(i) agápē(i) hḗ te philoxenía ... hḗ te "
                "philostorgía, philotechnía tis oûsa perì stérxin phílōn ḕ "
                "oikeíōn."
            ),
            translation=(
                "beside agape stands both hospitality ... and philostorgia, "
                "being a fond expertise concerned with the cherishing of friends "
                "or kin."
            ),
            commentary=(
                "Chrysippus, preserved by Clement, files philostorgia beside "
                "agape and hospitality: a fond expertise in cherishing friends "
                "or kin. The nursery instinct has become a named skill in the "
                "school's love-taxonomy."
            ),
        )
    ],
    # seq 18 - Chrysippus, Moral Fragments fr. 731 (kms-ae), doxography (DL).
    2121102: [
        Block(
            framing="",
            greek=(
                "φασὶ δὲ καὶ τὴν πρὸς τὰ τέκνα φιλοστοργίαν φυσικὴν εἶναι "
                "αὐτοῖς καὶ ἐν φαύλοις μὴ εἶναι."
            ),
            translit=(
                "phasì dè kaì tḕn pròs tà tékna philostorgían physikḕn eînai "
                "autoîs kaì en phaúlois mḕ eînai."
            ),
            translation=(
                "and they say that the philostorgia toward children is of "
                "physis for them, and does not exist in the base."
            ),
            commentary=(
                "The school report moralises what Xenophon and Aristotle "
                "observed: affection toward children is of physis for the wise "
                "and absent in the base. Horses and jackdaws no longer share "
                "the word on equal terms."
            ),
        )
    ],
    # seq 19 - Antipater of Tarsus, On Marriage fr. 63 (lcc-aa), via Stobaeus.
    1694974: [
        Block(
            framing="",
            greek=(
                "τὸν μὴ πεῖραν ἐσχηκότα γαμετῆς γυναικὸς καὶ τέκνων ἄγευστον "
                "εἶναι τῆς ἀληθινωτάτης καὶ γνησίου εὐνοίας ... αἱ μὲν γὰρ "
                "ἄλλαι φιλίαι ἢ φιλοστοργίαι ἐοίκασι ταῖς τῶν ὀσπρίων ἤ τινων "
                "ἄλλων παραπλησίων κατὰ τὰς παραθέσεις μίξεσιν, αἱ δ’ ἀνδρὸς "
                "καὶ γυναικὸς ταῖς δι’ ὅλων κράσεσιν"
            ),
            translit=(
                "tòn mḕ peîran eschēkóta gametês gynaikòs kaì téknōn ágeuston "
                "eînai tês alēthinōtátēs kaì gnēsíou eunoías ... hai mèn gàr "
                "állai philíai ḕ philostorgíai eoíkasi taîs tôn ospríōn ḗ "
                "tinōn állōn paraplēsíōn katà tàs parathéseis míxesin, hai d᾽ "
                "andròs kaì gynaikòs taîs di᾽ hólōn krásesin"
            ),
            translation=(
                "the man who has had no experience of wedded wife and children "
                "is untasting of the truest and most genuine goodwill ... for "
                "the other friendships or affections resemble the mixtures of "
                "pulses or the like set side by side, but those of husband and "
                "wife resemble blendings-through-and-through."
            ),
            commentary=(
                "Antipater grounds the household on the word: other friendships "
                "and affections lie side by side like pulses in a dish; "
                "husband and wife blend through-and-through. philostorgia "
                "does the structural work marriage needs."
            ),
        )
    ],
    # seq 21 - Posidonius, On Customs and Wars (msa-ac), via Diodorus.
    1545647: [
        Block(
            framing="",
            greek=(
                "δεομένων δὲ ἀλλήλων μετὰ δακρύων καὶ διαφιλοτιμουμένων ὑπὲρ "
                "εὐσεβείας τε καὶ φιλοστοργίας, σύγκρισίν τε λαμβάνοντος ἤθους "
                "φιλοτέκνου πρὸς τρόπον φιλοπάτορα, συνέβη τοὺς ληιστὰς "
                "ἐπιφανέντας ἀμφοτέρους ἀνελεῖν."
            ),
            translit=(
                "deoménōn dè allḗlōn metà dakrýōn kaì diaphilotimouménōn hypèr "
                "eusebeías te kaì philostorgías, sýnkrisín te lambánontos "
                "ḗthous philotéknou pròs trópon philopátora, synébē toùs "
                "lē(i)stàs epiphanéntas amphotérous aneleîn."
            ),
            translation=(
                "as they entreated each other with tears and vied in reverence "
                "and affection, a child-loving character set against a "
                "father-loving bent, it fell out that the bandits appeared and "
                "killed them both."
            ),
            commentary=(
                "In Diodorus's Sicilian narrative, father and son each refuse "
                "the one horse that could save him; they die contending in "
                "reverence and affection. The household word rises to heroic "
                "pitch at the point of death."
            ),
        )
    ],
    # seq 22 - Arius Didymus (nac-aa), doxography. THE KEYSTONE.
    200388: [
        Block(
            framing="",
            greek=(
                "Ἀπὸ ταύτης γοῦν τῆς φιλοστοργίας ... Εἰ δὲ πρὸς τοὺς πολίτας "
                "φιλίαν δι’ αὑτὴν αἱρετήν, ἀναγκαῖον εἶναι καὶ τὴν πρὸς "
                "ὁμοεθνεῖς καὶ ὁμοφύλους, ὥστε καὶ τὴν πρὸς πάντας ἀνθρώπους."
            ),
            translit=(
                "Apò taútēs goûn tês philostorgías ... Ei dè pròs toùs polítas "
                "philían di᾽ hautḕn hairetḗn, anankaîon eînai kaì tḕn pròs "
                "homoethneîs kaì homophýlous, hṓste kaì tḕn pròs pántas "
                "anthrṓpous."
            ),
            translation=(
                "from this affection, then, ... And if friendship toward "
                "fellow-citizens is choiceworthy for its own sake, then "
                "necessarily also that toward those of the same people and "
                "same stock, and so also that toward all human beings."
            ),
            commentary=(
                "The keystone: from parental affection outward, the school "
                "derives kin, fellow-citizens, same people, same stock, and "
                "finally all human beings. The boy's greeting and the mare's "
                "foal become the starting-point of fellowship and justice."
            ),
        )
    ],
    # seq 23 - Epictetus, Discourses 1.11 (ojw-ac), dialogue.
    1974146: [
        Block(
            framing="",
            greek=(
                "τὸ φιλόστοργον δοκεῖ σοι κατὰ φύσιν τ’ εἶναι καὶ καλόν; ... "
                "ἡ μήτηρ δ’ οὐ φιλοστοργεῖ τὸ παιδίον; ... ὅ τι ἂν εὑρίσκωμεν "
                "ὁμοῦ μὲν φιλόστοργον ὁμοῦ δ’ εὐλόγιστον, τοῦτο θαρροῦντες "
                "ἀποφαινόμεθα ὀρθόν τε εἶναι καὶ καλόν;"
            ),
            translit=(
                "tò philóstorgon dokeî soi katà phýsin t᾽ eînai kaì kalón? ... "
                "hē mḗtēr d᾽ ou philostorgeî tò paidíon? ... hó ti àn "
                "heurískōmen homoû mèn philóstorgon homoû d᾽ eulógiston, toûto "
                "tharroûntes apophainómetha orthón te eînai kaì kalón?"
            ),
            translation=(
                "does the affectionate seem to you to be in accord with physis "
                "and good? ... but does the mother not feel affection for the "
                "little child? ... whatever we find at once affectionate and at "
                "once well-reasoning, this we confidently declare to be right "
                "and good?"
            ),
            commentary=(
                "Epictetus cross-examines an official who fled his sick "
                "daughter. Affection is by physis and good, he grants; mother, "
                "nurse, and tutor feel it. Only what is at once affectionate and "
                "well-reasoning counts as right. Flight fails the test."
            ),
        )
    ],
    # seq 24 - Epictetus, Discourses 1.23 (ojw-ac), dialogue (vs Epicurus).
    1974158: [
        Block(
            framing="",
            greek=(
                "πῶς οὖν ὑπονοητικοί ἐσμεν, οἷς μὴ φυσικὴ ἔστι πρὸς τὰ ἔγγονα "
                "φιλοστοργία; ... μὴ ἀναιρώμεθα τέκνα"
            ),
            translit=(
                "pôs oûn hyponoētikoí esmen, hoîs mḕ physikḕ ésti pròs tà "
                "éngona philostorgía? ... mḕ anairṓmetha tékna"
            ),
            translation=(
                "how then are we creatures of mere suspicion, in whom there is "
                "no affection by physis toward our offspring? ... let us not "
                "rear children."
            ),
            commentary=(
                "Against Epicurus on rearing children, Epictetus treats "
                "affection toward offspring as a datum of physis: even sheep "
                "and wolves do not abandon their young. A school may not "
                "legislate the instinct away."
            ),
        )
    ],
    # seq 25 - Epictetus, Discourses 2.17 (ojw-ac), dialogue (the vice-word).
    1974182: [
        Block(
            framing="",
            greek=(
                "ἀφιλόστοργος γέρων· ἐξερχομένου μου οὐκ ἔκλαυσεν ... ταῦτ’ "
                "ἔστι τὰ τοῦ φιλοστόργου;"
            ),
            translit=(
                "aphilóstorgos gérōn· exerchoménou mou ouk éklausen ... taût᾽ "
                "ésti tà toû philostórgou?"
            ),
            translation=(
                "'an unaffectionate old man: when I was leaving he did not "
                "weep' ... are these the marks of the affectionate man?"
            ),
            commentary=(
                "Epictetus quotes a complaint about an unaffectionate old man "
                "who did not weep at parting, then refuses it: withholding "
                "tears is not what belongs to the affectionate man. The "
                "privative names the counterfeit; the same word will echo in "
                "the New Testament vice lists (Rom 1:31; 2 Tim 3:3), outside "
                "this corpus."
            ),
        )
    ],
    # seq 27 - Epictetus, Discourses 3.24 (ojw-ac), dialogue. THE TURN.
    1974215: [
        Block(
            framing="",
            greek=(
                "Πῶς οὖν γένωμαι φιλόστοργος; ... Ὡς γενναῖος, ὡς εὐτυχής ... "
                "οὕτως μοι γίνου φιλόστοργος ὡς ταῦτα τηρήσων ... οὐ λυσιτελεῖ "
                "φιλόστοργον εἶναι. καὶ τί κωλύει φιλεῖν τινα ὡς θνητόν, ὡς "
                "ἀποδημητικόν;"
            ),
            translit=(
                "Pôs oûn génōmai philóstorgos? ... Hōs gennaîos, hōs eutychḗs "
                "... hoútōs moi gínou philóstorgos hōs taûta tērḗsōn ... ou "
                "lysiteleî philóstorgon eînai. kaì tí kōlýei phileîn tina hōs "
                "thnētón, hōs apodēmētikón?"
            ),
            translation=(
                "How then am I to become affectionate? As a noble man, as a "
                "fortunate one ... be affectionate in such a way as will keep "
                "these things safe ... it does not profit to be affectionate. "
                "And what prevents loving someone as mortal, as one who may "
                "depart?"
            ),
            commentary=(
                "How to become affectionate without becoming a slave to "
                "affection: love as one who may depart, keep freedom intact, "
                "do not let affection that enslaves profit. The name is "
                "conservative; the test is not."
            ),
        )
    ],
    # seq 28 - Marcus Aurelius, To Himself 1.9.1 (qpy-aa), self-address.
    2070684: [
        Block(
            framing="",
            greek=(
                "τὸ μηδὲ ἔμφασίν ποτε ὀργῆς ἢ ἄλλου τινὸς πάθους παρασχεῖν, "
                "ἀλλὰ ἅμα μὲν ἀπαθέστατον εἶναι, ἅμα δὲ φιλοστοργότατον"
            ),
            translit=(
                "tò mēdè émphasín pote orgês ḕ állou tinòs páthous parascheîn, "
                "allà háma mèn apathéstaton eînai, háma dè philostorgótaton"
            ),
            translation=(
                "and never to give a sign of anger or of any other passion, "
                "but to be at once most free of passion and at once most "
                "affectionate."
            ),
            commentary=(
                "Marcus holds up Sextus as at once most free of passion and "
                "most affectionate. The Stoic reconciliation in one breath: "
                "philostorgia beside freedom from passion, not against it."
            ),
        )
    ],
    # seq 29 - Marcus Aurelius, To Himself 6.30.1 (qpy-aa), self-address.
    2070841: [
        Block(
            framing="",
            greek=(
                "τήρησον οὖν σεαυτὸν ἁπλοῦν, ἀγαθόν, ἀκέραιον, σεμνόν, ἄκομψον, "
                "τοῦ δικαίου φίλον, θεοσεβῆ, εὐμενῆ, φιλόστοργον, ἐρρωμένον "
                "πρὸς τὰ πρέποντα ἔργα."
            ),
            translit=(
                "tḗrēson oûn seautòn haploûn, agathón, akéraion, semnón, "
                "ákompson, toû dikaíou phílon, theosebê, eumenê, philóstorgon, "
                "errōménon pròs tà préponta érga."
            ),
            translation=(
                "keep yourself, then, simple, good, unmixed, dignified, "
                "unaffected, a friend of the just, reverent toward the gods, "
                "kindly, affectionate, strong for the fitting works."
            ),
            commentary=(
                "In a string of self-commands, Marcus tells himself to stay "
                "affectionate among the traits a good man guards: simple, "
                "just, reverent, kindly, strong for the fitting works."
            ),
        )
    ],
    # seq 30 - Marcus Aurelius, To Himself 11.18.4 (qpy-aa), self-address.
    2071049: [
        Block(
            framing="",
            greek=(
                "μή, τέκνον· πρὸς ἄλλο πεφύκαμεν ... ἀλλὰ φιλοστόργως καὶ "
                "ἀδήκτως τῇ ψυχῇ"
            ),
            translit=(
                "mḗ, téknon· pròs állo pephýkamen ... allà philostórgōs kaì "
                "adḗktōs tê(i) psychê(i)"
            ),
            translation=(
                "no, child: we were born for something else ... but "
                "affectionately and without gall in the psyche."
            ),
            commentary=(
                "Marcus addresses a wrongdoer as child and commands himself "
                "to respond affectionately and without gall in the psyche. "
                "Parental language reaches the stranger who harms you."
            ),
        )
    ],
    # seq 33 - Plutarch, On Affection for Offspring 494 C (okg-cg), treatise.
    1186233: [
        Block(
            framing="",
            greek=(
                "καθόλου γὰρ ἡ πρὸς τὰ ἔγγονα φιλοστοργία καὶ τὰ δειλὰ τολμηρὰ "
                "ποιεῖ καὶ φιλόπονα τὰ ῥᾴθυμα καὶ φειδωλὰ τὰ γαστρίμαργα·"
            ),
            translit=(
                "kathólou gàr hē pròs tà éngona philostorgía kaì tà deilà "
                "tolmērà poieî kaì philópona tà rhá(i)thyma kaì pheidōlà tà "
                "gastrímarga·"
            ),
            translation=(
                "for in general the affection toward offspring makes even the "
                "cowardly bold, the lazy hard-working, and the gluttonous "
                "sparing."
            ),
            commentary=(
                "Plutarch titles a treatise with the word and states its power "
                "in one line: affection toward offspring makes cowards bold, "
                "the lazy industrious, the greedy sparing. He reads the "
                "instinct up from animals into human parents."
            ),
        )
    ],
    # seq 34 - Plutarch, Whether Land or Water Animals Are Wiser 963 A
    # (okg-as), treatise reporting the Stoics from outside.
    1192009: [
        Block(
            framing="",
            greek=(
                "τὴν γοῦν πρὸς τὰ ἔγγονα φιλοστοργίαν ἀρχὴν μὲν ἡμῖν "
                "κοινωνίας καὶ δικαιοσύνης τιθέμενοι, πολλὴν δὲ τοῖς ζῴοις καὶ "
                "ἰσχυρὰν ὁρῶντες παροῦσαν ... οὔ φασιν αὐτοῖς οὐδ’ ἀξιοῦσι "
                "μετεῖναι δικαιοσύνης"
            ),
            translit=(
                "tḕn goûn pròs tà éngona philostorgían archḕn mèn hēmîn "
                "koinōnías kaì dikaiosýnēs tithémenoi, pollḕn dè toîs zṓois kaì "
                "ischyràn horôntes paroûsan ... oú phasin autoîs oud᾽ axioûsi "
                "meteînai dikaiosýnēs"
            ),
            translation=(
                "setting the affection toward offspring as the starting-point "
                "of fellowship and justice for us, yet seeing it present, "
                "strong and abundant, in the animals ... they refuse to grant "
                "that the animals have any share in justice."
            ),
            commentary=(
                "Plutarch reports the Stoic move from outside: affection toward "
                "offspring as starting-point of fellowship and justice, then "
                "asks the cost. The same philostorgia is strong in animals; "
                "either animals share in justice or the derivation fails."
            ),
        )
    ],
    # seq 35 - Diodorus of Sicily 34/35.4.2 (nde-ac), historiography
    # (Posidonian).
    922500: [
        Block(
            framing="",
            greek=(
                "καὶ βαρβάρων ψυχαὶ θηριώδεις, ὅταν ἡ τύχη διαζευγνύῃ τὸ "
                "σύνηθες ἀπὸ τῆς πατρίδος, ὅμως οὐκ ἐπιλανθάνονται τῆς πρὸς "
                "τὴν θρέψασαν γῆν φιλοστοργίας."
            ),
            translit=(
                "kaì barbárōn psychaì thēriṓdeis, hótan hē týchē diazeugnýē(i) "
                "tò sýnēthes apò tês patrídos, hómōs ouk epilanthánontai tês "
                "pròs tḕn thrépsasan gên philostorgías."
            ),
            translation=(
                "even barbarians, beast-like in psyche, when fortune severs "
                "them from the familiarity of their fatherland, still do not "
                "forget their affection toward the land that nourished them."
            ),
            commentary=(
                "Even men whose psyche is beast-like remember affection for "
                "the land that nourished them when fortune severs them from "
                "home. The parental image widens to the fatherland."
            ),
        )
    ],
    # seq 36 - Josephus, Jewish Antiquities 16.11 (ofq-ad), historiography.
    1094779: [
        Block(
            framing="",
            greek=(
                "ὁ βασιλεὺς τῇ τοῦ γεγεννηκέναι φιλοστοργίᾳ καὶ τιμῆς ἧς ἔδει "
                "μετεδίδου καὶ γυναῖκας ἐν ἡλικίᾳ γεγονόσιν ἐζεύγνυεν"
            ),
            translit=(
                "ho basileùs tê(i) toû gegennēkénai philostorgía(i) kaì timês "
                "hês édei metedídou kaì gynaîkas en hēlikía(i) gegonósin "
                "ezeúgnyen"
            ),
            translation=(
                "the king, out of the affection of one who had begotten them, "
                "gave them a share of the honour due and joined them, now come "
                "of age, to wives."
            ),
            commentary=(
                "Herod marries his sons and shares honour with them out of "
                "a father's affection. The word is ordinary historiographical "
                "vocabulary, here with dynastic stakes."
            ),
        )
    ],
    # seq 37 - Galen, On Temperaments 1.576 (qmm-dt), treatise (medical).
    319182: [
        Block(
            framing="",
            greek=(
                "ὡσαύτως δὲ καὶ τῇ ψυχῇ μέσος ἀκριβῶς ἐστι θρασύτητός τε καὶ "
                "δειλίας ... εἴη δ’ ἂν ὁ τοιοῦτος εὔθυμος, φιλόστοργος, "
                "φιλάνθρωπος, συνετός."
            ),
            translit=(
                "hōsaútōs dè kaì tê(i) psychê(i) mésos akribôs esti thrasýtētós "
                "te kaì deilías ... eíē d᾽ àn ho toioûtos eúthymos, "
                "philóstorgos, philánthrōpos, synetós."
            ),
            translation=(
                "likewise in the psyche too he is exactly in the mean between "
                "rashness and cowardice ... such a man would be good-spirited, "
                "affectionate, humane, intelligent."
            ),
            commentary=(
                "Galen makes affection a humoral marker: the man in the mean "
                "between rashness and cowardice is good-spirited, affectionate, "
                "humane, intelligent. Character follows blended temperament."
            ),
        )
    ],
    # seq 38 - Clement of Alexandria, Exhortation 10.94.1 (qya-ac), treatise.
    2059443: [
        Block(
            framing="",
            greek=(
                "ὁ δὲ φιλόστοργος οὗτος ἡμῶν πατήρ, ὁ ὄντως πατήρ, οὐ παύεται "
                "προτρέπων, νουθετῶν, παιδεύων, φιλῶν·"
            ),
            translit=(
                "ho dè philóstorgos hoûtos hēmôn patḗr, ho óntōs patḗr, ou "
                "paúetai protrépōn, nouthetôn, paideúōn, philôn·"
            ),
            translation=(
                "and this affectionate father of ours, the father who really "
                "is, does not cease exhorting, admonishing, teaching, loving."
            ),
            commentary=(
                "Clement redirects the household word: our affectionate father "
                "is God, who never ceases exhorting, teaching, and loving. "
                "Family affection reaches divine paternity at the far edge of "
                "this corpus."
            ),
        )
    ],
}

# unit_id -> verification marks + status. Covers every chunk-1 station row:
# stations (with blocks), secondaries (projected inline), set-asides (reported).
STATION_MARKS: dict[int, Mark] = {
    1771192: Mark("Q C T", "drafted"),
    1672066: Mark("Q C T", "drafted"),
    2047647: Mark("Q C T", "drafted"),
    2045970: Mark("Q C T", "drafted"),
    897351: Mark("Q C T", "drafted"),
    910464: Mark("Q C T", "drafted"),
    1691399: Mark("Q C T", "drafted"),
    2047665: Mark("Q C", "drafted"),  # secondary
    897371: Mark("Q C", "drafted"),  # secondary
    979376: Mark("Q C", "drafted"),  # set-aside (proper-name trap, reported)
    # chunk 2
    2120777: Mark("Q C T", "drafted"),
    2121102: Mark("Q C T", "drafted"),
    1694974: Mark("Q C T", "drafted"),
    744895: Mark("Q C", "drafted"),  # secondary (dating trap: pseudo-Theano)
    136035: Mark("Q C", "drafted"),  # secondary (dating trap: pseudo-Aresas)
    344155: Mark("Q C", "drafted"),  # secondary (dating trap: Allegorist)
    198622: Mark("Q C", "drafted"),  # secondary (dating trap: ps.-Aristotle)
    910544: Mark("Q C", "drafted"),  # secondary (Clearchus fr. 73)
    1924481: Mark("Q C", "drafted"),  # secondary (Aeschylus bare fragment)
    1694973: Mark("Q C", "drafted"),  # secondary (Antipater fr. 62)
    # chunk 3
    1545647: Mark("Q C T", "drafted"),
    200388: Mark("Q C T", "drafted"),
    1974146: Mark("Q C T", "drafted"),
    1974158: Mark("Q C T", "drafted"),
    1974182: Mark("Q C T H:NT-Rom-1:31;2Tim-3:3", "drafted"),
    1974215: Mark("Q C T", "drafted"),
    2070684: Mark("Q C T", "drafted"),
    2070841: Mark("Q C T", "drafted"),
    2071049: Mark("Q C T", "drafted"),
    1974209: Mark("Q C", "drafted"),  # secondary (Epictetus 3.18)
    # chunk 4
    1186233: Mark("Q C T", "drafted"),
    1192009: Mark("Q C T", "drafted"),
    922500: Mark("Q C T", "drafted"),
    1094779: Mark("Q C T", "drafted"),
    319182: Mark("Q C T", "drafted"),
    2059443: Mark("Q C T", "drafted"),
    2070701: Mark("Q C", "drafted"),  # secondary (Marcus 1.17.8)
    2070707: Mark("Q C", "drafted"),  # secondary (Marcus 2.5.1)
    # set-asides (no seq; reported in prose, no block row). Dispositioned by
    # catalog: C where the disposition is resolved by query; Q added where the
    # -storg- token string was itself confirmed present in text_greek (proving a
    # duplicate token or a proper-name hit), verified live this session.
    922510: Mark("Q C", "drafted"),  # duplicate-station of 1545647 (Posidonius)
    1545691: Mark("C", "drafted"),  # corrupted-unit (627 KB concatenation)
    1974208: Mark("Q C", "drafted"),  # proper-name (Philóstorgos, a person)
    2030884: Mark("C", "drafted"),  # proper-name (Philostórgios; accented στόργ)
    2124338: Mark("Q C", "drafted"),  # duplicate-station of 2120777 (Chrysippus)
}

# unit_id -> corrected idx key_phrase (accent/diacritic mismatches with the
# live text_greek found at fetch time; the light layer must match the DB for
# any phrase that may be projected inline).
IDX_FIXES: dict[int, str] = {
    2047647: "φύσει φιλόστοργος ὢν",  # was ...ὤν (acute); DB has grave ὢν
    897371: "φιλοστόργως μένει πρὸς τοῖς ᾠοῖς",  # was ...ῷοῖς; DB has ᾠοῖς
    744895: "φιλοστοργίᾳ περὶ τὰ τέκνα",  # was τῇ φιλοστοργίᾳ...; DB has τῇ δὲ
}

# unit_id -> corrected idx summary. The scaffold's index lines rendered φύσις as
# "nature" / "by nature" (blacklist_physis_nature, CRITICAL); repunctuated per
# prose_rules.md (*physis*, by *physis*). Caught by Phase 6 blacklist scan.
IDX_SUMMARY_FIXES: dict[int, str] = {
    2047647: (
        "earliest secure prose token: the boy Cyrus, affectionate by physis, "
        "greets his grandfather"
    ),
    897351: (
        "makes the affection zoological, by physis: horses as a kind are "
        "affectionate"
    ),
    2121102: (
        "makes it of physis and moralises it: present in the wise, absent in "
        "the base"
    ),
    2070841: (
        "issues a self-command to stay affectionate, with Antoninus as model"
    ),
    2047665: (
        "Cyrus's talk shows guilelessness and affection, not boldness"
    ),
    897371: (
        "extends the instinct to fish: the male catfish guards the spawn "
        "affectionately"
    ),
    1694973: (
        "parents' excess affection can warp judgment; the instinct needs "
        "governance"
    ),
    1974209: (
        "names affection among the goods a father forfeits by failing his work"
    ),
    2070701: (
        "thanks the gods for an affectionate wife"
    ),
    2070707: (
        "lists affection among the dispositions for each act"
    ),
}


def _ensure_framing_column(cur: sqlite3.Cursor) -> None:
    """Add ``block.framing`` if the store predates the craft pass."""
    cols = {row[1] for row in cur.execute("PRAGMA table_info(block)")}
    if "framing" not in cols:
        cur.execute("ALTER TABLE block ADD COLUMN framing TEXT")


def _station_id(cur: sqlite3.Cursor, unit_id: int) -> int:
    """Return the station row id for a unit, raising if it is absent."""
    row = cur.execute(
        "SELECT id FROM station WHERE unit_id = ?", (unit_id,)
    ).fetchone()
    if row is None:
        raise KeyError(f"no station row for unit_id {unit_id}")
    return int(row[0])


def write_blocks(con: sqlite3.Connection) -> tuple[int, int]:
    """Write blocks, verification marks, and idx fixes for managed units.

    Idempotent: deletes and re-inserts every managed unit's blocks. Returns the
    count of block rows written and station rows updated.
    """
    cur = con.cursor()
    _ensure_framing_column(cur)
    n_blocks = 0
    for unit_id, blocks in BLOCKS.items():
        sid = _station_id(cur, unit_id)
        cur.execute("DELETE FROM block WHERE station_id = ?", (sid,))
        for seq, blk in enumerate(blocks, start=1):
            cur.execute(
                "INSERT INTO block (station_id, block_seq, framing, greek, "
                "translit, translation, commentary) VALUES (?,?,?,?,?,?,?)",
                (sid, seq, blk.framing, blk.greek, blk.translit,
                 blk.translation, blk.commentary),
            )
            n_blocks += 1

    for unit_id, mark in STATION_MARKS.items():
        cur.execute(
            "UPDATE station SET verified = ?, status = ? WHERE unit_id = ?",
            (mark.verified, mark.status, unit_id),
        )

    for unit_id, key_phrase in IDX_FIXES.items():
        cur.execute(
            "UPDATE idx SET key_phrase = ? WHERE unit_id = ?",
            (key_phrase, unit_id),
        )

    for unit_id, summary in IDX_SUMMARY_FIXES.items():
        cur.execute(
            "UPDATE idx SET summary = ? WHERE unit_id = ?",
            (summary, unit_id),
        )

    con.commit()
    return n_blocks, len(STATION_MARKS)


def main() -> None:
    """Write the drafted blocks into the store and report the counts."""
    if not DB.exists():
        raise SystemExit(
            f"{DB} missing; run composition_build_store.py first"
        )
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        n_blocks, n_marks = write_blocks(con)
    finally:
        con.close()
    print(f"wrote {n_blocks} blocks; updated {n_marks} station rows")


if __name__ == "__main__":
    main()
