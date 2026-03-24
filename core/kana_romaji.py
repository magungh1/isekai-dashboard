"""Katakana/Hiragana to romaji transliteration."""

_KANA_MAP = {
    # Katakana
    'ア': 'a', 'イ': 'i', 'ウ': 'u', 'エ': 'e', 'オ': 'o',
    'カ': 'ka', 'キ': 'ki', 'ク': 'ku', 'ケ': 'ke', 'コ': 'ko',
    'サ': 'sa', 'シ': 'shi', 'ス': 'su', 'セ': 'se', 'ソ': 'so',
    'タ': 'ta', 'チ': 'chi', 'ツ': 'tsu', 'テ': 'te', 'ト': 'to',
    'ナ': 'na', 'ニ': 'ni', 'ヌ': 'nu', 'ネ': 'ne', 'ノ': 'no',
    'ハ': 'ha', 'ヒ': 'hi', 'フ': 'fu', 'ヘ': 'he', 'ホ': 'ho',
    'マ': 'ma', 'ミ': 'mi', 'ム': 'mu', 'メ': 'me', 'モ': 'mo',
    'ヤ': 'ya', 'ユ': 'yu', 'ヨ': 'yo',
    'ラ': 'ra', 'リ': 'ri', 'ル': 'ru', 'レ': 're', 'ロ': 'ro',
    'ワ': 'wa', 'ヲ': 'wo', 'ン': 'n',
    # Dakuten
    'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
    'ザ': 'za', 'ジ': 'ji', 'ズ': 'zu', 'ゼ': 'ze', 'ゾ': 'zo',
    'ダ': 'da', 'ヂ': 'di', 'ヅ': 'du', 'デ': 'de', 'ド': 'do',
    'バ': 'ba', 'ビ': 'bi', 'ブ': 'bu', 'ベ': 'be', 'ボ': 'bo',
    # Handakuten
    'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po',
    # Combo katakana
    'キャ': 'kya', 'キュ': 'kyu', 'キョ': 'kyo',
    'シャ': 'sha', 'シュ': 'shu', 'ショ': 'sho',
    'チャ': 'cha', 'チュ': 'chu', 'チョ': 'cho',
    'ニャ': 'nya', 'ニュ': 'nyu', 'ニョ': 'nyo',
    'ヒャ': 'hya', 'ヒュ': 'hyu', 'ヒョ': 'hyo',
    'ミャ': 'mya', 'ミュ': 'myu', 'ミョ': 'myo',
    'リャ': 'rya', 'リュ': 'ryu', 'リョ': 'ryo',
    'ギャ': 'gya', 'ギュ': 'gyu', 'ギョ': 'gyo',
    'ジャ': 'ja', 'ジュ': 'ju', 'ジョ': 'jo',
    'ビャ': 'bya', 'ビュ': 'byu', 'ビョ': 'byo',
    'ピャ': 'pya', 'ピュ': 'pyu', 'ピョ': 'pyo',
    # Extended katakana
    'ティ': 'ti', 'ディ': 'di', 'デュ': 'dyu',
    'ファ': 'fa', 'フィ': 'fi', 'フェ': 'fe', 'フォ': 'fo',
    'ウィ': 'wi', 'ウェ': 'we', 'ウォ': 'wo',
    'ヴァ': 'va', 'ヴィ': 'vi', 'ヴ': 'vu', 'ヴェ': 've', 'ヴォ': 'vo',
    # Small kana
    'ァ': 'a', 'ィ': 'i', 'ゥ': 'u', 'ェ': 'e', 'ォ': 'o',
    'ャ': 'ya', 'ュ': 'yu', 'ョ': 'yo',
    # Long vowel
    'ー': '-',
    # Sokuon (double consonant)
    'ッ': '*',  # placeholder, handled specially
    # Hiragana
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'wo', 'ん': 'n',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'だ': 'da', 'ぢ': 'di', 'づ': 'du', 'で': 'de', 'ど': 'do',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'っ': '*',
    'ゃ': 'ya', 'ゅ': 'yu', 'ょ': 'yo',
}

# Sort by length descending so multi-char combos match first
_SORTED_KANA = sorted(_KANA_MAP.keys(), key=len, reverse=True)


def to_romaji(text: str) -> str:
    result = []
    i = 0
    while i < len(text):
        matched = False
        for kana in _SORTED_KANA:
            if text[i:i+len(kana)] == kana:
                roma = _KANA_MAP[kana]
                if roma == '*':
                    # Sokuon: double the next consonant
                    # For now just mark it, we'll fix after
                    result.append('*')
                else:
                    result.append(roma)
                i += len(kana)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1

    # Fix sokuon: replace * with the first char of the next syllable
    output = []
    for j, part in enumerate(result):
        if part == '*' and j + 1 < len(result) and result[j + 1]:
            output.append(result[j + 1][0])
        else:
            output.append(part)

    return ''.join(output)


# Katakana ↔ Hiragana conversion (Unicode offset: katakana = hiragana + 0x60)
_KATA_START = 0x30A1  # ァ
_KATA_END = 0x30F6    # ヶ
_HIRA_START = 0x3041  # ぁ
_HIRA_END = 0x3096    # ゖ
_OFFSET = _KATA_START - _HIRA_START  # 0x60

# Special cases not covered by offset
_SPECIAL_KATA_TO_HIRA = {'ー': 'ー'}  # long vowel mark stays
_SPECIAL_HIRA_TO_KATA = {'ー': 'ー'}


def to_hiragana(text: str) -> str:
    result = []
    for ch in text:
        cp = ord(ch)
        if _KATA_START <= cp <= _KATA_END:
            result.append(chr(cp - _OFFSET))
        elif ch in _SPECIAL_KATA_TO_HIRA:
            result.append(_SPECIAL_KATA_TO_HIRA[ch])
        else:
            result.append(ch)
    return ''.join(result)


def to_katakana(text: str) -> str:
    result = []
    for ch in text:
        cp = ord(ch)
        if _HIRA_START <= cp <= _HIRA_END:
            result.append(chr(cp + _OFFSET))
        elif ch in _SPECIAL_HIRA_TO_KATA:
            result.append(_SPECIAL_HIRA_TO_KATA[ch])
        else:
            result.append(ch)
    return ''.join(result)
