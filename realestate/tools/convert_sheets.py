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


def parse_rows(lines):
    """行データ [(y, x, text)] -> (項目の辞書, 警告のリスト)。画像は含まない。"""
    toks = cluster_rows(lines)
    m, warn = {}, []
    texts = [t for _, _, t in toks]
    if not any('物件概要書' in norm(t) for t in texts[:8]):
        return None, ['概要書の様式ではありません']
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
    # フッター（発行者情報）の開始位置
    foot = next((i for i, (_, _, t) in enumerate(toks) if '｜' in t and re.search(r'Expert|Tel|Inc|株式会社', t)), None)
    footer = toks[foot:] if foot is not None else []
    body = toks[:foot] if foot is not None else toks
    vals, cur, section, bullets, mapnote = {}, None, None, [], []
    for y, x, t in body:
        n = norm(t)
        if n in SECTIONS or n.startswith(MAPBAND):
            section = '地図' if n.startswith(MAPBAND) else n; cur = None; continue
        if section == '特記事項':
            if t.startswith('・') or bullets:
                bullets.append(t); continue
        if section == '地図':
            if not DISCLAIMER.match(t):
                mapnote.append(t)
            continue
        if t in LABELS:
            cur = t; vals.setdefault(cur, []); continue
        if cur and not DISCLAIMER.match(t):
            vals[cur].append(t)
    v = lambda k: ' '.join(vals.get(k, [])).strip()
    m['name'] = (vals.get('物件名') or [''])[0]
    # 価格の下の行：現況（バッジ）・利回り・引渡時期
    price_block = vals.get('価格', [])
    for t in price_block:
        if '表面利回り' in t or '引渡時期' in t:
            g = re.search(r'表面利回り\s*([\d.]+%)', t); n_ = re.search(r'実質利回り\s*([\d.]+%[^\s｜]*)', t); dl = re.search(r'引渡時期[：:]\s*(\S+)', t)
            if g: m['grossText'] = g.group(1)
            if n_: m['netText'] = n_.group(1)
            if dl: m['delivery'] = dl.group(1)
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
    for need in ('name', 'price', 'address'):
        if not m.get(need): warn.append('必須項目を読み取れません: ' + need)
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
    ptype = map_type(kind, m.get('struct', ''), m.get('stories', ''))
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
    cur_rent = to_num(m.get('curRent')); full_rent = to_num(m.get('fullRent'))
    det = {
        'docNo': m.get('docNo', ''), 'docDate': m.get('docDate', ''), 'transit': re.sub(r'[\s　]*徒歩.*$', '', tr).strip(),
        'rightType': m.get('right', ''), 'zoning': m.get('zoning', ''), 'coverage': m.get('coverage', ''), 'far': m.get('far', ''),
        'fire': m.get('fire', ''), 'heightDistrict': m.get('heightDistrict', ''), 'elevator': m.get('elevator', ''),
        'inspection': m.get('inspection', ''), 'units': m.get('units', ''), 'roof': roof, 'delivery': m.get('delivery', ''),
        'occupancy': m.get('badge', ''), 'special': m.get('special', ''), 'photoNote': m.get('photoNote', ''),
        'dealType': m.get('dealType', ''), 'grossText': m.get('grossText', ''), 'netText': m.get('netText', ''), 'netNote': m.get('netNote', ''),
        'occupancyRate': (m.get('occRate', '') or '').replace('%', '').strip(), 'currentRent': str(int(cur_rent)) if cur_rent else '',
        'noAuto': '1',  # 元の書類にない自動コメント・実効容積率の注記は付けない
        'noFullRent': '' if full_rent else ('1' if cur_rent else ''), **road,
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
        'reg': {'acquired': '', 'joint': '', 'land': {'place': '', 'lot': m.get('lot', ''), 'category': m.get('category', ''), 'area': str(land_a) if land_a else ''},
                'bldg': {'place': '', 'no': m.get('bldgNo', ''), 'kind': kind, 'struct': struct, 'floorArea': str(floor_a) if floor_a else '', 'built': built}, 'kou': [], 'otsu': []},
    }
    if photo: p['photos'] = [{'src': photo, 'cap': ''}]
    if map_img: p['mapImg'] = map_img
    return p


def data_uri(doc, xref):
    img = doc.extract_image(xref)
    ext = (img.get('ext') or '').lower()
    if ext in ('jpeg', 'jpg', 'png', 'gif', 'webp'):
        mime = 'jpeg' if ext in ('jpeg', 'jpg') else ext
        return 'data:image/%s;base64,%s' % (mime, base64.b64encode(img['image']).decode())
    pix = pymupdf.Pixmap(doc, xref)
    if pix.n - pix.alpha >= 4: pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
    return 'data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode()


def read_pdf(path):
    doc = pymupdf.open(str(path))
    page = doc[0]
    lines = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            t = ''.join(s['text'] for s in l['spans']).strip()
            if t: lines.append((l['bbox'][1], l['bbox'][0], t))
    imgs = []
    for im in page.get_images(full=True):
        xref = im[0]
        for r in page.get_image_rects(xref):
            if r.width > 80 and r.height > 80 and im[2] >= 300:
                imgs.append((r.x0, xref)); break
    imgs.sort()
    photo = data_uri(doc, imgs[0][1]) if imgs else None
    map_img = data_uri(doc, imgs[1][1]) if len(imgs) > 1 else None
    return lines, photo, map_img


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
            pg.set_content(html_doc, wait_until='load'); pg.emulate_media(media='print')
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
        if not photo: warn.append('写真を取り出せませんでした')
        if not map_img: warn.append('地図の画像を取り出せませんでした')
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
