# 信息学奥赛一本通题目爬取工具

一个功能完整的 Python 爬虫，用于抓取 YBT（信息学奥赛一本通）在线评测系统的题目信息、样例和图片，并生成 SQL 导入文件。

## 功能特性

✅ **智能题目检测**
- 自动检测不存在的题目
- 不为不存在的题目创建文件夹或生成 SQL
- 跳过无效题目，保持数据库整洁

✅ **HTTP 请求健壮性**
- 自动重试（5次，带退避）处理超时和服务器错误
- 支持 429（速率限制）和 5xx（服务器错误）自动恢复

✅ **图片处理**
- 流式下载图片避免内存溢出
- 按题目ID和MD5哈希唯一命名：`{pid}_{idx}_{md5}.{ext}`
- 自动创建兼容副本：`{pid}.{ext}`（供旧系统兼容）

✅ **并发爬取**
- 线程池并发爬取，可配置 worker 数量
- 自动降低瞬时压力的速率延迟

✅ **断点续爬**
- 基于中间 JSON 快照识别已完成题目
- 仅爬取缺失题目，自动合并结果

✅ **灵活输出**
- 保存中间 JSON 快照（`problems_{start}_{end}.json`）
- 生成标准 SQL 导入文件（`problems_{start}_{end}.sql`）
- 支持图片引用规范化（自动替换为兼容主名）

✅ **日志追踪**
- 彩色控制台输出 + 文件日志（`crawler.log`）
- 包含图片下载、错误重试等详细信息

## 安装

```bash
pip install requests beautifulsoup4 urllib3
```

## 使用方法

### 基本爬取

爬取题目 1000 到 1010：

```bash
python yibentong.py 1000 1010
```

### 并发爬取

使用 4 个 worker 线程并发爬取：

```bash
python yibentong.py 1000 1010 --concurrent 4
```

### 断点续爬

跳过已完成的题目，仅爬取缺失部分（基于现有 JSON）：

```bash
python yibentong.py 1000 1010 --resume --concurrent 4
```

### 仅基于 JSON 生成 SQL

如果已有 JSON 文件（`problems_1000_1010.json`），可直接基于它生成或重新生成 SQL：

```bash
python yibentong.py 1000 1010 --json-only
```

### 跳过图片下载

仅爬取题目信息（不下载图片），加速爬取：

```bash
python yibentong.py 1000 1010 --no-image
```

### 调整请求延迟

设置请求间隔为 0.2 秒（默认 0.5 秒），提高爬取速度：

```bash
python yibentong.py 1000 1010 --rate 0.2
```

### 组合选项示例

并发爬取、启用断点续爬、跳过图片、低延迟：

```bash
python yibentong.py 1000 1010 --concurrent 4 --resume --no-image --rate 0.1
```

## CLI 选项参考

```
positional arguments:
  start                起始题目ID（默认 1445）
  end                  结束题目ID（默认 1445）

optional arguments:
  -c, --concurrent N   启用并发爬取，N 为 worker 数量（默认 3）
  --resume             从已有 JSON 恢复，跳过已完成的题目
  --json-only          仅基于现有 JSON 生成 SQL，不进行网络爬取
  --no-image           跳过图片下载（仅爬取题目信息）
  --rate FLOAT         请求间隔（秒），默认 0.5
```

## 输出文件结构

```
├── yibentong.py              爬虫主脚本
├── crawler.log               运行日志
├── problems_1000_1010.json   题目数据快照（中间文件）
├── problems_1000_1010.sql    SQL 导入文件
├── data/
│   ├── 1000/
│   │   ├── sample.in         输入样例
│   │   └── sample.out        输出样例
│   ├── 1001/
│   │   ...
│   └── 1010/
└── image/
    ├── 1000/
    │   ├── 1000_1_<hash>.png 原始图片（带哈希）
    │   └── 1000.png          兼容副本
    ├── 1001/
    │   ...
    └── 1010/
```

## 工作流程示例

### 场景 1：首次大规模爬取

```bash
# 并发爬取 1000-2000，4 个 worker，跳过图片以加速
python yibentong.py 1000 2000 --concurrent 4 --no-image
# 结果：JSON + SQL 生成完成，耗时约 5 分钟
```

### 场景 2：补充下载缺失的图片

```bash
# 基于现有 JSON 再次爬取，启用图片但跳过已完成的题目
python yibentong.py 1000 2000 --resume
# 仅重新爬取上次失败的题目并下载图片
```

### 场景 3：修改生成规则后重新生成 SQL

```bash
# 假设修改了 SQL 生成逻辑，直接从 JSON 重新生成（无需重新爬取网页）
python yibentong.py 1000 2000 --json-only
```

## 常见问题

**Q: 爬取被限速或中断怎么办？**  
A: 使用 `--resume` 重新运行相同命令，脚本会自动跳过已完成的题目。

**Q: 图片没有下载成功怎么办？**  
A: 检查 `crawler.log` 中的错误信息。可以用 `--resume` 重新尝试失败的题目。

**Q: 如何仅更新 SQL 而不重新爬取网页？**  
A: 如果 JSON 文件已存在，使用 `--json-only` 选项仅基于 JSON 生成 SQL。

**Q: 并发数应该设置多少？**  
A: 建议 2-4，过高可能被服务器限速或 IP 被封。监控日志判断最佳值。

## 许可

无，仅供学习和个人使用。

## 更新日志

- **v1.1** (2026-01-13)
  - ✨ 添加智能题目检测：跳过不存在的题目
  - ✨ 不为不存在的题目创建数据文件夹
  - ✨ 不为不存在的题目生成 SQL INSERT 语句
  - 📝 在 JSON 中添加 `"exists"` 标记

- **v1.0** (2026-01-13)
  - ✨ 完整 argparse CLI 接口
  - ✨ 断点续爬 (`--resume`)
  - ✨ JSON-only 模式 (`--json-only`)
  - ✨ 跳过图片模式 (`--no-image`)
  - ✨ HTTP 重试 + 日志记录
  - ✨ 并发爬取（ThreadPoolExecutor）
  - ✨ 图片兼容副本自动生成
  - ✨ SQL 图片引用规范化
