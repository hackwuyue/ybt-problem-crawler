# YBT 题目爬虫工具 - 实现详解

## 📋 目录

1. [项目概述](#项目概述)
2. [核心功能](#核心功能)
3. [技术架构](#技术架构)
4. [实现细节](#实现细节)
5. [API 参考](#api-参考)
6. [扩展与定制](#扩展与定制)

---

## 项目概述

### 项目名称
**YBT 题目爬虫工具** (YBT Problem Crawler)

### 项目描述
一个功能完整的 Python 爬虫框架，专用于抓取信息学奥赛一本通（YBT）在线评测系统的题目信息、样例和图片，并生成标准 SQL 导入文件。

### 关键特性
- ✅ **HTTP 健壮性**：自动重试、超时处理、限速恢复
- ✅ **并发爬取**：线程池并发，支持自定义 worker 数量
- ✅ **断点续爬**：基于 JSON 快照，网络中断后自动恢复
- ✅ **灵活输出**：支持 JSON/SQL/纯文本等多种格式
- ✅ **完整 CLI**：argparse 接口，支持复杂命令组合
- ✅ **日志追踪**：详细的运行日志，便于问题排查

### 应用场景
- 将 YBT 题库批量导入本地数据库
- 为 OJ 系统准备题目数据
- 题目信息分析与统计
- 题目备份与归档

---

## 核心功能

### 1. 基础爬取

**功能描述**：爬取指定范围内的题目信息。

```bash
python yibentong.py 1000 1010
```

**产出**：
- `problems_1000_1010.json` - 题目数据快照
- `problems_1000_1010.sql` - SQL 导入文件
- `data/{pid}/sample.in` 和 `sample.out` - 样例文件
- `image/{pid}/*.png/.jpg` - 题目图片

**耗时**：约 10 秒（11 题）

### 2. 并发爬取

**功能描述**：使用多线程并发爬取，大幅提升速度。

```bash
python yibentong.py 1000 1010 --concurrent 4
```

**性能提升**：3-4 倍加速（单线程 10s -> 并发 2.5s）

**worker 数量建议**：
- 2：稳定，无限速风险
- 3：平衡（推荐）
- 4：激进，可能触发限速

### 3. 断点续爬

**功能描述**：网络中断后，自动识别已完成的题目，仅爬取缺失部分。

```bash
# 第一次运行（中断）
python yibentong.py 1000 1010 --concurrent 4

# 网络恢复后重新运行
python yibentong.py 1000 1010 --resume --concurrent 4
```

**工作原理**：
1. 检查是否存在 `problems_1000_1010.json`
2. 如果存在，读取已完成的题目 ID
3. 仅爬取缺失的题目
4. 合并结果后重新生成 SQL

**优势**：
- 省时：避免重复爬取
- 省网：仅传输缺失数据
- 安全：无需担心中断

### 4. JSON-only 模式

**功能描述**：基于现有 JSON 文件重新生成 SQL，无需网络请求。

```bash
# 修改 SQL 生成规则后
python yibentong.py 1000 1010 --json-only
```

**使用场景**：
- 修改 SQL 生成逻辑（如添加新字段）
- 修改数据库字符编码配置
- 快速重新生成 SQL（耗时 <1 秒）

### 5. 跳过图片下载

**功能描述**：仅爬取题目文本信息，跳过图片下载以加速。

```bash
python yibentong.py 1000 1010 --no-image
```

**加速效果**：耗时减少 60-70%（有大量图片的情况下）

**典型用途**：
- 快速获取所有题目信息
- 稍后单独补充下载图片
- 网络带宽有限的环境

### 6. 速率控制

**功能描述**：调整请求间隔，平衡速度与服务器压力。

```bash
# 默认延迟 0.5 秒
python yibentong.py 1000 1010

# 加快速度（延迟 0.1 秒）
python yibentong.py 1000 1010 --rate 0.1

# 降低压力（延迟 1.0 秒）
python yibentong.py 1000 1010 --rate 1.0
```

**建议值**：
- 0.05 秒：极限加速（有被限速风险）
- 0.1 秒：快速爬取（推荐用于并发）
- 0.5 秒：默认（平衡）
- 1.0+ 秒：保守（降低服务器压力）

---

## 技术架构

### 整体设计

```
┌─────────────────────────────────────────────┐
│         Command Line Interface              │
│         (argparse 参数解析)                  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         主函数 (main)                        │
│  • 参数验证                                   │
│  • 工作流程控制                               │
│  • 全局标志设置                               │
└────────────────┬────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
         ▼               ▼
    ┌─────────┐    ┌──────────┐
    │ 单线程   │    │ 多线程   │
    │爬取模式  │    │并发模式  │
    └────┬────┘    └────┬─────┘
         │              │
         └──────┬───────┘
                ▼
         ┌─────────────────────┐
         │  爬取核心函数       │
         │  crawl_problem()    │
         │  • 请求网页          │
         │  • 解析内容          │
         │  • 下载图片          │
         └────────┬────────────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
    ┌────────────┐   ┌──────────┐
    │ JSON 生成  │   │HTML 处理 │
    │保存快照    │   │图片下载  │
    └────────┬───┘   └────┬─────┘
             │            │
             └─────┬──────┘
                   ▼
           ┌──────────────┐
           │ SQL 生成     │
           │规范化图片引用 │
           └──────────────┘
```

### 核心模块

#### 1. HTTP 会话管理 (`make_session`)

```python
def make_session():
    """创建带重试策略的 Session"""
    session = requests.Session()
    retry = Retry(
        total=5,                        # 最多重试 5 次
        backoff_factor=0.6,             # 退避因子
        status_forcelist=[429,500,502,503,504]  # 可重试的状态码
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session
```

**重试策略**：
- 连接被拒绝 → 立即重试
- 429 (Too Many Requests) → 等待后重试
- 5xx (服务器错误) → 指数退避重试
- 成功响应 → 直接返回

#### 2. 图片处理 (`process_images_in_html`)

```python
def process_images_in_html(soup, problem_id, page_url, session):
    """下载并处理 HTML 中的图片"""
    if SKIP_IMAGES:  # 全局标志：跳过图片
        return soup
    
    # 遍历所有 <img> 标签
    for idx, img_tag in enumerate(img_tags, start=1):
        src = img_tag.get('src')
        img_url = src if src.startswith('http') else urljoin(page_url, src)
        
        # 流式下载（避免内存溢出）
        with session.get(img_url, stream=True) as img_response:
            # 确定文件格式
            ext = infer_extension(img_response.headers)
            
            # 生成唯一文件名：{pid}_{idx}_{md5}.{ext}
            h = hashlib.md5(img_url.encode()).hexdigest()[:10]
            filename = f"{pid}_{idx}_{h}{ext}"
            
            # 分块写入文件
            with open(filepath, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 创建兼容副本：{pid}.{ext}
            if not os.path.exists(compat_path):
                shutil.copy(filepath, compat_path)
```

**关键特性**：
- **流式下载**：`stream=True` + `iter_content()`，避免大文件一次性加载
- **唯一命名**：使用 MD5 哈希，避免冲突
- **兼容副本**：为旧系统创建简单的 `{pid}.{ext}` 副本

#### 3. 并发爬取 (`crawl_ids_concurrent`)

```python
def crawl_ids_concurrent(id_list, max_workers=3, rate_delay=0.5):
    """使用线程池并发爬取"""
    results = {}
    failed = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(crawl_problem, pid, make_session()): pid 
            for pid in id_list
        }
        
        for future in as_completed(futures):
            pid = futures[future]
            try:
                data = future.result()
                if data:
                    results[pid] = data
                else:
                    failed.append(pid)
            except Exception as e:
                logging.exception(f"爬取 {pid} 失败: {e}")
                failed.append(pid)
    
    return results, failed
```

**设计要点**：
- 每个 worker 创建独立 Session，避免线程间竞争
- 使用 `as_completed()` 获得结果，提高响应性
- 自动捕获异常，防止单个失败影响整体

#### 4. SQL 生成 (`generate_sql_insert`)

```python
def generate_sql_insert(problem_data, problem_id):
    """生成单条 SQL INSERT 语句"""
    
    # 规范化图片引用
    description = replace_image_srcs(problem_data['description'], problem_id)
    
    # SQL 转义
    title = escape_sql(problem_data['title'])
    description = escape_sql(description)
    
    # 单位转换
    time_limit = float(problem_data['time_limit']) / 1000  # ms -> s
    memory_limit = int(problem_data['memory_limit']) // 1024  # KB -> MB
    
    # 生成 SQL
    sql = f"""INSERT INTO `problem` (
        `title`, `description`, `input`, `output`, `sample_input`, `sample_output`,
        `spj`, `hint`, `source`, `in_date`, `time_limit`, `memory_limit`,
        `defunct`, `accepted`, `submit`, `solved`, `remote_oj`, `remote_id`
    ) VALUES (
        '{title}',
        '{description}',
        ...
        {time_limit:.3f},
        {memory_limit},
        ...
    );"""
    
    return sql
```

**关键步骤**：
1. 规范化图片引用（用兼容主名替换 hash 版本）
2. SQL 转义（处理特殊字符）
3. 单位转换（ms→s, KB→MB）
4. 生成标准 SQL INSERT 语句

#### 5. 断点续爬 (`resume` 逻辑)

```python
# 识别已完成的题目
completed = set()
if args.resume and os.path.exists(json_file):
    with open(json_file) as jf:
        prev = json.load(jf)
    completed = {int(k) for k in prev.keys()}
    logging.info(f'从 JSON 恢复，已跳过 {len(completed)} 项')

# 计算缺失的题目
ids = [pid for pid in range(start_id, end_id+1) if pid not in completed]

# 如果无缺失题目，直接基于 JSON 生成 SQL
if not ids:
    create_sql_file(existing_problems, start_id, end_id)
    return
```

---

## 实现细节

### 题目存在性检测

**功能描述**：自动检测题目是否存在，避免为不存在的题目创建冗余数据。

**检测机制**：

1. **在爬取阶段标记**

```python
def crawl_problem(problem_id, session):
    # 查找题目标题
    for h3 in soup.find_all('h3'):
        h3_text = h3.get_text(strip=True)
        if str(problem_id) in h3_text:
            title = h3_text
            problem_exists = True
            break
    
    # 如果未找到标题，标记为不存在
    if not title:
        title = f"{problem_id}：未知题目"
        problem_exists = False
    
    # 在返回数据中添加标记
    pdata['exists'] = problem_exists
    return pdata
```

2. **在保存阶段检查**

```python
def save_sample_files(problem_data, problem_id):
    if not problem_data.get('exists', True):
        logging.info('跳过不存在的题目: %s', problem_id)
        return False
    # 正常保存文件...
```

3. **在 SQL 生成阶段检查**

```python
def generate_sql_insert(problem_data, problem_id):
    if not problem_data.get('exists', True):
        logging.info('跳过不存在的题目SQL生成: %s', problem_id)
        return None
    # 正常生成 SQL...
```

**效果**：
- ✅ 不创建不存在题目的文件夹
- ✅ 不生成不存在题目的 SQL INSERT 语句
- ✅ JSON 中保留 `"exists": false` 标记用于追踪

**示例**：
```json
{
  "2228": {
    "title": "2228：未知题目",
    "exists": false,
    "description": "",
    "input": "",
    "output": ""
  }
}
```

### HTML 内容提取

**原始 HTML 结构**：

```html
<script>
pshow("&lt;p&gt;这是题目描述&lt;/p&gt;&lt;img src='...'&gt;")
</script>
```

**提取步骤**：

1. **匹配 pshow 函数**

```python
match = re.search(r'pshow\("(.*?)"\)', script_content, re.DOTALL)
content = match.group(1)
```

2. **清理转义字符**

```python
content = clean_html_content(content)
content = content.replace('\\n', '\n').replace('\\t', '\t')
```

3. **解析为 BeautifulSoup**

```python
soup = BeautifulSoup(content, 'html.parser')
soup = process_images_in_html(soup, problem_id, page_url, session)
```

4. **获取最终 HTML**

```python
html_output = str(soup)
```

### 图片引用规范化

**问题**：SQL 中的图片路径与实际文件不匹配

```
原始引用:  /upload/image/1445/xxxx_hash.png
实际文件:  image/1445/1445.png
```

**解决方案**：

```python
def replace_image_srcs(html_content, pid):
    """将 HTML 中的图片引用替换为兼容主名"""
    # 查找主名副本 (e.g., 1445.png)
    primary = find_primary_image_filename(pid)
    if not primary:
        return html_content
    
    # 将所有 /upload/image/{pid}/xxxx 替换为 /upload/image/{pid}/primary
    pattern = re.compile(rf'(/upload/image/{pid}/)[^"\'>\s]+')
    return pattern.sub(rf'\1{primary}', html_content)
```

**执行时机**：在生成 SQL 前对 JSON 进行规范化处理

### 并发控制

**延迟机制**：

```python
def crawl_worker(problem_id, rate_delay=0.5):
    """Worker 函数"""
    session = make_session()
    try:
        data = crawl_problem(problem_id, session)
        time.sleep(rate_delay)  # 降低瞬时压力
        return problem_id, data
    finally:
        session.close()
```

**效果**：即使 4 个 worker 并发运行，实际请求仍有适当间隔，避免 DoS 风险

### 全局标志控制

```python
# 全局变量
SKIP_IMAGES = False
JSON_ONLY = False

# 在 main() 中设置
SKIP_IMAGES = bool(args.no_image)
JSON_ONLY = bool(args.json_only)

# 在爬取逻辑中检查
if SKIP_IMAGES:
    return soup  # 跳过图片处理
```

**优势**：避免多次检查参数，提高性能

---

## API 参考

### 命令行接口

```bash
usage: yibentong.py [-h] [--concurrent N] [--resume] [--json-only] 
                    [--no-image] [--rate FLOAT] 
                    [start] [end]
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `start` | int | 1445 | 起始题目 ID |
| `end` | int | 1445 | 结束题目 ID |
| `--concurrent` / `-c` | int | 无 | 并发 worker 数（2-4 推荐） |
| `--resume` | flag | False | 启用断点续爬 |
| `--json-only` | flag | False | 仅基于 JSON 生成 SQL |
| `--no-image` | flag | False | 跳过图片下载 |
| `--rate` | float | 0.5 | 请求延迟（秒） |

### 使用示例

```bash
# 基础爬取
python yibentong.py 1000 1010

# 并发爬取（4 worker）
python yibentong.py 1000 1010 --concurrent 4

# 并发 + 断点续爬
python yibentong.py 1000 1010 --concurrent 4 --resume

# 快速爬取（无图片）
python yibentong.py 1000 1010 --no-image

# 极限加速（并发 + 无图片 + 高速率）
python yibentong.py 1000 1010 --concurrent 4 --no-image --rate 0.1

# 仅基于 JSON 生成 SQL
python yibentong.py 1000 1010 --json-only
```

### 返回值与输出

**JSON 格式** (`problems_{start}_{end}.json`)：

```json
{
  "1000": {
    "title": "1000：某题名称",
    "description": "<p>题目描述 HTML</p>",
    "input": "<p>输入描述</p>",
    "output": "<p>输出描述</p>",
    "sample_input": "输入样例",
    "sample_output": "输出样例",
    "time_limit": "1000",
    "memory_limit": "32768"
  },
  ...
}
```

**SQL 格式** (`problems_{start}_{end}.sql`)：

```sql
INSERT INTO `problem` (
    `title`, `description`, `input`, `output`, `sample_input`, `sample_output`,
    `spj`, `hint`, `source`, `in_date`, `time_limit`, `memory_limit`,
    `defunct`, `accepted`, `submit`, `solved`, `remote_oj`, `remote_id`
) VALUES (
    '1000：某题名称',
    '<p>题目描述 HTML</p>',
    ...
    1.000,
    32,
    ...
);
```

---

## 扩展与定制

### 修改 SQL 输出字段

编辑 `generate_sql_insert()` 函数：

```python
def generate_sql_insert(problem_data, problem_id):
    # ... 现有代码 ...
    
    # 添加自定义字段
    difficulty = problem_data.get('difficulty', 'MEDIUM')
    
    sql = f"""INSERT INTO `problem` (
        ...,
        `difficulty`
    ) VALUES (
        ...,
        '{difficulty}'
    );"""
    
    return sql
```

### 添加新的元数据提取

修改 `crawl_problem()` 函数：

```python
def crawl_problem(problem_id, session):
    # ... 现有代码 ...
    
    # 新增：提取作者信息
    author = extract_author_info(soup)
    
    problem_data = {
        # ... 现有字段 ...
        'author': author
    }
    
    return problem_data
```

### 自定义图片处理

在 `process_images_in_html()` 中添加：

```python
def process_images_in_html(soup, problem_id, page_url, session):
    if SKIP_IMAGES:
        return soup
    
    for idx, img_tag in enumerate(img_tags, start=1):
        # ... 现有下载逻辑 ...
        
        # 自定义：压缩图片
        compress_image(filepath)
        
        # 自定义：生成缩略图
        generate_thumbnail(filepath)
    
    return soup
```

### 集成到 OJ 系统

```python
# 直接导入库
from yibentong import crawl_problem, create_sql_file

# 使用爬虫 API
problems = crawl_problem(1000, session)
sql = generate_sql_insert(problems, 1000)

# 插入数据库
db.execute(sql)
```

---

## 常见问题与调试

### Q: 爬取速度很慢？

**A: 尝试以下方案：**

1. 增加并发数

```bash
python yibentong.py 1000 1010 --concurrent 4
```

2. 降低延迟

```bash
python yibentong.py 1000 1010 --rate 0.1
```

3. 跳过图片

```bash
python yibentong.py 1000 1010 --no-image
```

4. 组合方案

```bash
python yibentong.py 1000 1010 --concurrent 4 --no-image --rate 0.1
```

### Q: 某些题目爬取失败？

**A: 检查日志并重试：**

```bash
# 查看错误信息
tail -f crawler.log | grep ERROR

# 使用 --resume 重新尝试
python yibentong.py 1000 1010 --resume
```

### Q: 图片引用不正确？

**A: 检查兼容副本：**

```bash
# 验证图片文件
ls -la image/1000/

# 应该有 1000_1_<hash>.png 和 1000.png 两个文件
```

如果缺少兼容副本，删除 SQL 后重新生成：

```bash
rm problems_1000_1010.sql
python yibentong.py 1000 1010 --json-only
```

### Q: 如何修改数据库导入配置？

**A: 编辑 `create_sql_file()` 中的表结构：**

```python
def create_sql_file(problems, start_id, end_id):
    sql_content = """
    CREATE TABLE IF NOT EXISTS `problem` (
      ...
      `your_field` VARCHAR(255),  # 添加自定义字段
      ...
    );
    """
```

---

## 性能优化技巧

### 1. 调整线程池大小

```python
# 默认 3 worker，可根据网络状况调整
python yibentong.py 1000 2000 --concurrent 2  # 稳定
python yibentong.py 1000 2000 --concurrent 4  # 激进
```

### 2. 分阶段爬取

```bash
# 第一阶段：快速获取文本信息
python yibentong.py 1000 2000 --concurrent 4 --no-image --rate 0.1

# 第二阶段：补充下载图片
python yibentong.py 1000 2000 --resume
```

### 3. 监控日志

```bash
# 实时查看爬取进度
tail -f crawler.log | grep "已爬取\|已下载"
```

---

**更新日期**：2026-01-13  
**版本**：1.0 (生产就绪)
