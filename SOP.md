# 标准操作流程 (SOP)

在项目根目录依次执行以下命令，即可完成环境准备与启动：

```Shell
npm install --prefix static

# 将项目前端依赖保存至static里

py -m venv venv

# 创建虚拟环境

venv/scripts/activate

# 进入虚拟环境

py main.py serve

# 挂起至端口
```

- 前端应用：http://127.0.0.1:5173
- 后端 API 文档：http://127.0.0.1:8000/docs