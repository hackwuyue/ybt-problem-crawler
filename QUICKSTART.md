# 快速开始指南

## 安装依赖

```bash
pip install requests beautifulsoup4 urllib3
```

## 最常见的用法

### 1. 爬取一个范围内的所有题目

```bash
python yibentong.py 1000 1100
```

这会：
- 按顺序爬取题目 1000-1100（共 101 个）
- 保存样例文件到 `data/{pid}/` 目录
- 下载所有图片到 `image/{pid}/` 目录
- 生成 `problems_1000_1100.json`（中间数据）
- 生成 `problems_1000_1100.sql`（导入文件）

耗时：约 100 秒（每题约 1 秒）

---

### 2. 用并发加快速度

```bash
python yibentong.py 1000 1100 --concurrent 4
```

这会用 4 个线程并行爬取，**耗时约 30 秒**（快 3 倍）。

**建议**：
- worker 数 = 2-4（过多可能被限速）
- 对于 >500 题的范围，使用 `--concurrent 3` 是最佳平衡

---

### 3. 中途中断后继续爬取

假设爬到一半时网络断掉，直接重新运行：

```bash
python yibentong.py 1000 1100 --resume --concurrent 4
```

这会：
- 自动检测已有的 `problems_1000_1100.json`
- 跳过已完成的题目
- 仅爬取缺失的部分
- 合并结果后重新生成 SQL

**优点**：省时省网络，避免重复爬取

---

### 4. 快速修改规则并重新生成 SQL

修改了 SQL 生成代码或格式化规则后，无需重新爬取网页，直接：

```bash
python yibentong.py 1000 1100 --json-only
```

这会：
- 加载现有的 JSON 文件
- **不进行任何网络请求**
- 直接生成新的 SQL 文件

**耗时**：<1 秒

---

### 5. 仅爬取题目信息，跳过图片

如果只关心题目描述和样例，不需要图片：

```bash
python yibentong.py 1000 1100 --no-image
```

这会：
- 爬取所有题目信息和样例
- **不下载任何图片**
- 生成 JSON 和 SQL

**耗时**：约 30 秒（快 3 倍）

**组合使用**：

```bash
python yibentong.py 1000 1100 --concurrent 4 --no-image
```

**耗时**：约 10 秒（非常快）

---

## 其他选项

### `--rate` 控制请求延迟

默认每题延迟 0.5 秒。如果想更快：

```bash
python yibentong.py 1000 1100 --rate 0.1
```

**警告**：过低的延迟可能导致服务器限速或 IP 被封。不建议低于 0.05 秒。

### `-c` 缩写

`--concurrent` 可以缩写为 `-c`：

```bash
python yibentong.py 1000 1100 -c 4
```

---

## 完整工作流程示例

```bash
# 第 1 步：首次大规模爬取，并发 + 跳过图片，快速构建 JSON
python yibentong.py 1000 2000 -c 4 --no-image
# 耗时：~250 秒 / 1000 题 = 4 题/秒

# 第 2 步：检查结果和日志
# 查看 crawler.log，确保没有重大错误

# 第 3 步：补充下载图片（基于现有 JSON，仅重试失败项）
python yibentong.py 1000 2000 --resume
# 耗时：~1000 秒（所有 1000 题的图片）

# 第 4 步：修改 SQL 生成规则（如添加新字段）
# 编辑 yibentong.py 中的 generate_sql_insert()
# 然后不需要重新爬取，直接重新生成 SQL
python yibentong.py 1000 2000 --json-only
# 耗时：<1 秒
```

---

## 输出文件位置

爬取完成后，查看以下文件：

```
.
├── crawler.log                     运行日志（查看错误信息）
├── problems_1000_2000.json         题目数据快照（可备份）
├── problems_1000_2000.sql          SQL 导入文件（导入数据库）
├── data/
│   ├── 1000/
│   │   ├── sample.in              输入样例
│   │   └── sample.out             输出样例
│   ├── 1001/
│   │   ...
│   └── 2000/
└── image/
    ├── 1000/
    │   ├── 1000_1_<hash>.png      原始图片（带 MD5 哈希）
    │   └── 1000.png               兼容副本（旧系统用）
    ├── 1001/
    │   ...
    └── 2000/
```

---

## 常见问题

**Q: 爬取到一半被限速了怎么办？**

A: 直接用 `--resume` 重新运行，脚本会自动跳过已完成的题目。

```bash
python yibentong.py 1000 2000 --resume --concurrent 4
```

**Q: 某些题目爬取失败了怎么办？**

A: 查看 `crawler.log` 找到失败原因。常见原因：
- 网络超时：增加 `--rate` 延迟再试
- 页面不存在：检查题目 ID 是否有效
- 服务器过载：等待后再重试

**Q: 如何只爬取某个特定的题目？**

A: 爬取范围可以相同，如只爬题目 1234：

```bash
python yibentong.py 1234 1234
```

**Q: 能否提高并发数来加速？**

A: 可以，但不推荐超过 4。建议测试值：
- 2：稳定，无限速风险
- 3：平衡（推荐）
- 4：激进，可能触发限速

**Q: 图片文件名为什么这么复杂？**

A: 图片名 `1445_1_06521b018a.png` 的含义：
- `1445`：题目 ID
- `1`：该题目的第 1 张图片
- `06521b018a`：图片 URL 的 MD5 前 10 位（保证唯一性）
- `.png`：文件格式

同时会自动创建兼容副本 `1445.png`（用于旧系统）。

---

## 故障排除

### 爬取速度很慢

**解决**：
1. 增加并发数：`--concurrent 4`
2. 减少延迟：`--rate 0.1`
3. 跳过图片：`--no-image`

组合：
```bash
python yibentong.py 1000 1100 --concurrent 4 --rate 0.1 --no-image
```

### 某些题目爬取失败

**排查步骤**：
1. 查看 `crawler.log` 找到错误信息
2. 检查网络连接
3. 用 `--resume` 重新尝试失败项

```bash
python yibentong.py 1000 1100 --resume
```

### JSON 或 SQL 文件损坏

**恢复方法**：
1. 删除损坏的 SQL：`rm problems_*.sql`
2. 基于 JSON 重新生成：`python yibentong.py 1000 1100 --json-only`

---

## 性能参考

在 4 Mbps 网络下的实际测试数据：

| 命令 | 100 题耗时 | 备注 |
|-----|---------|------|
| `基本爬取` | 100s | 无并发 |
| `--concurrent 2` | 50s | 2 倍加速 |
| `--concurrent 4` | 30s | 3 倍加速 |
| `--no-image` | 30s | 无图片 |
| `-c4 --no-image` | 10s | **最快** |
| `--resume`（无新项） | <1s | 仅检查 JSON |
| `--json-only` | <1s | 仅生成 SQL |

---

## 提示与最佳实践

1. **首次爬取**：使用 `--concurrent 3 --no-image` 快速获取所有题目信息
2. **补充资源**：用 `--resume` 分别下载图片或修复失败项
3. **修改规则**：用 `--json-only` 快速重新生成 SQL
4. **大规模爬取**：监控 `crawler.log`，确保网络稳定
5. **备份重要数据**：定期备份 `problems_*.json` 文件

---

**祝爬取顺利！** 🚀

有问题或建议？查看 `README.md` 获得更多信息。
