import requests
from bs4 import BeautifulSoup
import re
import os
import datetime
import time
import sys
import html
import urllib.parse
from urllib.parse import urljoin
import hashlib

def clean_html_content(content):
    """清理HTML内容中的转义字符"""
    if not content:
        return ""
    
    # 处理常见的转义字符
    content = content.replace('\\"', '"')  # 处理转义的双引号
    content = content.replace("\\'", "'")  # 处理转义的单引号
    content = content.replace('\\\\', '\\')  # 处理转义的反斜杠
    content = html.unescape(content)  # 处理HTML实体
    
    return content

def ensure_paragraph_tags(html_content):
    """确保HTML内容包含段落标签"""
    if not html_content:
        return html_content
    
    # 如果已经包含段落标签或div标签，直接返回
    if '<p>' in html_content or '<div>' in html_content:
        return html_content
    
    # 将内容用段落标签包装
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text().strip()
    
    if not text:
        return html_content
    
    # 将文本分段处理
    paragraphs = re.split(r'\n\s*\n', text)  # 按空行分割段落
    html_paragraphs = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # 将段落内的换行符转换为<br>
            para = para.replace('\n', '<br>')
            html_paragraphs.append(f'<p>{para}</p>')
    
    if html_paragraphs:
        return ''.join(html_paragraphs)
    
    return html_content

def extract_html_from_script(script_content, problem_id, page_url, session):
    """从script标签中提取pshow函数的HTML内容并处理图片"""
    if not script_content:
        return ""
    
    # 查找pshow("内容")模式
    match = re.search(r'pshow\("(.*?)"\)', script_content, re.DOTALL)
    if not match:
        return ""
    
    content = match.group(1)
    # 清理转义字符
    content = clean_html_content(content)
    content = content.replace('\\n', '\n').replace('\\t', '\t')
    
    # 使用BeautifulSoup解析HTML内容
    content_soup = BeautifulSoup(content, 'html.parser')
    
    # 处理图片标签
    content_soup = process_images_in_html(content_soup, problem_id, page_url, session)
    
    # 返回处理后的HTML字符串
    return str(content_soup)

def process_images_in_html(soup, problem_id, page_url, session):
    """处理HTML中的图片标签，下载图片并更新路径为相对路径"""
    try:
        # 查找所有img标签
        img_tags = soup.find_all('img')
        
        if not img_tags:
            return soup
        
        # 确保图片目录存在
        img_dir = os.path.join('image', str(problem_id))
        os.makedirs(img_dir, exist_ok=True)
        
        for img_tag in img_tags:
            src = img_tag.get('src')
            if not src:
                continue
            
            # 清理src中的转义字符
            src = clean_html_content(src)
            
            try:
                # 构建完整的图片URL
                base_url = "http://ybt.ssoier.cn:8088/"
                
                if src.startswith('http'):
                    img_url = src
                elif src.startswith('pic/'):
                    # 处理pic/开头的相对路径
                    img_url = urljoin(base_url, src)
                elif src.startswith('/'):
                    # 处理绝对路径
                    img_url = urljoin(base_url, src[1:])
                else:
                    # 处理其他相对路径
                    img_url = urljoin(page_url, src)
                
                # 下载图片
                img_response = session.get(img_url, timeout=10)
                
                if img_response.status_code == 200:
                    # 从URL中提取原文件名
                    original_filename = os.path.basename(src)
                    if not original_filename:
                        # 如果没有文件名，使用题目ID作为文件名
                        original_filename = f"{problem_id}"
                    
                    # 确定图片扩展名
                    content_type = img_response.headers.get('Content-Type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = '.jpg'
                    elif 'png' in content_type:
                        ext = '.png'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    else:
                        # 尝试从URL中获取扩展名
                        url_ext = os.path.splitext(src)[1]
                        if url_ext and len(url_ext) <= 5:
                            ext = url_ext
                        else:
                            ext = '.jpg'
                    
                    # 如果文件名没有扩展名，添加扩展名
                    filename_without_ext = os.path.splitext(original_filename)[0]
                    if not os.path.splitext(original_filename)[1]:
                        img_filename = f"{filename_without_ext}{ext}"
                    else:
                        img_filename = original_filename
                    
                    # 确保文件名是题目ID
                    img_filename = f"{problem_id}{ext}"
                    
                    img_path = os.path.join(img_dir, img_filename)
                    
                    # 保存图片
                    with open(img_path, 'wb') as f:
                        f.write(img_response.content)
                    print(f"已下载图片: {img_filename}")
                    
                    # 更新img标签的src属性为服务器相对路径
                    new_src = f"/upload/image/{problem_id}/{img_filename}"
                    img_tag['src'] = new_src
                else:
                    print(f"图片下载失败: {img_url}, 状态码: {img_response.status_code}")
                    
            except Exception as e:
                print(f"处理图片时出错: {e}")
                continue
        
        return soup
        
    except Exception as e:
        print(f"处理HTML图片时出错: {e}")
        return soup

def extract_text_from_script(script_content):
    """从script标签中提取pshow函数的文本内容（原功能）"""
    if not script_content:
        return ""
    
    # 查找pshow("内容")模式
    match = re.search(r'pshow\("(.*?)"\)', script_content, re.DOTALL)
    if match:
        content = match.group(1)
        # 清理转义字符
        content = clean_html_content(content)
        content = content.replace('\\n', '\n').replace('\\t', '\t')
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        return content.strip()
    return ""

def crawl_problem(problem_id, session):
    """爬取单个题目 - 增强版：保留HTML标签并下载图片"""
    url = f"http://ybt.ssoier.cn:8088/problem_show.php?pid={problem_id}"
    
    try:
        print(f"正在爬取题目 {problem_id}...")
        response = session.get(url, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 提取标题
        title = ""
        h3_tags = soup.find_all('h3')
        for h3 in h3_tags:
            h3_text = h3.get_text(strip=True)
            if str(problem_id) in h3_text:
                title = h3_text
                break
        
        if not title:
            title = f"{problem_id}：未知题目"
        
        print(f"标题: {title}")
        
        # 2. 提取时间限制和内存限制
        time_limit = "1000"
        memory_limit = "32768"
        
        # 查找包含限制信息的文本
        all_text = soup.get_text()
        
        time_match = re.search(r'时间限制\s*[:：]\s*(\d+)\s*ms', all_text)
        if time_match:
            time_limit = time_match.group(1)
        
        memory_match = re.search(r'内存限制\s*[:：]\s*(\d+)\s*KB', all_text)
        if memory_match:
            memory_limit = memory_match.group(1)
        
        # 3. 提取题目描述、输入、输出 - 保留HTML标签
        problem_description_html = ""
        input_description_html = ""
        output_description_html = ""
        
        problem_description_text = ""
        input_description_text = ""
        output_description_text = ""
        
        input_sample = ""
        output_sample = ""
        
        # 查找所有script标签
        scripts = soup.find_all('script')
        
        # 存储找到的HTML内容
        found_html_contents = []
        # 存储找到的文本内容
        found_text_contents = []
        
        for script in scripts:
            if script.string and 'pshow' in script.string:
                # 提取HTML内容（保留标签）
                html_content = extract_html_from_script(script.string, problem_id, url, session)
                if html_content:
                    found_html_contents.append(html_content)
                
                # 提取文本内容（原功能）
                text_content = extract_text_from_script(script.string)
                if text_content:
                    found_text_contents.append(text_content)
        
        # 根据找到的内容数量分配HTML内容
        if len(found_html_contents) >= 3:
            problem_description_html = found_html_contents[0]
            input_description_html = found_html_contents[1]
            output_description_html = found_html_contents[2]
        elif len(found_html_contents) == 2:
            problem_description_html = found_html_contents[0]
            # 判断哪个是输入，哪个是输出
            if len(found_html_contents[1]) < 100:  # 输入通常较短
                input_description_html = found_html_contents[1]
            else:
                output_description_html = found_html_contents[1]
        elif len(found_html_contents) == 1:
            problem_description_html = found_html_contents[0]
        
        # 根据找到的内容数量分配文本内容（保持与原代码兼容）
        if len(found_text_contents) >= 3:
            problem_description_text = found_text_contents[0]
            input_description_text = found_text_contents[1]
            output_description_text = found_text_contents[2]
        elif len(found_text_contents) == 2:
            problem_description_text = found_text_contents[0]
            if len(found_text_contents[1]) < 100:
                input_description_text = found_text_contents[1]
            else:
                output_description_text = found_text_contents[1]
        elif len(found_text_contents) == 1:
            problem_description_text = found_text_contents[0]
        
        # 4. 提取样例
        # 查找所有pre标签
        pre_tags = soup.find_all('pre')
        if len(pre_tags) >= 2:
            input_sample = pre_tags[0].get_text(strip=False).strip()
            output_sample = pre_tags[1].get_text(strip=False).strip()
        elif len(pre_tags) == 1:
            # 如果只有一个pre标签，可能是输出样例
            output_sample = pre_tags[0].get_text(strip=False).strip()
        
        # 返回整理好的数据
        problem_data = {
            'title': title,
            'description': problem_description_html,  # 使用HTML格式
            'input': input_description_html,  # 使用HTML格式
            'output': output_description_html,  # 使用HTML格式
            'sample_input': input_sample,
            'sample_output': output_sample,
            'time_limit': time_limit,
            'memory_limit': memory_limit,
            # 保留文本版本用于备份
            'description_text': problem_description_text,
            'input_text': input_description_text,
            'output_text': output_description_text
        }
        
        # 打印提取结果
        print(f"提取结果:")
        print(f"  描述: {len(problem_description_html)} 字符")
        print(f"  输入: {len(input_description_html)} 字符")
        print(f"  输出: {len(output_description_html)} 字符")
        print(f"  输入样例: {len(input_sample)} 字符")
        print(f"  输出样例: {len(output_sample)} 字符")
        
        return problem_data
        
    except Exception as e:
        print(f"爬取题目 {problem_id} 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_sample_files(problem_data, problem_id):
    """保存样例文件"""
    if not problem_data:
        return False
    
    try:
        # 提取题目编号
        match = re.match(r'^(\d+)', problem_data['title'])
        if match:
            problem_num = match.group(1)
        else:
            problem_num = str(problem_id)
        
        # 创建目录
        problem_dir = os.path.join('data', problem_num)
        os.makedirs(problem_dir, exist_ok=True)
        
        # 保存输入样例
        with open(os.path.join(problem_dir, 'sample.in'), 'w', encoding='utf-8') as f:
            f.write(problem_data['sample_input'])
        
        # 保存输出样例
        with open(os.path.join(problem_dir, 'sample.out'), 'w', encoding='utf-8') as f:
            f.write(problem_data['sample_output'])
        
        print(f"已保存样例文件到: {problem_dir}")
        return True
        
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False

def generate_sql_insert(problem_data, problem_id):
    """生成SQL插入语句 - 使用HTML内容"""
    if not problem_data:
        return None
    
    try:
        # 转义特殊字符 - 修复单引号转义问题
        def escape_sql(text):
            if not text:
                return ''
            # 首先清理转义字符
            text = clean_html_content(text)
            # 然后转义SQL特殊字符
            text = text.replace('\\', '\\\\')
            text = text.replace("'", "''")
            return text
        
        # 准备数据 - 使用HTML内容，并确保有段落标签
        description = ensure_paragraph_tags(problem_data.get('description', ''))
        input_desc = ensure_paragraph_tags(problem_data.get('input', ''))
        output_desc = ensure_paragraph_tags(problem_data.get('output', ''))
        
        title = escape_sql(problem_data['title'])
        description = escape_sql(description)
        input_desc = escape_sql(input_desc)
        output_desc = escape_sql(output_desc)
        sample_input = escape_sql(problem_data['sample_input'])
        sample_output = escape_sql(problem_data['sample_output'])
        
        # 如果HTML内容为空，回退到文本内容
        if not description and 'description_text' in problem_data:
            description_text = ensure_paragraph_tags(problem_data['description_text'])
            description = escape_sql(description_text)
        if not input_desc and 'input_text' in problem_data:
            input_text = ensure_paragraph_tags(problem_data['input_text'])
            input_desc = escape_sql(input_text)
        if not output_desc and 'output_text' in problem_data:
            output_text = ensure_paragraph_tags(problem_data['output_text'])
            output_desc = escape_sql(output_text)
        
        # 处理时间限制（ms转秒）
        time_limit = float(problem_data['time_limit']) / 1000
        
        # 处理内存限制（KB转MB）
        memory_limit = int(problem_data['memory_limit']) // 1024
        
        # 当前时间
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成SQL
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
        
    except Exception as e:
        print(f"生成SQL时出错: {e}")
        return None

def create_sql_file(problems, start_id, end_id):
    """创建完整的SQL文件"""
    sql_file = f"problems_{start_id}_{end_id}.sql"
    
    # SQL文件开头
    sql_content = """-- 设置字符集
SET NAMES utf8mb4;

-- 创建数据库
CREATE DATABASE IF NOT EXISTS jol CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE jol;

-- 创建problem表
CREATE TABLE IF NOT EXISTS `problem` (
  `problem_id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL DEFAULT '',
  `description` mediumtext,
  `input` mediumtext,
  `output` mediumtext,
  `sample_input` text,
  `sample_output` text,
  `spj` char(1) NOT NULL DEFAULT '0',
  `hint` mediumtext,
  `source` varchar(100) DEFAULT NULL,
  `in_date` datetime DEFAULT NULL,
  `time_limit` DECIMAL(10,3) NOT NULL DEFAULT 0,
  `memory_limit` int(11) NOT NULL DEFAULT 0,
  `defunct` char(1) NOT NULL DEFAULT 'N',
  `accepted` int(11) DEFAULT '0',
  `submit` int(11) DEFAULT '0',
  `solved` int(11) DEFAULT '0',
  `remote_oj` varchar(16) DEFAULT NULL,
  `remote_id` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`problem_id`)
) ENGINE=MyISAM AUTO_INCREMENT=1000 DEFAULT CHARSET=utf8mb4;

-- 插入题目数据
"""

    # 添加每个题目的SQL
    for problem_id, problem_data in problems.items():
        if problem_data:
            sql = generate_sql_insert(problem_data, problem_id)
            if sql:
                sql_content += sql + "\n\n"
    
    # 写入文件
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"SQL文件已保存到: {sql_file}")
    return sql_file

def main():
    print("=" * 60)
    print("信息学奥赛一本通题目爬取工具 - 最终版")
    print("功能说明:")
    print("1. 保留HTML标签和原网页格式")
    print("2. 自动添加段落标签<p>和换行标签<br>")
    print("3. 自动下载图片并保存为原文件名")
    print("4. 图片路径格式: /upload/image/{题目ID}/{题目ID}.jpg")
    print("5. 生成完整的SQL文件")
    print("=" * 60)
    
    # 设置爬取范围
    start_id = 1445
    end_id = 1445
    
    # 从命令行参数获取范围
    if len(sys.argv) >= 3:
        try:
            start_id = int(sys.argv[1])
            end_id = int(sys.argv[2])
        except ValueError:
            print("参数错误，使用默认范围 1445-1445")
    
    print(f"爬取范围: {start_id} - {end_id}")
    print(f"预计爬取题目数: {end_id - start_id + 1}")
    print("开始爬取...\n")
    
    # 确保必要的目录存在
    for dir_name in ['data', 'image']:
        os.makedirs(dir_name, exist_ok=True)
    
    # 创建session保持连接
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # 存储所有题目数据
    all_problems = {}
    success_count = 0
    fail_count = 0
    
    # 爬取每个题目
    for problem_id in range(start_id, end_id + 1):
        problem_data = crawl_problem(problem_id, session)
        
        if problem_data:
            # 保存样例文件
            save_sample_files(problem_data, problem_id)
            
            # 存储数据
            all_problems[problem_id] = problem_data
            success_count += 1
            
            print(f"题目 {problem_id} 爬取成功")
        else:
            fail_count += 1
            # 创建空目录和空文件
            problem_dir = os.path.join('data', str(problem_id))
            os.makedirs(problem_dir, exist_ok=True)
            with open(os.path.join(problem_dir, 'sample.in'), 'w') as f:
                f.write('')
            with open(os.path.join(problem_dir, 'sample.out'), 'w') as f:
                f.write('')
            
            # 创建默认数据
            default_data = {
                'title': f"{problem_id}：题目不存在",
                'description': '题目不存在或无法访问',
                'input': '',
                'output': '',
                'sample_input': '',
                'sample_output': '',
                'time_limit': '1000',
                'memory_limit': '32768'
            }
            all_problems[problem_id] = default_data
            print(f"题目 {problem_id} 爬取失败，使用默认数据")
        
        # 添加延迟，避免请求过快
        time.sleep(1)
    
    # 生成SQL文件
    create_sql_file(all_problems, start_id, end_id)
    
    # 输出统计信息
    print("\n" + "=" * 60)
    print("爬取完成!")
    print(f"成功爬取: {success_count} 个题目")
    print(f"失败: {fail_count} 个题目")
    print(f"SQL文件已保存到: problems_{start_id}_{end_id}.sql")
    print(f"题目文件已保存到: data/ 目录")
    print(f"图片文件已保存到: image/ 目录")
    print("=" * 60)

if __name__ == "__main__":
    main()
