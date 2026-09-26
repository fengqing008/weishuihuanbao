#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ali-asr — 阿里云 DashScope 语音转写（非实时文件转写）

用法:
  python3 transcribe.py <音频文件或公开URL> [--out 结果.json] [--diarization] [--speakers N]
                        [--lang zh] [--vocab "热词:权重,热词2:权重"] [--model MODEL]

输出:
  - stdout 打印逐句文本（供上层链路直接捕获）
  - --out 指定 .json 时写入结构化结果，结构：
    {"text": 全文,
     "transcripts": [{"text": 全文, "sentences": [{"text","speaker_id","begin_time","end_time"}]}],
     "sentences": [...]}

依赖: requests；环境变量 DASHSCOPE_API_KEY（或 ~/.dashscope_config.json）
"""
import argparse
import json
import os
import pathlib
import sys
import time

API_BASE = 'https://dashscope.aliyuncs.com'
DEFAULT_MODEL = 'qwen-audio-3.0-asr-flash-filetrans'


def load_api_key() -> str:
    key = os.environ.get('DASHSCOPE_API_KEY')
    if key:
        return key
    cfg = pathlib.Path.home() / '.dashscope_config.json'
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding='utf-8'))
            key = data.get('api_key') or data.get('apiKey')
            if key:
                return key
        except Exception:
            pass
    raise SystemExit('ali-asr: 未找到 DASHSCOPE_API_KEY（请设置环境变量或写入 ~/.dashscope_config.json）')


def upload_file(api_key: str, file_path: str, model: str) -> str:
    """上传本地文件到 DashScope 托管 OSS，返回 oss:// 协议地址。"""
    import requests
    r = requests.get(
        f'{API_BASE}/api/v1/uploads',
        headers={'Authorization': f'Bearer {api_key}'},
        params={'action': 'getPolicy', 'model': model},
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f'获取上传凭证失败: {r.status_code} {r.text[:200]}')
    policy = r.json()['data']
    name = pathlib.Path(file_path).name
    key = f"{policy['upload_dir']}/{name}"
    with open(file_path, 'rb') as fh:
        files = {
            'OSSAccessKeyId': (None, policy['oss_access_key_id']),
            'policy': (None, policy['policy']),
            'signature': (None, policy['signature']),
            'key': (None, key),
            'x-oss-object-acl': (None, policy.get('x_oss_object_acl', 'private')),
            'x-oss-forbid-overwrite': (None, policy.get('x_oss_forbid_overwrite', 'true')),
            'file': (name, fh, 'application/octet-stream'),
        }
        up = requests.post(policy['upload_host'], files=files, timeout=300)
    if up.status_code not in (200, 204):
        raise RuntimeError(f'文件上传失败: {up.status_code} {up.text[:200]}')
    return f'oss://{key}'


def transcribe(audio: str, out_json: str = None, diarization: bool = False,
               speakers: int = None, lang: str = 'zh', vocab: str = None,
               model: str = DEFAULT_MODEL) -> dict:
    import requests

    api_key = load_api_key()
    if os.path.isfile(audio):
        print(f'[ali-asr] 本地文件: {audio}')
        file_url = upload_file(api_key, audio, model)
        print(f'[ali-asr] 已上传: {file_url[:80]}...')
    else:
        file_url = audio

    parameters = {}
    if lang:
        parameters['language_hints'] = [lang]
    if diarization:
        parameters['diarization_enabled'] = True
        if speakers:
            parameters['speaker_count'] = speakers
    if vocab:
        vdict = {}
        for item in vocab.split(','):
            parts = item.strip().split(':')
            if len(parts) == 2:
                vdict[parts[0].strip()] = int(parts[1].strip())
        if vdict:
            parameters['vocabulary'] = vdict

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'X-DashScope-Async': 'enable',
        'X-DashScope-OssResourceResolve': 'enable',
    }
    payload = {'model': model, 'input': {'file_urls': [file_url]}, 'parameters': parameters}
    print(f'[ali-asr] 提交转写任务 (model={model})...')
    r = requests.post(f'{API_BASE}/api/v1/services/audio/asr/transcription',
                      headers=headers, data=json.dumps(payload), timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f'提交转写任务失败 HTTP {r.status_code}: {r.text[:300]}')
    task_id = r.json().get('output', {}).get('task_id')
    print(f'[ali-asr] 任务ID: {task_id}，轮询中...')

    js = None
    while True:
        time.sleep(2)
        q = requests.get(f'{API_BASE}/api/v1/tasks/{task_id}',
                         headers={'Authorization': f'Bearer {api_key}'}, timeout=30)
        js = q.json()
        status = js.get('output', {}).get('task_status')
        if status == 'SUCCEEDED':
            break
        if status in ('FAILED', 'UNKNOWN', 'CANCELED'):
            raise RuntimeError(f'转写任务失败({status}): {json.dumps(js, ensure_ascii=False)[:400]}')

    sentences = []
    for item in js.get('output', {}).get('results', []):
        out = item.get('output', item)
        turl = out.get('transcription_url')
        if not turl and out.get('results'):
            turl = out['results'][0].get('transcription_url')
        if turl:
            data = requests.get(turl, timeout=30).json()
        else:
            data = out
        for t in data.get('transcripts', []):
            for s in t.get('sentences', []) or []:
                sentences.append({
                    'text': s.get('text', ''),
                    'speaker_id': s.get('speaker_id', ''),
                    'begin_time': s.get('begin_time', 0),
                    'end_time': s.get('end_time', 0),
                })
            if not t.get('sentences') and t.get('text'):
                sentences.append({'text': t['text'], 'speaker_id': '', 'begin_time': 0, 'end_time': 0})

    full_text = '\n'.join(
        (f"[说话人{s['speaker_id']}] " if s['speaker_id'] else '') + s['text'] for s in sentences
    )
    result = {
        'text': full_text,
        'transcripts': [{'text': full_text, 'sentences': sentences}],
        'sentences': sentences,
    }

    print('\n' + '=' * 60)
    print(full_text if full_text else '(空)')
    print('=' * 60)
    print(f'[ali-asr] 共 {len(sentences)} 句')

    if out_json:
        pathlib.Path(out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'[ali-asr] 已保存: {out_json}')
    return result


def main():
    ap = argparse.ArgumentParser(description='ali-asr 语音转写（DashScope 非实时文件转写）')
    ap.add_argument('audio', help='音频/视频文件路径，或公开可访问 URL')
    ap.add_argument('--out', '-o', dest='out', default=None, help='结果 JSON 输出路径（.json）')
    ap.add_argument('--diarization', action='store_true', help='开启说话人分离')
    ap.add_argument('--speakers', type=int, default=None, help='说话人数量参考')
    ap.add_argument('--lang', default='zh', help='语言提示（默认 zh）')
    ap.add_argument('--vocab', default=None, help='热词，格式 "词1:权重,词2:权重"')
    ap.add_argument('--model', default=DEFAULT_MODEL, help=f'转写模型（默认 {DEFAULT_MODEL}）')
    args = ap.parse_args()

    try:
        transcribe(args.audio, args.out, args.diarization, args.speakers,
                   args.lang, args.vocab, args.model)
    except Exception as exc:
        print(f'[ali-asr] 错误: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
