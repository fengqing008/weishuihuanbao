# 使用示例

## 示例 1：技术问答

用户：我的 Python 脚本内存泄漏，怎么排查？

正常回复（约 120 词）：
"内存泄漏是 Python 程序中常见的问题。你首先可以使用 tracemalloc 模块来跟踪内存分配情况。其次，objgraph 库可以帮助你查看对象的引用关系。另外，你还可以考虑使用 gc 模块手动触发垃圾回收，检查是否有循环引用。建议你在代码的关键位置添加内存快照对比，这样可以定位到具体是哪个函数导致的内存增长。"

压缩后（约 35 词）：
"Python 内存排查：tracemalloc 跟踪分配，objgraph 查引用环，gc.collect() 手动回收。三处打快照对比。"

## 示例 2：调试建议

用户：React 页面白屏，控制台无报错。

压缩后：
"白屏无报错 → 组件 render 抛异常被吞。加 ErrorBoundary 抓。或 React.StrictMode 二次渲染暴露副作用。"

## 示例 3：概念解释

用户：什么是 WebSocket？

压缩后：
"TCP 长连接协议。HTTP 是一问一答，WS 是持久双向。适合实时推送（聊天/行情）。"

## 示例 4：命令行

用户：怎么在 Linux 上杀掉占用 8080 端口的进程？

压缩后：
```bash
lsof -ti:8080 | xargs kill -9
```

## 示例 5：含代码块的回复

用户：怎么用 Python 读 JSON？

压缩后：
```python
import json
data = json.load(open("file.json"))
```

代码块不压缩。
