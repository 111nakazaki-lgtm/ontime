#!/usr/bin/env python3
"""既存の「物件概要書」PDFを、現在の概要書の様式で作り直す一括変換ツール。

使い方:
  python convert_sheets.py <フォルダ または PDF> [<フォルダ>...] --out <出力フォルダ>
  python convert_sheets.py <フォルダ> --out <出力フォルダ> --dry-run     # 読み取り結果だけ確認

・元のファイルは一切変更しません（出力は --out の下に、同じフォルダ構成で新規作成）
・項目の値・利回り・特記事項・発行者情報・写真・地図は、元の書類のものをそのまま引き継ぎます
・概要書の様式でない PDF（投資分析など）は自動でスキップします
必要なもの: pip install pymupdf playwright / python -m playwright install chromium
"""
import argparse, base64, csv, html, json, os, re, sys
from pathlib import Path

try:
    import pymupdf
except ImportError:  # 古い PyMuPDF
    import fitz as pymupdf

APP = Path(__file__).resolve().parent.parent / "index.html"
MAX_PX = 1000

LABELS = ['物件名', '所在地', '地番', '交通', '価格', '権利', '地目', '公簿面積', '接道', '種類', '構造', '築年月',
          '延床面積', '専有面積', '総戸数', '間取り', '総階数', 'EV', '家屋番号', '検査済証', '満室想定賃料', '現況賃料',
          '稼働率', '満室想定利回り', '表面利回り', '実質利回り', '用途地域', '建蔽率', '容積率', '防火指定', '高度地区']
SECTIONS = {'土地', '建物', '収益情報', '法規制', '特記事項', '取引条件'}
MAPBAND = ('地図', '写真・地図', '写真地図')
DISCLAIMER = re.compile(r'^※\s*(本資料は参考情報|記載内容は調査時点)')
ERA = {'令和': 2018, '平成': 1988, '昭和': 1925, '大正': 1911, '明治': 1867}
STRUCT_MAP = [('鉄骨鉄筋', '鉄骨鉄筋コンクリート造'), ('SRC', '鉄骨鉄筋コンクリート造'), ('鉄筋コンクリート', '鉄筋コンクリート造'),
              ('RC', '鉄筋コンクリート造'), ('軽量鉄骨', '軽量鉄骨造(厚3mm超4mm以下)'), ('S造', '鉄骨造(厚4mm超)'),
              ('鉄骨造', '鉄骨造(厚4mm超)'), ('木造', '木造')]


def norm(t):
    return re.sub(r'[\s　]+', '', t)


def to_num(t, default=0):
    m = re.search(r'-?[\d,]+(?:\.\d+)?', t or '')
    return float(m.group(0).replace(',', '')) if m else default


def cluster_rows(lines):
    """(y, x, text) を行ごとにまとめ、左→右の順に並べる。"""
    lines = sorted(lines, key=lambda r: (r[0], r[1]))
    rows, cur, last = [], [], None
    for y, x, t in lines:
        if last is not None and y - last > 6:
            rows.append(cur); cur = []
        cur.append((y, x, t)); last = y
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        out.extend(sorted(r, key=lambda a: (a[1], a[0])))
    return out



LEGACY_LABELS = ['物件種別', 'エリア', '所在地', '交通', '延床面積', '専有面積', '用途', '構造', '規模', '構造・規模', '築年月', '現況', '土地面積', '土地権利',
                 '地目', '接道状況', 'バルコニー面積', '間取り', '所在階', '総戸数', '管理形態', '売出価格', '税区分', '坪単価', '取引態様', '引渡し', '価格条件',
                 '管理費', '修繕積立金', '現況賃料(年)', '表面利回り', '都市計画', '用途地域', '建ぺい率', '容積率', 'その他制限']
LEGACY_SECTIONS = {'物件基本情報', '建物情報', '敷地情報', '価格・取引情報', '収益情報', '法令制限', '備考・特記事項'}
LEGACY_NOTE = re.compile(r'^(※\s*本書の内容|CO\s*N\s*F\s*I\s*D\s*E\s*N\s*T\s*I\s*A\s*L)')


def parse_legacy(toks):
    """旧様式（物件基本情報／建物情報／敷地情報…の2ページ構成）。新様式と同じ形の辞書にそろえる。"""
    texts = [t for _, _, t in toks]
    m, warn = {'legacy': True, 'hasBuilding': True}, []
    ti = next(i for i, t in enumerate(texts) if '物件概要書' in norm(t))
    head = texts[:ti]
    tail = texts[ti + 1:]
    m['name'] = next((t for t in tail if not t.startswith('■')), '')
    iss = {'company': '', 'role': '', 'name': '', 'tel': '', 'email': '', 'office': ''}
    for t in head:
        if re.search(r'Mobile|Tel', t): iss['tel'] = re.sub(r'^(Mobile|Tel)[：:]\s*', '', t).strip()
        elif '@' in t: iss['email'] = t.strip()
        elif not iss['company'] and re.search(r'株式会社|Inc', t): iss['company'] = t
        elif not iss['name'] and iss['company'] and t != iss['company']: iss['name'] = t
    m['issuer'] = iss
    vals, cur, section, notes = {}, None, None, []
    for y, x, t in toks[ti + 1:]:
        n = norm(t)
        if n in LEGACY_SECTIONS:
            section = n; cur = None; continue
        if LEGACY_NOTE.match(t): cur = None; section = '終了'; continue
        if section == '備考・特記事項':
            notes.append(t); continue
        if t in LEGACY_LABELS:
            cur = t; vals.setdefault(cur, []); continue
        if cur is not None and section != '終了': vals[cur].append(t)
    g = lambda k: (' '.join(vals.get(k, [])).strip())
    def val(k):
        v = g(k); return '' if v in ('-', 'ー', '－') else v
    m['kind'] = val('物件種別'); m['address'] = val('所在地')
    tr = val('交通'); m['transit'] = re.sub(r'駅駅', '駅', tr)
    m['floorArea'] = val('延床面積') or val('専有面積'); m['landArea'] = val('土地面積')
    m['struct'] = val('構造') or val('構造・規模'); m['stories'] = val('規模') or val('所在階')
    m['built'] = val('築年月'); m['right'] = val('土地権利'); m['category'] = val('地目'); m['access'] = val('接道状況')
    m['units'] = val('総戸数'); m['dealType'] = val('取引態様'); m['delivery'] = val('引渡し')
    m['zoning'] = val('用途地域')
    for k_in, k_out in (('建ぺい率', 'coverage'), ('容積率', 'far')):
        if val(k_in): m[k_out] = val(k_in).replace('%', '').strip()
    m['curRent'] = val('現況賃料(年)')
    if m['curRent']: m['hasIncome'] = True
    if val('表面利回り'): m['grossText'] = val('表面利回り')
    pv = val('売出価格')
    pm = re.match(r'^([\d,\.]+)\s*(億)?\s*([\d,]*)\s*(万)?円', pv) if pv else None
    if pv and re.match(r'^[\d,]+円$', pv): m['price'] = int(re.sub(r'[^\d]', '', pv))
    elif pv and pm: m['price'] = int(float(pm.group(1).replace(',', '')) * (1e8 if pm.group(2) else (1e4 if pm.group(4) else 1)) + (float(pm.group(3).replace(',', '') or 0) * 1e4 if pm.group(3) else 0))
    else: m['priceNote'] = '価格要相談'
    other = val('その他制限')
    m['special'] = (''.join(notes) + ('\n' + other if other else '')).strip()
    m['noPhotoText'] = ''
    for need in ('name', 'address'):
        if not m.get(need): warn.append('必須項目を読み取れません: ' + need)
    return m, warn



def parse_rows(lines):
    """行データ [(y, x, text)] -> (項目の辞書, 警告のリスト)。画像は含まない。"""
    toks = cluster_rows(lines)
    m, warn = {}, []
    texts = [t for _, _, t in toks]
    if not any('物件概要書' in norm(t) for t in texts[:12]):
        return None, ['概要書の様式ではありません']
    if any(norm(t) == '物件基本情報' for t in texts):
        return parse_legacy(toks)
    for t in texts[:8]:
        if re.match(r'^[A-Za-z]-\d{8}-\w+$', t):
            m['docNo'] = t
        d = re.search(r'作成日[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日', t)
        if d:
            m['docDate'] = '%04d-%02d-%02d' % tuple(map(int, d.groups()))
    # 価格（価格枠の大きい文字は、ラベルの位置と前後するため先に抜き出す）
    for i, (y, x, t) in enumerate(toks):
        pm = re.match(r'^([\d,]+)\s*円\s*[（(](.*?)[）)]?$', t)
        if pm:
            m['price'] = int(pm.group(1).replace(',', '')); m['priceText'] = pm.group(2)
            del toks[i]; break
        if re.match(r'^価格\s*(要相談|未定|応相談|相談)', t):
            m['priceNote'] = t.replace(' ', ''); del toks[i]; break
    # フッター（発行者情報）の開始位置
    foot = next((i for i, (_, _, t) in enumerate(toks) if '｜' in t and re.search(r'Expert|Tel|Inc|株式会社', t)), None)
    footer = toks[foot:] if foot is not None else []
    body = toks[:foot] if foot is not None else toks
    vals, cur, section, bullets, mapnote = {}, None, None, [], []
    for y, x, t in body:
        n = norm(t)
        if n in SECTIONS or n.startswith(MAPBAND):
            section = '地図' if n.startswith(MAPBAND) else n; cur = None
            if section == '収益情報': m['hasIncome'] = True
            if section == '建物': m['hasBuilding'] = True
            continue
        if section == '特記事項':
            if t.startswith('・') or bullets:
                bullets.append(t); continue
        if section == '地図':
            if re.match(r'^写真は.*(ご案内|準備|未登録)', t):
                m['noPhotoText'] = t
            elif not DISCLAIMER.match(t):
                mapnote.append(t)
            continue
        if t in LABELS:
            cur = t; vals.setdefault(cur, []); continue
        if cur and not DISCLAIMER.match(t):
            vals[cur].append(t)
    v = lambda k: ' '.join(vals.get(k, [])).strip()
    nm = (vals.get('物件名') or [''])[0]
    sp = re.match(r'^(.*)\u3000([^\u3000]+)$', nm)
    m['name'] = sp.group(1).strip() if sp and re.search(r'[都道府県市区町村郡]', sp.group(2)) and len(sp.group(2)) <= 24 else nm
    # 価格の下の行：現況（バッジ）・利回り・引渡時期
    price_block = vals.get('価格', [])
    for t in price_block:
        if '表面利回り' in t or '引渡時期' in t:
            g = re.search(r'表面利回り\s*([^\s｜\u3000]+)', t); n_ = re.search(r'実質利回り\s*([^\s｜\u3000（]+(?:（[^）]*）)?)', t); dl = re.search(r'引渡時期[：:]\s*(\S+)', t)
            if g: m['grossText'] = g.group(1)
            if n_: m['netText'] = n_.group(1)
            if dl: m['delivery'] = dl.group(1)
            pre = re.split(r'表面利回り|引渡時期', t)[0].strip()
            if pre and len(pre) <= 12 and 'badge' not in m: m['badge'] = pre
        elif len(t) <= 12 and 'badge' not in m:
            m['badge'] = t
    for k_in, k_out in [('所在地', 'address'), ('地番', 'lot'), ('権利', 'right'), ('地目', 'category'), ('種類', 'kind'), ('家屋番号', 'bldgNo'),
                        ('検査済証', 'inspection'), ('EV', 'elevator'), ('総戸数', 'units'), ('総階数', 'stories'), ('用途地域', 'zoning'),
                        ('防火指定', 'fire'), ('高度地区', 'heightDistrict'), ('間取り', 'layout'), ('稼働率', 'occRate')]:
        if v(k_in): m[k_out] = v(k_in)
    for k in ('建蔽率', '容積率'):
        if v(k): m['coverage' if k == '建蔽率' else 'far'] = v(k).replace('%', '').strip()
    m['stories'] = ''.join(vals.get('総階数', [])) or m.get('stories', '')
    m['transit'] = v('交通'); m['access'] = v('接道'); m['struct'] = v('構造'); m['built'] = v('築年月')
    m['landArea'] = v('公簿面積'); m['floorArea'] = v('延床面積') or v('専有面積')
    m['fullRent'] = v('満室想定賃料'); m['curRent'] = v('現況賃料')
    m['rentLabelsSeen'] = bool(vals.get('満室想定賃料') or vals.get('現況賃料') or vals.get('満室想定利回り'))
    nv = vals.get('実質利回り', [])
    if nv:
        m.setdefault('netText', nv[0])
        notes = [t for t in nv[1:] if t.startswith('※')]
        if notes: m['netNote'] = ' '.join(notes)
    if vals.get('表面利回り'): m.setdefault('grossText', vals['表面利回り'][0])
    # 特記事項
    items = []
    for b in bullets:
        for part in re.split(r'・\s*(?=[①-⑳])', b):
            part = re.sub(r'^・?\s*[①-⑳\d]+[.．)]?\s*', '', part.strip())
            if part and not re.match(r'^本資料は参考情報です', part):
                items.append(part)
    m['special'] = '\n'.join(items)
    m['photoNote'] = ' '.join(mapnote).strip()
    # フッター
    ft = ' '.join(t for _, _, t in footer if not DISCLAIMER.match(t))
    parts = [p.strip() for p in re.split(r'[｜|]', ft) if p.strip()]
    iss = {'company': '', 'role': '', 'name': '', 'tel': '', 'email': '', 'office': ''}
    for p in parts:
        if p.startswith('Tel'): iss['tel'] = re.sub(r'^Tel[：:]\s*', '', p)
        elif p.startswith('Email'): iss['email'] = re.split(r'\s', re.sub(r'^Email[：:]\s*', '', p))[0]
        elif 'Expert' in p:
            iss['role'] = 'Expert Agent'; rest = re.sub(r'.*Expert Agent\s*', '', p).strip()
            if rest: iss['name'] = rest
        elif not iss['company']: iss['company'] = p
        elif not iss['name'] and not re.search(r'[:：]', p): iss['name'] = p
    o = re.search(r'事務所[：:]\s*(.+?)(?=\s+取引態様|$)', ft); dl = re.search(r'取引態様[：:]\s*(\S+)', ft)
    if o: iss['office'] = o.group(1).strip()
    if dl: m['dealType'] = dl.group(1)
    m['issuer'] = iss
    for need in ('name', 'address'):
        if not m.get(need): warn.append('必須項目を読み取れません: ' + need)
    if not m.get('price') and not m.get('priceNote'): warn.append('必須項目を読み取れません: price')
    return m, warn


def unknown(v):
    return (not v) or v in ('要確認', '不明', '-', 'ー')


def era_to_year(s):
    mm = re.search(r'(令和|平成|昭和|大正|明治)(元|\d+)年', s)
    if not mm: return None
    return ERA[mm.group(1)] + (1 if mm.group(2) == '元' else int(mm.group(2)))


def map_type(kind, struct_text, stories):
    k = kind or ''
    if '土地' in k and '建' not in k: return '土地'
    if re.search(r'戸建|一戸建|テラスハウス', k): return '一戸建て'
    if '一棟' in k or '棟' in k:
        return 'ビル・店舗' if re.search(r'ビル|店舗|事務所|倉庫|工場|ホテル', k) else 'アパート'
    if re.search(r'区分|マンション', k): return 'マンション'
    return 'アパート' if '共同' in k or 'レジデンス' in k else 'マンション'


def to_prop(m, photo=None, map_img=None):
    """読み取り結果 -> アプリの物件データ（sanitizeProp に渡す形）。"""
    kind = m.get('kind', '')
    ptype = map_type(kind, m.get('struct', ''), m.get('stories', '')) if (kind or m.get('hasBuilding')) else '土地'
    st = m.get('struct', '')
    struct = next((v for k, v in STRUCT_MAP if k in st), re.split(r'[（(\s　]', st)[0] if st else '')
    roof = (re.findall(r'(陸屋根|切妻屋根|寄棟屋根|片流れ屋根|瓦屋根|スレート屋根|折板屋根|屋根)', st) or [''])[-1]
    tr = m.get('transit', '')
    wm = re.search(r'徒歩\s*(\d+)\s*分', tr); sm = re.search(r'[「『](.+?)[」』]\s*駅', tr) or re.search(r'([^\s「」・]+?)駅', tr)
    built = ''
    bt = m.get('built', '')
    ym = re.search(r'(\d{4})年', bt); mo = re.search(r'年\s*(\d{1,2})月', bt)
    yr = int(ym.group(1)) if ym else era_to_year(bt)
    if yr: built = '%04d-%02d-01' % (yr, int(mo.group(1)) if mo else 1)
    am = re.search(r'築\s*(\d+)\s*年', bt)
    land_a, floor_a = to_num(m.get('landArea')), to_num(m.get('floorArea'))
    st_text = m.get('stories', '')
    above = re.search(r'地上\s*(\d+)', st_text); below = re.search(r'地下\s*(\d+)', st_text)
    access = m.get('access', '')
    road = {'roadDir': '', 'roadKind': '', 'roadWidth': ''}
    if access and not unknown(access):
        w = re.search(r'幅員\s*([\d.]+)', access)
        road['roadWidth'] = w.group(1) if w else ''
        parts = [p for p in re.split(r'[\s　]+', access) if p and not p.startswith('幅員') and not re.match(r'^[\d.]+m?$', p)]
        if parts and len(parts[0]) <= 2: road['roadDir'] = parts[0]; parts = parts[1:]
        road['roadKind'] = ' '.join(parts)
    elif access:
        road['roadKind'] = access
    cur_rent = 0 if m.get('legacy') else to_num(m.get('curRent')); full_rent = to_num(m.get('fullRent'))
    det = {
        'docNo': m.get('docNo', ''), 'docDate': m.get('docDate', ''), 'transit': re.sub(r'[\s　]*徒歩.*$', '', tr).strip(),
        'rightType': m.get('right', ''), 'zoning': m.get('zoning', ''), 'coverage': m.get('coverage', ''), 'far': m.get('far', ''),
        'fire': m.get('fire', ''), 'heightDistrict': m.get('heightDistrict', ''), 'elevator': m.get('elevator', ''),
        'inspection': m.get('inspection', ''), 'units': m.get('units', ''), 'roof': roof, 'delivery': m.get('delivery', ''),
        'occupancy': m.get('badge', ''), 'special': m.get('special', ''), 'photoNote': m.get('photoNote', ''),
        'dealType': m.get('dealType', ''), 'grossText': m.get('grossText', ''), 'netText': m.get('netText', ''), 'netNote': m.get('netNote', ''),
        'occupancyRate': (m.get('occRate', '') or '').replace('%', '').strip(), 'currentRent': str(int(cur_rent)) if cur_rent else '',
        'builtText': ('' if built else (bt if bt and not am else '')), 'priceNote': m.get('priceNote', ''), 'priceText': m.get('priceText', ''), 'showIncome': '1' if m.get('hasIncome') else '',
        'fullRentText': m.get('fullRent', ''), 'currentRentText': (m.get('curRent', '') + '（年額）') if (m.get('legacy') and m.get('curRent')) else m.get('curRent', ''), 'noPhotoText': m.get('noPhotoText', ''),
        'noAuto': '1',  # 元の書類にない自動コメント・実効容積率の注記は付けない
        'noFullRent': '' if full_rent else ('1' if (cur_rent or m.get('legacy')) else ''), **road,
    }
    if above:
        det['floorsAbove'] = above.group(1); det['floorsBelow'] = below.group(1) if below else ''
    else:
        det['stories'] = st_text
    p = {
        'id': re.sub(r'[^A-Za-z0-9_-]', '', m.get('docNo', '')) or 'conv', 'name': m['name'], 'address': m.get('address', ''),
        'station': (sm.group(1) if sm else ''), 'walk': int(wm.group(1)) if wm else 0, 'type': ptype,
        'purpose': '投資' if (full_rent or cur_rent or m.get('grossText')) else '居住', 'status': '検討中',
        'price': m.get('price', 0), 'rent': full_rent or cur_rent, 'area': (land_a if ptype == '土地' else floor_a),
        'layout': m.get('layout', ''), 'age': int(am.group(1)) if am else 0, 'mgmt': 0, 'tax': 0, 'note': '', 'det': det,
        'reg': {'acquired': '', 'joint': '', 'land': {'place': '', 'lot': m.get('lot', ''), 'category': m.get('category', ''), 'area': str(land_a) if land_a else (m.get('landArea') or '')},
                'bldg': {'place': '', 'no': m.get('bldgNo', ''), 'kind': kind, 'struct': struct, 'floorArea': str(floor_a) if floor_a else (m.get('floorArea') or ''), 'built': built}, 'kou': [], 'otsu': []},
    }
    if photo: p['photos'] = [{'src': photo, 'cap': ''}]
    if map_img: p['mapImg'] = map_img
    return p


def crop_uri(doc, xref, fx0, fx1):
    """元の書類で枠からはみ出して隠れていた部分を切り落とした画像（横方向の割合 fx0〜fx1 だけ残す）。"""
    pix = pymupdf.Pixmap(doc, xref)
    if pix.alpha: pix = pymupdf.Pixmap(pix, 0)
    if pix.n >= 4 or (pix.colorspace is not None and pix.colorspace.n >= 4): pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    x0, x1 = max(0, int(round(fx0 * pix.width))), min(pix.width, int(round(fx1 * pix.width)))
    clip = pymupdf.IRect(x0, 0, max(x0 + 1, x1), pix.height)
    k = min(1.0, MAX_PX / max(clip.width, clip.height))  # 長辺を MAX_PX 以下に縮小（ファイルサイズを抑える）
    cut = pymupdf.Pixmap(pix.colorspace, clip, False)
    cut.copy(pix, clip)
    n = int(1 / k)
    if n >= 2: cut.shrink(n)  # 整数倍で縮小（Pixmap の拡縮コンストラクタは一部の画像で落ちるため使わない）
    return 'data:image/jpeg;base64,' + base64.b64encode(cut.tobytes('jpeg', jpg_quality=85)).decode()


def data_uri(doc, xref):
    img = doc.extract_image(xref)
    ext = (img.get('ext') or '').lower()
    if ext in ('jpeg', 'jpg', 'png', 'gif', 'webp'):
        mime = 'jpeg' if ext in ('jpeg', 'jpg') else ext
        return 'data:image/%s;base64,%s' % (mime, base64.b64encode(img['image']).decode())
    pix = pymupdf.Pixmap(doc, xref)
    if pix.n - pix.alpha >= 4: pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    return 'data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode()


def classify_images(cands, page_w):
    """(x0, x1, 面積, xref) の一覧 -> (写真の xref, 地図の xref)。中心が右寄り=地図、左寄り=写真。"""
    photo = [c for c in cands if (c[0] + c[1]) / 2 < page_w * 0.45]
    mp = [c for c in cands if (c[0] + c[1]) / 2 > page_w * 0.55]
    pick = lambda l: max(l, key=lambda c: c[2])[3] if l else None
    return pick(photo), pick(mp)


def read_pdf(path):
    doc = pymupdf.open(str(path))
    page = doc[0]
    lines = []
    for pi, pg in enumerate(doc):  # 複数ページの書類（旧様式）は、2ページ目以降の文字も続けて読む
        for b in pg.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                t = ''.join(s['text'] for s in l['spans']).strip()
                if t: lines.append((l['bbox'][1] + pi * 10000, l['bbox'][0], t))
    cands = []
    for im in page.get_images(full=True):
        xref = im[0]
        for r in page.get_image_rects(xref):
            if r.width > 80 and r.height > 80 and im[2] >= 300:
                cands.append((r.x0, r.x1, r.width * r.height, xref)); break
    W = page.rect.width
    photo_x, map_x = classify_images([(a, b, ar, x) for a, b, ar, x in cands], W)
    box = {c[3]: (c[0], c[1]) for c in cands}

    def uri(xref, lo, hi):
        if not xref: return None
        x0, x1 = box[xref]
        fx0, fx1 = max(0.0, (lo - x0) / (x1 - x0)), min(1.0, (hi - x0) / (x1 - x0))
        try: return crop_uri(doc, xref, fx0 if fx0 > 0.01 else 0.0, fx1 if fx1 < 0.99 else 1.0)  # 枠で隠れていた部分は落とし、大きい画像は縮小
        except Exception: return data_uri(doc, xref)
    return lines, uri(photo_x, 0, W / 2), uri(map_x, W / 2, W)


def render_all(jobs, args):
    from playwright.sync_api import sync_playwright
    results = []
    with sync_playwright() as pw:
        kw = {'executable_path': os.environ['CHROMIUM_PATH']} if os.environ.get('CHROMIUM_PATH') else {}
        browser = pw.chromium.launch(**kw)
        page = browser.new_page()
        page.goto(APP.as_uri())
        for src, dst, prop, issuer in jobs:
            html_doc = page.evaluate("""([prop, issuer]) => {
                S.issuer = issuer; const p = sanitizeProp(prop); S.props = [p];
                return '<!doctype html><html lang="ja"><meta charset="utf-8"><title>物件概要書 - ' + esc(p.name) + '</title><style>body{margin:0;font-family:system-ui,"Hiragino Sans","Noto Sans JP",sans-serif}' + DOC_CSS + st.textContent + '</style><body><div id="doc" class="doc sheet">' + docGaiyo(ensure(p)) + '</div></body></html>' }""", [prop, issuer])
            pg = browser.new_page()
            pg.set_viewport_size({'width': 726, 'height': 1000})
            pg.set_content(html_doc, wait_until='load'); pg.emulate_media(media='print')
            h = pg.evaluate("document.querySelector('.doc').getBoundingClientRect().height")
            if h > 1030:  # A4 1ページ(余白9mm)に収まらないときは、全体を少し縮小する
                pg.evaluate("z => { document.querySelector('.doc').style.zoom = z }", 1030 / h)
            dst.parent.mkdir(parents=True, exist_ok=True)
            pg.pdf(path=str(dst), format='A4', print_background=True, prefer_css_page_size=True)
            n_pages = len(pymupdf.open(str(dst)))
            pg.close(); results.append((src, dst, n_pages))
        browser.close()
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inputs', nargs='+'); ap.add_argument('--out', required=True); ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        try: stream.reconfigure(encoding='utf-8', errors='replace')  # Windows のコンソールでも文字化けしないように
        except Exception: pass
    out = Path(args.out).resolve()
    files = []
    for i in args.inputs:
        p = Path(i).resolve()
        if p.is_dir():
            for f in sorted(p.rglob('*.pdf')):
                if out in f.parents: continue
                files.append((f, f.relative_to(p)))
        elif p.suffix.lower() == '.pdf':
            files.append((p, Path(p.name)))
    for f, rel in files:
        if (out / rel).resolve() == f:
            sys.exit('出力先が入力と同じ場所です。別のフォルダを指定してください: ' + str(f))
    jobs, log = [], []
    for f, rel in files:
        try:
            lines, photo, map_img = read_pdf(f)
            m, warn = parse_rows(lines)
        except Exception as e:  # 壊れた PDF など
            log.append((str(f), 'スキップ', 'PDFを読めません: %s' % e)); continue
        if m is None:
            log.append((str(f), 'スキップ', warn[0])); continue
        if any(w.startswith('必須') for w in warn):
            log.append((str(f), 'スキップ', ' / '.join(warn))); continue
        if not photo and not m.get('noPhotoText') and not m.get('legacy'): warn.append('写真を取り出せませんでした')
        if not map_img: warn.append('地図の画像を取り出せませんでした')
        if m.get('legacy'): warn.append('旧様式から変換（元の書類にない項目は空欄）')
        prop = to_prop(m, photo, map_img)
        jobs.append((f, out / rel, prop, m['issuer']))
        log.append((str(f), '読み取りOK' if not warn else '読み取りOK(注意)', ' / '.join(warn)))
        print('読み取り:', rel, m['name'], ('  ※' + ' / '.join(warn)) if warn else '')
    if not args.dry_run and jobs:
        for src, dst, n in render_all(jobs, args):
            for i, row in enumerate(log):
                if row[0] == str(src): log[i] = (row[0], '変換完了' if n == 1 else '変換完了(%dページ)' % n, row[2] + ('' if not row[2] else ' / ') + str(dst))
            print('作成:', dst)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / '変換ログ.csv', 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['元ファイル', '結果', '備考']); w.writerows(log)
    done = sum(1 for r in log if r[1].startswith('変換完了')); skip = sum(1 for r in log if r[1] == 'スキップ')
    print('\n対象 %d 件 / 変換 %d 件 / スキップ %d 件（%s）' % (len(log), done, skip, out / '変換ログ.csv'))


if __name__ == '__main__':
    main()
