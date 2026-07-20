# philostorgia Tekmerion: verification report

Produced by composition_verify.py from philostorgia.db and the
recorded live corpus/rules queries. A failing line blocks publish.

## quote_integrity: PASS
- 44 segments checked, 44 matched

## translation_fidelity: PASS
- 25 blocks; 25 marked trans_ok
- ok  1771192.1: trans_ok (station marks 'Q C T')
- ok  1672066.1: trans_ok (station marks 'Q C T')
- ok  2047647.1: trans_ok (station marks 'Q C T')
- ok  2045970.1: trans_ok (station marks 'Q C T')
- ok  897351.1: trans_ok (station marks 'Q C T')
- ok  910464.1: trans_ok (station marks 'Q C T')
- ok  1691399.1: trans_ok (station marks 'Q C T')
- ok  2120777.1: trans_ok (station marks 'Q C T')
- ok  2121102.1: trans_ok (station marks 'Q C T')
- ok  1694974.1: trans_ok (station marks 'Q C T')
- ok  1545647.1: trans_ok (station marks 'Q C T')
- ok  200388.1: trans_ok (station marks 'Q C T')
- ok  1974146.1: trans_ok (station marks 'Q C T')
- ok  1974158.1: trans_ok (station marks 'Q C T')
- ok  1974182.1: trans_ok (station marks 'Q C T H:NT-Rom-1:31;2Tim-3:3')
- ok  1974215.1: trans_ok (station marks 'Q C T')
- ok  2070684.1: trans_ok (station marks 'Q C T')
- ok  2070841.1: trans_ok (station marks 'Q C T')
- ok  2071049.1: trans_ok (station marks 'Q C T')
- ok  1186233.1: trans_ok (station marks 'Q C T')
- ok  1192009.1: trans_ok (station marks 'Q C T')
- ok  922500.1: trans_ok (station marks 'Q C T')
- ok  1094779.1: trans_ok (station marks 'Q C T')
- ok  319182.1: trans_ok (station marks 'Q C T')
- ok  2059443.1: trans_ok (station marks 'Q C T')

## blacklist_scan: PASS
- 147 patterns x 131 fields scanned

## u2014_scan: PASS
- no U+2014 found

## coverage: PASS
- secondary 6; set-aside 12; station 25
- ok  complete-coverage set 'stoic': all 18 candidates individually dispositioned
- 368 candidates; 43 individually dispositioned; 325 group-set-aside (outside predicate, covered by the chronological/thematic selection)

## catalog_counts: PASS
- witnesses = 25 (ending states 25)
- authors = 17 (ending states 17)
- secondaries = 6 (ending states 6)
- set_asides = 12 (ending states 12)
- earliest_secure = -400 (ending states -400)
- latest = 500 (ending states 500)
- stoa_chapter = 12 (ending states 12)

## period_claims: PASS
- 6 pre-Xenophon (fl<-400) rows; each must be testimonium or set-aside
- ok  979376 Greek Anthology fl -650 [epigram, ch III, set-aside]: pre-Xenophon row accounted for
- ok  744895 Theano of Croton fl -530 [letter, ch III, set-aside]: pre-Xenophon row accounted for
- ok  344155 Heraclitus (Allegorist) fl -504 [commentary, ch III, set-aside]: pre-Xenophon row accounted for
- ok  1924481 Aeschylus the Tragedian fl -499 [dramatic-fragment, ch III, set-aside]: pre-Xenophon row accounted for
- ok  1672066 Antiphon of Athens fl -480 [testimonium, ch I, station]: pre-Xenophon row accounted for
- ok  136035 Aresas of Lucania fl -450 [treatise, ch III, set-aside]: pre-Xenophon row accounted for

## claims_register: PASS
- ok  claim 1: 2 deps present
- ok  claim 2: 6 deps present
- ok  claim 3: 4 deps present
- ok  claim 4: 2 deps present
- ok  claim 5: 2 deps present
- ok  claim 6: 1 deps present
- ok  claim 7: 1 deps present
- ok  claim 8: 1 deps present
- ok  claim 9: 5 deps present
- ok  claim 10: 5 deps present
- ok  claim 11: 5 deps present
- ok  claim 12: 1 deps present

## hand_register: PASS
- 1 HAND-marked stations
- ok  1974182 H:NT-Rom-1:31;2Tim-3:3: disclosed in commentary
