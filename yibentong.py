import requests
from bs4 import BeautifulSoup
import re
import os
import datetime
import time
import sys
import html
import argparse
import urllib.parse
from urllib.parse import urljoin
import hashlib
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import shutil

# 全局选项（由 CLI 设置）
SKIP_IMAGES = False
JSON_ONLY = False

def clean_html_content(content):
    if not content:
        return ""
    content = content.replace('\\"', '"')
    content = content.replace("\\'", "'")
    content = content.replace('\\\\', '\\')
    content = html.unescape(content)
    return content

def ensure_paragraph_tags(html_content):
    if not html_content:
        return html_content
    if '<p>' in html_content or '<div>' in html_content or '<img' in html_content:
        return html_content
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text().strip()
    if not text:
        return html_content
    paragraphs = re.split(r'\n\s*\n', text)
    html_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para:
            para = para.replace('\n', '<br>')
            html_paragraphs.append(f'<p>{para}</p>')
    if html_paragraphs:
        return ''.join(html_paragraphs)
    return html_content

def make_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    })
    retry = Retry(total=5, backoff_factor=0.6, status_forcelist=[429,500,502,503,504], allowed_methods=["HEAD","GET","OPTIONS"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def process_images_in_html(soup, problem_id, page_url, session):
    if SKIP_IMAGES:
        return soup
    try:
        img_tags = soup.find_all('img')
        if not img_tags:
            return soup
        img_dir = os.path.join('image', str(problem_id))
        os.makedirs(img_dir, exist_ok=True)
        def sanitize_name(name):
            return re.sub(r'[^A-Za-z0-9._-]', '_', name)

        for idx, img_tag in enumerate(img_tags, start=1):
            src = img_tag.get('src')
            if not src:
                continue
            src = clean_html_content(src)
            img_url = src if src.startswith('http') else urljoin(page_url, src)
            try:
                with session.get(img_url, timeout=15, stream=True) as img_response:
                    if img_response.status_code != 200:
                        logging.warning('图片下载失败: %s, 状态码: %s', img_url, img_response.status_code)
                        continue
                    content_type = img_response.headers.get('Content-Type','')
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    else:
                        url_ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1]
                        ext = url_ext if url_ext and len(url_ext)<=6 else '.jpg'
                    h = hashlib.md5(img_url.encode('utf-8')).hexdigest()[:10]
                    img_filename = sanitize_name(f"{problem_id}_{idx}_{h}{ext}")
                    img_path = os.path.join(img_dir, img_filename)
                    with open(img_path, 'wb') as f:
                        for chunk in img_response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    logging.info('已下载图片: %s', img_filename)
                    try:
                        primary_filename = sanitize_name(f"{problem_id}{ext}")
                        primary_path = os.path.join(img_dir, primary_filename)
                        if not os.path.exists(primary_path):
                            shutil.copy(img_path, primary_path)
                            logging.info('已创建兼容图片副本: %s', primary_filename)
                    except Exception:
                        logging.exception('创建兼容图片副本失败: %s', img_path)
                    new_src = f"/upload/image/{problem_id}/{img_filename}"
                    img_tag['src'] = new_src
            except Exception:
                logging.exception('处理图片时出错: %s', img_url)
                continue
        return soup
    except Exception:
        logging.exception('处理HTML图片时出错')
        return soup

def extract_html_from_script(script_content, problem_id, page_url, session):
    if not script_content:
        return ''
    match = re.search(r'pshow\("(.*?)"\)', script_content, re.DOTALL)
    if not match:
        return ''
    content = match.group(1)
    content = clean_html_content(content).replace('\\n','\n').replace('\\t','\t')
    content_soup = BeautifulSoup(content, 'html.parser')
    content_soup = process_images_in_html(content_soup, problem_id, page_url, session)
    return str(content_soup)

def extract_text_from_script(script_content):
    if not script_content:
        return ''
    match = re.search(r'pshow\("(.*?)"\)', script_content, re.DOTALL)
    if match:
        content = match.group(1)
        content = clean_html_content(content).replace('\\n','\n').replace('\\t','\t')
        content = re.sub(r'<[^>]+>','', content)
        return content.strip()
    return ''

def crawl_problem(problem_id, session):
    url = f'http://ybt.ssoier.cn:8088/problem_show.php?pid={problem_id}'
    try:
        print(f'正在爬取题目 {problem_id}...')
        resp = session.get(url, timeout=10)
        resp.encoding = 'utf-8'
        if resp.status_code != 200:
            print(f'请求失败，状态码: {resp.status_code}')
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')
        title = ''
        for h3 in soup.find_all('h3'):
            h3_text = h3.get_text(strip=True)
            if str(problem_id) in h3_text:
                title = h3_text
                break
        problem_exists = True
        if not title:
            title = f"{problem_id}：未知题目"
            problem_exists = False
        time_limit = '1000'
        memory_limit = '32768'
        all_text = soup.get_text()
        tm = re.search(r'时间限制\s*[:：]\s*(\d+)\s*ms', all_text)
        if tm:
            time_limit = tm.group(1)
        mm = re.search(r'内存限制\s*[:：]\s*(\d+)\s*KB', all_text)
        if mm:
            memory_limit = mm.group(1)
        found_html = []
        found_text = []
        for script in soup.find_all('script'):
            s = script.get_text() if script else ''
            if s and 'pshow' in s:
                htmlc = extract_html_from_script(s, problem_id, url, session)
                if htmlc:
                    found_html.append(htmlc)
                tc = extract_text_from_script(s)
                if tc:
                    found_text.append(tc)
        problem_description_html = found_html[0] if len(found_html)>=1 else ''
        input_description_html = found_html[1] if len(found_html)>=2 else ''
        output_description_html = found_html[2] if len(found_html)>=3 else ''
        problem_description_text = found_text[0] if len(found_text)>=1 else ''
        input_description_text = found_text[1] if len(found_text)>=2 else ''
        output_description_text = found_text[2] if len(found_text)>=3 else ''
        input_sample = ''
        output_sample = ''
        pre_tags = soup.find_all('pre')
        if len(pre_tags) >=2:
            input_sample = pre_tags[0].get_text(strip=False).strip()
            output_sample = pre_tags[1].get_text(strip=False).strip()
        elif len(pre_tags) ==1:
            output_sample = pre_tags[0].get_text(strip=False).strip()
        pdata = {
            'title': title,
            'description': problem_description_html,
            'input': input_description_html,
            'output': output_description_html,
            'sample_input': input_sample,
            'sample_output': output_sample,
            'time_limit': time_limit,
            'memory_limit': memory_limit,
            'description_text': problem_description_text,
            'input_text': input_description_text,
            'output_text': output_description_text,
            'exists': problem_exists
        }
        return pdata
    except Exception:
        logging.exception('爬取题目 %s 时出错', problem_id)
        return None

def save_sample_files(problem_data, problem_id):
    if not problem_data:
        return False
    if not problem_data.get('exists', True):
        logging.info('跳过不存在的题目: %s', problem_id)
        return False
    try:
        m = re.match(r'^(\d+)', problem_data.get('title',''))
        pid = m.group(1) if m else str(problem_id)
        problem_dir = os.path.join('data', pid)
        os.makedirs(problem_dir, exist_ok=True)
        with open(os.path.join(problem_dir, 'sample.in'), 'w', encoding='utf-8') as f:
            f.write(problem_data.get('sample_input',''))
        with open(os.path.join(problem_dir, 'sample.out'), 'w', encoding='utf-8') as f:
            f.write(problem_data.get('sample_output',''))
        print(f'已保存样例文件到: {problem_dir}')
        return True
    except Exception:
        logging.exception('保存样例文件失败: %s', problem_id)
        return False

def generate_sql_insert(problem_data, problem_id):
    if not problem_data:
        return None
    if not problem_data.get('exists', True):
        logging.info('跳过不存在的题目SQL生成: %s', problem_id)
        return None
    try:
        def replace_image_srcs(html_content, pid):
            # 不需要替换图片路径，直接返回原始HTML内容
            # 图片路径在爬取时已经正确设置为 /upload/image/{pid}/{filename}
            return html_content

        def escape_sql(text):
            if not text:
                return ''
            text = clean_html_content(text)
            text = text.replace('\\','\\\\')
            text = text.replace("'","''")
            return text

        try:
            problem_data['description'] = replace_image_srcs(problem_data.get('description',''), problem_id)
            problem_data['input'] = replace_image_srcs(problem_data.get('input',''), problem_id)
            problem_data['output'] = replace_image_srcs(problem_data.get('output',''), problem_id)
        except Exception:
            logging.exception('预处理图片引用失败: %s', problem_id)

        description = ensure_paragraph_tags(problem_data.get('description',''))
        input_desc = ensure_paragraph_tags(problem_data.get('input',''))
        output_desc = ensure_paragraph_tags(problem_data.get('output',''))
        title = escape_sql(problem_data.get('title',''))
        # 去掉题目名称前面的题号（如"1000："或"1000："）以避免与自增id冲突
        title = re.sub(r'^\d+[：:.、]', '', title).strip()
        
        description = escape_sql(description)
        input_desc = escape_sql(input_desc)
        output_desc = escape_sql(output_desc)
        sample_input = escape_sql(problem_data.get('sample_input',''))
        sample_output = escape_sql(problem_data.get('sample_output',''))

        try:
            description = replace_image_srcs(description, problem_id)
            input_desc = replace_image_srcs(input_desc, problem_id)
            output_desc = replace_image_srcs(output_desc, problem_id)
        except Exception:
            logging.exception('替换图片引用时出错: %s', problem_id)

        if not description and 'description_text' in problem_data:
            description = escape_sql(ensure_paragraph_tags(problem_data['description_text']))
        if not input_desc and 'input_text' in problem_data:
            input_desc = escape_sql(ensure_paragraph_tags(problem_data['input_text']))
        if not output_desc and 'output_text' in problem_data:
            output_desc = escape_sql(ensure_paragraph_tags(problem_data['output_text']))

        time_limit = float(problem_data.get('time_limit', '1000'))/1000
        memory_limit = int(problem_data.get('memory_limit', '32768'))//1024
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        sql = f"""INSERT INTO `problem` (
    `title`, `description`, `input`, `output`, `sample_input`, `sample_output`,
    `spj`, `hint`, `source`, `in_date`, `time_limit`, `memory_limit`,
    `defunct`, `accepted`, `submit`, `solved`, `remote_oj`, `remote_id`
) VALUES (
    '{title}',
    '{description}',
    '{input_desc}',
    '{output_desc}',
    '{sample_input}',
    '{sample_output}',
    '0',
    NULL,
    '信息学奥赛一本通（C++版）在线评测系统',
    '{current_time}',
    {time_limit:.3f},
    {memory_limit},
    'N',
    0,
    0,
    0,
    NULL,
    NULL
);"""
        return sql
    except Exception:
        logging.exception('生成SQL时出错: %s', problem_id)
        return None

def create_sql_file(problems, start_id, end_id):
    sql_file = f"problems_{start_id}_{end_id}.sql"
    sql_content = """-- 设置字符集
SET NAMES utf8mb4;

-- 使用数据库
USE jol;

-- 插入题目数据
"""
    for pid_str, pdata in problems.items():
        try:
            pid = int(pid_str)
        except Exception:
            continue
        if pdata:
            sql = generate_sql_insert(pdata, pid)
            if sql:
                sql_content += sql + "\n\n"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    print(f"SQL文件已保存到: {sql_file}")
    return sql_file

def crawl_ids_concurrent(id_list, max_workers=3, rate_delay=0.5):
    results = {}
    failed = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(crawl_problem, pid, make_session()): pid for pid in id_list}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                data = fut.result()
                if data and data.get('exists', True):
                    results[pid] = data
                    try:
                        save_sample_files(data, pid)
                    except Exception:
                        logging.exception('保存样例失败: %s', pid)
                elif data:
                    results[pid] = data
                else:
                    failed.append(pid)
            except Exception:
                logging.exception('并发爬取时异常: %s', pid)
                failed.append(pid)
    return results, failed

def main():
    parser = argparse.ArgumentParser(description='信息学奥赛一本通题目爬取工具')
    parser.add_argument('start', type=int, nargs='?', default=1445)
    parser.add_argument('end', type=int, nargs='?', default=1445)
    parser.add_argument('--concurrent', '-c', type=int, nargs='?', const=3)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--json-only', action='store_true')
    parser.add_argument('--no-image', action='store_true')
    parser.add_argument('--rate', type=float, default=0.5)
    args = parser.parse_args()

    global SKIP_IMAGES, JSON_ONLY
    SKIP_IMAGES = bool(args.no_image)
    JSON_ONLY = bool(args.json_only)

    start_id = args.start
    end_id = args.end
    workers = args.concurrent if args.concurrent is not None else None
    use_concurrent = workers is not None
    rate_delay = args.rate

    for d in ('data','image'):
        os.makedirs(d, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        fh = logging.FileHandler('crawler.log', encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        logger.addHandler(ch)
        logger.addHandler(fh)

    json_file = f'problems_{start_id}_{end_id}.json'
    completed = set()
    if args.resume and os.path.exists(json_file):
        try:
            with open(json_file,'r',encoding='utf-8') as jf:
                prev = json.load(jf)
            for k in prev.keys():
                try:
                    completed.add(int(k))
                except Exception:
                    pass
            logging.info('从JSON恢复，已跳过 %s 项', len(completed))
        except Exception:
            logging.exception('加载 JSON 失败，继续全量抓取')

    ids = [pid for pid in range(start_id, end_id+1) if pid not in completed]
    all_problems = {}

    # 如果是 --json-only 模式，直接跳过爬取
    if JSON_ONLY:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as jf:
                    all_problems = json.load(jf)
                logging.info('--json-only 模式：仅基于现有 JSON %s 生成 SQL', json_file)
            except Exception:
                logging.exception('加载 JSON 失败')
                print(f'错误：找不到 {json_file}，无法进行 --json-only 模式')
                return
        else:
            print(f'错误：--json-only 模式需要已有的 JSON 文件 {json_file}')
            return
    elif not ids:
        if os.path.exists(json_file):
            with open(json_file,'r',encoding='utf-8') as jf:
                existing = json.load(jf)
            create_sql_file(existing, start_id, end_id)
            print('没有需要抓取的题目，已基于现有 JSON 生成 SQL')
            return
        else:
            print('没有需要抓取的题目且未找到 JSON')
            return

    if not JSON_ONLY:
        if use_concurrent:
            w = workers if workers and workers>0 else 3
            logging.info('使用并发： workers=%s', w)
            results, failed = crawl_ids_concurrent(ids, max_workers=w, rate_delay=rate_delay)
            all_problems.update(results)
            if failed:
                with open('failed_ids.txt','w',encoding='utf-8') as f:
                    for fid in failed:
                        f.write(str(fid)+'\n')
        else:
            sess = make_session()
            for pid in ids:
                pdata = crawl_problem(pid, sess)
                if pdata and pdata.get('exists', True):
                    save_sample_files(pdata, pid)
                    all_problems[pid] = pdata
                elif pdata:
                    all_problems[pid] = pdata
                else:
                    all_problems[pid] = {'title': f"{pid}：题目不存在", 'description':'', 'input':'', 'output':'', 'sample_input':'', 'sample_output':'', 'time_limit':'1000','memory_limit':'32768', 'exists': False}
                time.sleep(1)

    # 合并已有 JSON
    if os.path.exists(json_file):
        try:
            with open(json_file,'r',encoding='utf-8') as jf:
                prev = json.load(jf)
            for k,v in prev.items():
                try:
                    ik = int(k)
                except Exception:
                    continue
                if ik not in all_problems:
                    all_problems[ik] = v
        except Exception:
            logging.exception('合并已有 JSON 失败')

    try:
        # 确保所有 key 都转换为 int，然后按 int 排序
        int_problems = {}
        for k, v in all_problems.items():
            try:
                int_key = int(k) if isinstance(k, str) else k
                int_problems[int_key] = v
            except Exception:
                continue
        dump = {str(k): v for k,v in sorted(int_problems.items())}
        with open(json_file,'w',encoding='utf-8') as jf:
            json.dump(dump, jf, ensure_ascii=False, indent=2)
        logging.info('已保存 JSON: %s', json_file)
    except Exception:
        logging.exception('写入 JSON 失败')

    try:
        with open(json_file,'r',encoding='utf-8') as jf:
            problems_for_sql = json.load(jf)
    except Exception:
        problems_for_sql = all_problems

    # 规范图片引用
    # SQL生成完毕

    try:
        # 不需要规范化图片引用 - JSON中已有正确的路径
        # normalize_problems_image_refs(problems_for_sql)
        pass
    except Exception:
        logging.exception('规范图片引用失败')

    create_sql_file(problems_for_sql, start_id, end_id)

if __name__ == '__main__':
    main()
