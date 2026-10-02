# 审计模式与「用户自行提供密钥」话术参考

本文件供 `scripts/package_skill_audit.py` 配套使用，列出常见泄露模式，
以及发现密钥/个人路径时应如何改写文案。

## 一、真实密钥模式（高危，必须删除）

| 类型 | 特征 | 示例 |
|------|------|------|
| OpenAI | `sk-` + ≥20 位 | `sk-ab12cd34...` |
| AWS | `AKIA` + 16 位大写 | `AKIAIOSFODNN7EXAMPLE` |
| GitHub | `ghp_`/`gho_`/`ghu_`/`ghs_`/`ghr_` + ≥20 位 | `ghp_xxxxxxxxxxxx` |
| Slack | `xoxb-`/`xoxp-`/`xoxa-` + 字母数字 | `xoxb-123456` |
| Google | `AIza` + 35 位 | `AIzaSyA...` |
| Google OAuth | `ya29.` 开头 | `ya29.a0Af...` |
| JWT | `eyJ...eyJ...` 三段式 | `eyJhbG...` |
| 明文字符串赋值 | `api_key="..."` / `password='...'`（非占位） | `api_key="a8f3..."` |

**判定要点**：仅当右侧是「真实长随机串」才算泄露；以下为安全写法，不应误报：
- 占位符：`"你的key"` / `"your-key"` / `"xxxx"` / `"placeholder"`
- 环境读取：`os.environ.get("S2_API_KEY")` / `args.api_key` / `api_key=None`
- 文档里的变量名本身：`S2_API_KEY`（只是名字，不是值）

## 二、个人环境路径模式（待泛化，warning）

| 类型 | 例子 | 应改为 |
|------|------|--------|
| Windows 用户路径 | `C:\Users\<用户名>\.workbuddy\...` | 泛指 `~/.workbuddy/skills/`（用户级）或 `.workbuddy/skills/`（项目级） |
| macOS/Linux home | `/home/norma/...` `/Users/norma/...` | `~/.workbuddy/...` |
| 云盘同步目录 | `E:\BaiduSyncdisk\...` / `百度网盘` | 删除具体路径，提示「勿放入会被云盘同步的目录」 |
| 密钥文件 | `s2_key.txt` 绝对路径 | 改为「用环境变量临时传入」 |
| managed Python 绝对路径 | `C:\Users\<用户名>\.workbuddy\binaries\python\...` | 改为「任意 Python 3.8+ / WorkBuddy 自带 managed Python」 |

## 三、「用户自行提供密钥」标准话术（写入 README / 文档）

发现需要密钥的步骤（如 P6 调 Semantic Scholar）时，按以下模板改写：

```
## 关于 API Key（重要）
**本 skill 不内置任何 API key，也绝不会替你保存密钥。** 仅在某步骤需要提速时用到密钥：

- 未配置也能正常运行，仅限速更严。
- 若需提速，请自行到 <官网> 免费申请 <KEY_NAME>，用环境变量传入
  （不要写进会被云盘/版本库同步的文件）：

  # Linux / macOS
  export KEY_NAME="你的key"
  python scripts/xxx.py --input refs.json

  # Windows (cmd)
  set KEY_NAME=你的key
  python scripts/xxx.py --input refs.json

- 也可调用时直接传参：python scripts/xxx.py --api-key "你的key" --input refs.json
```

## 四、README 应包含的最小安装/使用章节

1. 这是什么（一句话定位 + 适用场景）
2. 安装说明（用户级 / 项目级目录放法 + 验证方法 + 可选依赖）
3. 使用指南（触发语、阶段/命令表、通用指令、断点续传）
4. 关于 API Key（第三节话术）
5. 文件结构（与实际文件对齐，删除已不存在的目录）
6. 设计理念

> 注意：每次打包前务必先跑 `scripts/package_skill_audit.py` 审计；
> 若 README 仍停留在旧版本/旧阶段数，先更新再打包（避免分发过期文档）。

## 五、版权 / 作者 标准话术（缺失时补全到 README 末尾）

审计发现「版权说明」「作者说明」缺失时，按以下模板补全（放在 README 末尾）：

```
---

## 版权与作者

- **作者 / 维护者**：<你的名字或团队>（如 Norma · 职教本科理工科教师）
- **版本**：v<版本号> · <YYYY-MM-DD>
- **许可证**：<许可证名称>（如 MIT / Apache-2.0 / 免费用于非商业教学科研）
  - 若未声明许可证，默认：**保留署名，禁止未授权商用与再分发**。可写为：
    "© <年份> <作者>。本 skill 仅供学习与非商业用途，转载请保留出处。"
- **免责声明**：本 skill 输出仅供学术写作参考，引用文献须自行逐条核验；
  因使用本工具产生的学术不端或误引，作者不承担责任。
```

要点：
- **作者说明**必须含可识别的维护者（人名 / 团队 / 组织），不要留空。
- **版权说明**至少含 `©` 或 "版权所有" + 许可证/使用范围；未指定许可证时给出默认约束。
- 若 skill 含第三方脚本/数据，需另附其出处与许可证（避免抄袭争议）。
- 这些字段建议常驻 README，每次改版只更新版本号与日期。
