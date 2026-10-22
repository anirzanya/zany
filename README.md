# LegalReader · 法律文件解读工具

面向英语法律文件（判决书、法规、论文、合同）的学习与解读工具：上传文件后，逐句翻译成中文并解析法律术语、核心观点/义务与引注，左右双语对照浏览，引注可一键跳转官方数据库。

## 功能

- **双语对照**：左侧原文、右侧译文与解析，句级同步高亮。
- **逐句翻译 + 解析**：术语解释、观点/法律义务摘要、法源说明。
- **引注真实查询**：自动识别美国判例（Bluebook）、判例名、美国法典（U.S.C.）、欧盟法规（CELEX）、欧盟判例（ECLI）、英国判例等，点击后**实时查询数据库**（判例→CourtListener、论文→Crossref DOI、著作→Open Library），返回真实出处与原文链接，而非通用搜索。
- **PDF 原件精读**：上传 PDF 后可在「对照」与「原件」两种视图间切换，原件视图像素级还原原 PDF 排版（保留页眉、脚注、注释），并自动清洗正文中的页码/页眉噪音。
- **多格式上传**：PDF、Word(.docx/.doc)、TXT、Markdown，也支持直接粘贴文本。
- **汇总视图**：术语表、参考出处、观点摘要一键汇总。
- **导出**：Word 文档、双语 HTML、Markdown、JSON。
- **本地隐私**：API Key 仅存本机 `config.json`，不经过任何第三方服务器。

## 环境要求

- Python 3.10 及以上（仅本地后端需要，零第三方依赖）。

## 快速开始（源码运行）

```bash
# 方式一：双击
start.bat

# 方式二：命令行
python server.py
```

启动后会自动打开浏览器，访问 http://127.0.0.1:8721/ 。首次使用请点击右上角「设置」，填入 DeepSeek API Key（获取：https://platform.deepseek.com/ ）。

## 打包成独立 exe（给他人使用）

```bash
# 双击 build.bat，或命令行：
python -m pip install pyinstaller
python -m PyInstaller --onefile --name LegalReader --add-data "index.html;." server.py
```

产物在 `dist/LegalReader.exe`。对方电脑**无需安装 Python**，双击 exe 即自动启动并打开浏览器；首次在「设置」中填入自己的 API Key（存于 exe 同目录的 `config.json`）。

## 配置说明

| 配置项 | 说明 | 默认值 |
| --- | --- | --- |
| `api_key` | DeepSeek API Key | 空 |
| `base_url` | 模型接口地址 | `https://api.deepseek.com/chat/completions` |
| `model` | 模型名 | `deepseek-chat` |
| `temperature` | 生成温度（越低越稳定） | `0.3` |
| `courtlistener_token` | CourtListener Token（可选，判例精确解析） | 空 |

配置通过界面「设置」保存，或手动复制 `config.example.json` 为 `config.json` 填写。

> **CourtListener Token（可选）**：免费注册 [courtlistener.com](https://www.courtlistener.com/) 后，在账户设置里获取 Token。配置后，点击判例引注会通过 CourtListener 官方 lookup API 精确解析到对应判例原文（显示判例名、法院、日期）；不配置则判例显示为 CourtListener 搜索链接。

## 数据源与版权说明

引注跳转使用的均为**公开数据库**（元数据查询免认证）：

- 美国判例 → [CourtListener](https://www.courtlistener.com/)（Free Law Project，900 万+判例）
- 美国法典 → [Legal Information Institute](https://www.law.cornell.edu/)
- 欧盟法规/判例 → [EUR-Lex](https://eur-lex.europa.eu/) / [CURIA](https://curia.europa.eu/)
- 英国判例 → [BAILII](https://www.bailii.org/)
- 学术论文 → [Crossref](https://www.crossref.org/)（返回 DOI 与原文链接）
- 学术著作 → [Open Library](https://openlibrary.org/)（互联网档案馆开放图书目录）

**注意**：
- 原 Caselaw Access Project（CAP）REST API 已于 2024 年退役，判例查询已切换至 CourtListener。
- ISO 标准（如 ISO 37001、ISO 37301）全文为付费版权物，本工具不内置其正文，仅提供条款结构说明与公开资料解读，请勿要求输出标准原文。

## 目录结构

```
legalreader/
├── server.py            # 本地后端（零依赖，托管前端 + 代理 DeepSeek）
├── index.html           # 前端双语对照工作台
├── start.bat            # 源码运行启动脚本
├── build.bat            # 打包 exe 脚本
├── config.example.json  # 配置示例
└── README.md
```

## 架构

```
浏览器(index.html) ──HTTP──> 本地后端(server.py) ──HTTPS──> DeepSeek API（翻译解析）
        │                          │
        │ 引注高亮 + 点击查询        ├── /api/chat      代理大模型
        │                          └── /api/citations 引注解析 → 查询
        ▼                                                CourtListener / Crossref / Open Library
  双语对照工作台（对照 / PDF 原件双视图）                       （返回真实出处 + 原文链接）
```

## 后续规划（Roadmap）

- [x] CourtListener Token 可选配置（判例精确 lookup，返回判例名/法院/日期/原文链接）
- [ ] 流式输出（打字机体验）
- [ ] 阅读深度分级（快速/标准/深度）
- [ ] eyecite 精确引注解析（Python 后端，提升 Bluebook 识别精度）
- [ ] 术语库/合规专区知识库（ISO、FCPA 静态参考）
- [ ] 沉淀为 WorkBuddy skill（对话式批量解读）
