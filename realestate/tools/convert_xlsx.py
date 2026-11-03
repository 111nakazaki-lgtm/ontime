#!/usr/bin/env python3
"""土地一覧表(xlsx) -> 物件概要書PDF（1物件1枚）。

使い方:  python tools/convert_xlsx.py 一覧.xlsx --out 出力フォルダ [--issuer-json 発行者.json] [--include-stopped]
  - 1行目〜の凡例の下にある見出し行（No, 物件名, ...）から表を読みます。
  - 「販売中止」の物件は既定でも作成します（価格は「—」、バッジに販売中止）。--skip-stopped で除外。
"""
import argparse, csv, importlib.util, json, re, sys
from pathlib import Path
import openpyxl

spec = importlib.util.spec_from_file_location('convert_sheets', Path(__file__).with_name('convert_sheets.py'))
cs = importlib.util.module_from_spec(spec); spec.loader.exec_module(cs)

DEFAULT_ISSUER = {'company': 'TERASS, Inc.', 'role': 'Expert Agent', 'name': '高橋 幸輝', 'tel': '090-7258-2663', 'email': 'koki.takahashi@terass.com', 'office': ''}


def s(v):
    if v is None: return ''
    if isinstance(v, float) and v == int(v): v = int(v)
    return str(v).strip()


def n(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0


def fmt(v):
    x = n(v)
    return ('%g' % round(x, 2)) if x else ''


def load(path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == 'No')
    head = rows[hi]
    return [dict(zip(head, r)) for r in rows[hi + 1:] if r[0] is not None]


def to_prop(r, docdate):
    status = s(r['販売状況'])
    stopped = status == '販売中止'
    price = int(round(n(r['販売価格（万円）']) * 10000))
    lots = int(n(r['区画数（想定）']))
    area = n(r['有効面積（㎡）']) or n(r['実測㎡']) or n(r['公簿㎡'])
    st1, walk = s(r['最寄駅①']), int(n(r['徒歩①']))
    st2 = s(r['最寄駅②'])
    station = re.sub(r'^.*[\s　]', '', st1)
    transit = (st1 + '駅') if st1 and not st1.endswith('駅') else st1
    notes = []
    if lots > 1 and price: notes.append('想定%d区画（1区画あたり約%s万円）' % (lots, format(int(round(price / 10000 / lots)), ',')))
    elif lots > 1: notes.append('想定%d区画' % lots)
    if st2: notes.append('その他の最寄駅：' + st2)
    ar = [k + ' ' + fmt(r[c]) + '㎡' for k, c in (('公簿', '公簿㎡'), ('実測', '実測㎡'), ('セットバック', 'SB㎡'), ('私道', '私道㎡')) if n(r[c])]
    if ar: notes.append('面積：' + '／'.join(ar))
    if s(r['有効坪']): notes.append('有効面積 %s㎡（約%s坪）' % (fmt(r['有効面積（㎡）']), fmt(r['有効坪'])))
    if n(r['坪単価（万円）']): notes.append('坪単価 約%s万円' % format(n(r['坪単価（万円）']), ',.1f').rstrip('0').rstrip('.'))
    if s(r['設備']): notes.append('設備：' + s(r['設備']).replace('/', '、'))
    cond = [x for x in (s(r['現況']) and '現況：' + s(r['現況']), s(r['引渡条件']) and '引渡条件：' + s(r['引渡条件']), s(r['契約不適合責任']) and '契約不適合責任：' + s(r['契約不適合責任'])) if x]
    if cond: notes.append('　'.join(cond))
    if s(r['その他制限']): notes.append('その他制限：' + s(r['その他制限']))
    if s(r['第2用途地域']): notes.append('第2用途地域：%s（%s）' % (s(r['第2用途地域']), s(r['②建蔽/容積'])))
    if status == '確認中': notes.append('資料未整備のため確認中の物件です。数値は参考値です。')
    if stopped: notes.append('販売を中止しています。')
    no = int(n(r['No']))
    det = {'docNo': 'S-%s-TL%03d' % (docdate.replace('-', ''), no), 'docDate': docdate, 'transit': transit, 'rightType': s(r['権利']) or '所有権',
           'zoning': s(r['用途地域①']), 'coverage': s(r['建蔽①%']), 'far': s(r['容積①%']), 'fire': s(r['防火指定']), 'heightDistrict': s(r['高度地区']),
           'roadKind': s(r['前面道路']), 'delivery': s(r['引渡時期']) or '応相談', 'occupancy': status, 'special': '\n'.join(notes),
           'priceNote': '価格未定' if not price else '', 'noAuto': '1'}
    name = s(r['物件名'])
    return {'id': 'tl%03d' % no, 'name': name, 'address': s(r['所在地']), 'station': station, 'walk': walk, 'type': '土地', 'purpose': '居住', 'status': '検討中',
            'price': price, 'area': area, 'det': det,
            'reg': {'acquired': '', 'joint': '', 'land': {'place': '', 'lot': s(r['地番']), 'category': s(r['地目']), 'area': (fmt(r['公簿㎡']) or fmt(area))},
                    'bldg': {'place': '', 'no': '', 'kind': '', 'struct': '', 'floorArea': '', 'built': ''}, 'kou': [], 'otsu': []}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('xlsx'); ap.add_argument('--out', required=True); ap.add_argument('--issuer-json'); ap.add_argument('--docdate', default='')
    ap.add_argument('--skip-stopped', action='store_true')
    a = ap.parse_args()
    iss = json.load(open(a.issuer_json, encoding='utf-8')) if a.issuer_json else DEFAULT_ISSUER
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    rows = load(a.xlsx)
    jobs, log = [], []
    for r in rows:
        if a.skip_stopped and s(r['販売状況']) == '販売中止': continue
        p = to_prop(r, a.docdate or '2026-10-06')
        safe = re.sub(r'[\\/:*?"<>|]', '_', p['name'])
        sub = {'販売中': '', '確認中': '確認中_', '販売中止': '販売中止_'}.get(s(r['販売状況']), '')
        dst = out / ('%s%03d_%s_概要書.pdf' % (sub, int(n(r['No'])), safe))
        jobs.append((Path(s(r['No'])), dst, p, iss)); log.append([int(n(r['No'])), p['name'], s(r['販売状況']), dst.name, s(r['資料フォルダ'])])
    res = cs.render_all(jobs, a)
    bad = [x for x in res if x[2] != 1]
    with open(out / '一覧.csv', 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh); w.writerow(['No', '物件名', '販売状況', '概要書ファイル', '資料フォルダ']); w.writerows(log)
    print('作成 %d 件 / 1ページに収まらなかった %d 件' % (len(res), len(bad)), [str(x[1].name) for x in bad])


if __name__ == '__main__':
    main()
