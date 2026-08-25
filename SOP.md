# 标准操作流程 (SOP)

在项目根目录右键 → 点击‘在终端中打开’ ；

依次执行以下命令，即可完成环境准备与启动：

```Shell
npm install --prefix static/new

# 将项目前端依赖保存至 static/new 里

py -m venv venv

# 创建虚拟环境

venv/scripts/activate

# 进入虚拟环境

py new.py serve

# 挂起至端口（后端 :8100 + 前端 :5174）
```

启动后：

- 后端 API 文档：http://127.0.0.1:8100/docs
- 前端页面：http://127.0.0.1:5174
- 健康检查：http://127.0.0.1:8100/health

> 旧版原型（Circular Timber Intelligence）已移至 `archived-version/`，不影响本项目的启动，可整体删除。
