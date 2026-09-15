#!/usr/bin/env python3
"""北师大教室课表占用查询；仅依赖 Python 3.9+ 标准库。"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

BASE = 'https://weixin.bnu.edu.cn/classroom/'
BUILDINGS = ['化学楼', '教七楼', '教三楼', '教九楼', '教二楼', '教八楼',
             '教十楼', '教四楼', '生地楼', '电子楼', '育荣主', '艺术楼']
SLOTS = ['08:00–09:40', '10:00–11:40', '13:30–15:10',
         '15:30–17:10', '18:00–19:40', '19:50–21:30']
CHINA_TZ = timezone(timedelta(hours=8))
DAYS = {'today': 0, 'tomorrow': 1, '2daysl': 2}


def validate_rows(data, room_mode):
    """缺失或损坏的数据不能当成空结果、空闲教室。"""
    if not isinstance(data, dict) or type(data.get('success')) is not int or data['success'] != 1:
        raise ValueError('接口未返回成功数据')
    key, label = ('detail', 'date') if room_mode else ('result', 'room_number')
    if key not in data or not isinstance(data[key], list):
        raise ValueError('接口缺少有效的 ' + key + ' 列表')
    for row in data[key]:
        if not isinstance(row, dict) or not isinstance(row.get(label), str) or not row[label].strip():
            raise ValueError('接口记录缺少有效的 ' + label)
        status = row.get('status')
        if not isinstance(status, list) or len(status) != 6 or any(type(s) is not int for s in status):
            raise ValueError('接口 status 必须包含六个整数，无法可靠判断空闲情况')
        if room_mode:
            try:
                datetime.strptime(row['date'], '%Y-%m-%d')
            except ValueError as exc:
                raise ValueError('接口日期格式无效') from exc
    return key, data[key]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--building', default='教二楼', choices=BUILDINGS, help='默认教二楼')
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--day', choices=list(DAYS), help='今天、明天、后天；默认 today')
    mode.add_argument('--room', help='指定教室七天课表，例如 307；不能与 --day 混用')
    p.add_argument('--json', action='store_true', help='输出经过验证及筛选的 JSON')
    p.add_argument('--list-buildings', action='store_true', help='列出支持的楼宇')
    p.add_argument('--free-slots', nargs='+', type=int, choices=range(1, 7),
                   help='所选大节必须全部空闲；文本与 JSON 模式均生效')
    p.add_argument('--use-proxy', action='store_true', help='使用系统/环境代理；默认直连')
    a = p.parse_args(argv)
    if a.room is not None and not a.room.strip():
        p.error('--room 不能为空')
    if a.list_buildings:
        print(json.dumps({'buildings': BUILDINGS}, ensure_ascii=False) if a.json else '\n'.join(BUILDINGS))
        return 0
    day = a.day or 'today'
    room = a.room.strip() if a.room is not None else None
    params = {'ca': 1, 'b_name': a.building}
    params.update({'room': room} if room else {'time': day})
    endpoint = 'room-detail.php' if room else 'rooms.php'
    url = BASE + endpoint + '?' + urlencode(params)
    started = datetime.now(CHINA_TZ)
    try:
        opener = build_opener() if a.use_proxy else build_opener(ProxyHandler({}))
        with opener.open(Request(url), timeout=20) as response:
            data = json.load(response)
        key, rows = validate_rows(data, bool(room))
        fetched = datetime.now(CHINA_TZ)
        if not room and started.date() != fetched.date():
            raise ValueError('请求跨越北京时间午夜，请重新查询以确认日期')
        matched = [row for row in rows if not a.free_slots or
                   all(row['status'][i - 1] == 0 for i in a.free_slots)]
        result = {'success': 1, 'building': a.building, 'room': room,
                  'day': None if room else day,
                  'query_date': None if room else (started.date() + timedelta(days=DAYS[day])).isoformat(),
                  'timezone': 'Asia/Shanghai', 'fetched_at': fetched.isoformat(timespec='seconds'),
                  'source_url': url, 'slots': SLOTS, 'free_slots': sorted(set(a.free_slots or [])),
                  'total_count': len(rows), 'count': len(matched), key: matched}
        if a.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(a.building, room or result['query_date'])
            print('时段：' + ' | '.join(f'{i + 1}={slot}' for i, slot in enumerate(SLOTS)))
            for row in matched:
                label = row['date'] if room else row['room_number']
                print(label + '\t' + ' | '.join('空' if s == 0 else '占' for s in row['status']))
            if not rows:
                print('接口返回空列表，无法据此确认该楼宇或教室可用。')
            elif not matched:
                print('没有符合所选时段的记录。')
            print(f'共 {len(matched)} 条（原始记录 {len(rows)} 条）；课表占用以教务安排及现场情况为准。')
        return 0
    except (HTTPError, URLError, OSError, ValueError) as exc:
        message = f'查询失败：{exc}'
        if a.json:
            print(json.dumps({'success': 0, 'error': message}, ensure_ascii=False))
        print(message, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
