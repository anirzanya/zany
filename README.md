# 🍅 番茄钟 (Pomodoro Timer)

一个精致的番茄工作法计时器，纯前端实现，浏览器即可运行。

## 功能

- ⏱ **番茄计时** — 25分钟专注 + 5分钟短休 + 15分钟长休（每4个番茄）
- 📋 **任务管理** — 添加任务、预估番茄数、追踪完成进度
- 📝 **备忘录** — 内置笔记功能，自动保存到浏览器本地
- 🎵 **提示音** — Web Audio API 合成音效
- ⌨️ **键盘快捷键** — Space 开始/暂停、R 重置、S 跳过、1/2/3 切换标签
- 📌 **窗口置顶** — PowerShell 启动脚本支持 Edge/Chrome app 模式并置顶窗口
- 💾 **自动保存** — 计时状态、任务、备忘录全部 localStorage 持久化

## 使用方法

### 方式一：直接打开

用浏览器打开 `pomodoro.html`。

### 方式二：置顶窗口（推荐）

```powershell
.\launch-pomodoro.ps1
```
以 Edge/Chrome app 模式打开并自动置顶，专注时不被其他窗口遮挡。

## 技术栈

- 纯 HTML/CSS/JS，零依赖
- Web Audio API 音效
- SVG 环形进度条
- localStorage 数据持久化
