# 标准操作流程 (SOP)

在项目根目录右键 → 点击‘在终端中打开’ ；

依次执行以下命令，即可完成环境准备与启动：

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
