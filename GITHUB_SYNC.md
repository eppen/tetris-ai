# 将 Tetris 同步到 GitHub

本地 Git 仓库已创建并完成首次提交。按以下步骤同步到 GitHub：

## 1. 在 GitHub 上创建新仓库

1. 打开 https://github.com/new
2. **Repository name** 填写：`tetris`（或你喜欢的名字）
3. 选择 **Public**，**不要**勾选 "Add a README"（本地已有代码）
4. 点击 **Create repository**

## 2. 添加远程并推送

在终端进入本目录后执行（把 `YOUR_USERNAME` 换成你的 GitHub 用户名）：

```bash
cd /Users/liuhualiang/.nanobot/workspace/tetris

# 添加 GitHub 远程仓库（替换为你的仓库 URL）
git remote add origin https://github.com/YOUR_USERNAME/tetris.git

# 推送到 GitHub
git push -u origin main
```

若使用 SSH：

```bash
git remote add origin git@github.com:YOUR_USERNAME/tetris.git
git push -u origin main
```

## 3. 之后日常推送

```bash
git add .
git commit -m "你的提交说明"
git push
```
